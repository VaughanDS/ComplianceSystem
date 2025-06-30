# data/data_manager.py
"""
Enhanced data management with better Excel handling and multi-user support
Cross-platform file locking for Windows, macOS, and Linux
"""

import pandas as pd
import os
import time
import json
import shutil
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from contextlib import contextmanager
import platform

# Cross-platform file locking imports
try:
    if platform.system() == 'Windows':
        import msvcrt  # Windows file locking
    else:
        import fcntl  # Unix/Linux file locking
except ImportError:
    # Fallback if imports fail
    msvcrt = None
    fcntl = None

from config import get_config, get_db_config
from core.exceptions import FileAccessError, FileLockError, DataIntegrityError
from core.models import Task, TeamMember, LegislationReference
from utils.logger import get_logger

logger = get_logger(__name__)


class FileLockManager:
    """Manages cross-platform file locking for multi-user access"""

    def __init__(self, lock_dir: Optional[Path] = None):
        self.lock_dir = lock_dir or Path.home() / ".compliance_locks"
        self.lock_dir.mkdir(exist_ok=True)
        self.is_windows = platform.system() == 'Windows'
        self.is_unix = platform.system() in ['Linux', 'Darwin']

        # Check if locking modules are available
        self.locking_available = (
                (self.is_windows and msvcrt is not None) or
                (self.is_unix and fcntl is not None)
        )

        if not self.locking_available:
            logger.warning("File locking not available - using fallback method")

    def _get_lock_file_path(self, file_path: Path) -> Path:
        """Get lock file path for a given file"""
        # Create a safe filename for the lock
        safe_name = str(file_path).replace('/', '_').replace('\\', '_').replace(':', '_')
        return self.lock_dir / f"{safe_name}.lock"

    @contextmanager
    def file_lock(self, file_path: Path, timeout: int = 30):
        """Context manager for cross-platform file locking"""
        lock_file = self._get_lock_file_path(file_path)
        lock_acquired = False
        file_handle = None

        try:
            # Try to acquire lock
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    # Create lock file
                    file_handle = open(lock_file, 'w')

                    if self.locking_available:
                        if self.is_windows and msvcrt:
                            # Windows file locking
                            msvcrt.locking(file_handle.fileno(), msvcrt.LK_NBLCK, 1)
                        elif self.is_unix and fcntl:
                            # Unix file locking
                            fcntl.flock(file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

                    # Write lock info
                    lock_info = {
                        'pid': os.getpid(),
                        'user': os.environ.get('USERNAME', os.environ.get('USER', 'unknown')),
                        'timestamp': datetime.now().isoformat(),
                        'file': str(file_path)
                    }
                    json.dump(lock_info, file_handle)
                    file_handle.flush()

                    lock_acquired = True
                    break

                except (IOError, OSError, BlockingIOError):
                    # Lock is held by another process
                    if file_handle:
                        file_handle.close()
                    time.sleep(0.5)

            if not lock_acquired:
                raise FileLockError(
                    f"Could not acquire lock for {file_path}",
                    file_path=str(file_path),
                    timeout=True
                )

            yield

        finally:
            # Release lock
            if file_handle:
                try:
                    if self.locking_available:
                        if self.is_windows and msvcrt:
                            msvcrt.locking(file_handle.fileno(), msvcrt.LK_UNLCK, 1)
                        elif self.is_unix and fcntl:
                            fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
                    file_handle.close()
                except:
                    pass

            # Remove lock file
            if lock_acquired and lock_file.exists():
                try:
                    lock_file.unlink()
                except:
                    pass

    def is_file_locked(self, file_path: Path) -> bool:
        """Check if file is currently locked"""
        lock_file = self._get_lock_file_path(file_path)

        if not lock_file.exists():
            return False

        # Try to read lock info
        try:
            with open(lock_file, 'r') as f:
                lock_info = json.load(f)

            # Check if lock is stale (older than 1 hour)
            lock_time = datetime.fromisoformat(lock_info['timestamp'])
            if (datetime.now() - lock_time).total_seconds() > 3600:
                # Stale lock, try to remove it
                try:
                    lock_file.unlink()
                    return False
                except:
                    pass

            return True

        except:
            return True

    def _is_lock_active(self, lock_file: Path) -> bool:
        """Check if a lock file represents an active lock"""
        try:
            with open(lock_file, 'r') as f:
                lock_info = json.load(f)

            pid = lock_info.get('pid')
            if pid:
                # Check if process is still running
                if self.is_windows:
                    # Windows process check
                    import subprocess
                    result = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'],
                                            capture_output=True, text=True)
                    return str(pid) in result.stdout
                else:
                    # Unix process check
                    try:
                        os.kill(pid, 0)
                        return True
                    except ProcessLookupError:
                        return False

        except:
            pass

        return False

    def clear_stale_locks(self, max_age_hours: int = 24):
        """Clear stale lock files"""
        current_time = time.time()

        for lock_file in self.lock_dir.glob("*.lock"):
            try:
                file_age_hours = (current_time - lock_file.stat().st_mtime) / 3600
                if file_age_hours > max_age_hours:
                    # Double-check it's not an active lock
                    if not self._is_lock_active(lock_file):
                        lock_file.unlink()
                        logger.info(f"Cleared stale lock: {lock_file.name}")
            except Exception as e:
                logger.error(f"Error clearing lock {lock_file}: {e}")


class ExcelFileManager:
    """Manages Excel file operations with proper locking and backup"""

    def __init__(self, base_path: Path, lock_manager: FileLockManager):
        self.base_path = base_path
        self.lock_manager = lock_manager
        self.config = get_config()
        self.db_config = get_db_config()

    def read_excel(self, filename: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """Read Excel file with locking and proper error handling"""
        file_path = self.base_path / self.config.data_folder / filename

        if not file_path.exists():
            logger.warning(f"Excel file not found: {file_path}")
            return pd.DataFrame()

        try:
            with self.lock_manager.file_lock(file_path, timeout=10):
                # Try to read the Excel file
                try:
                    df = pd.read_excel(
                        file_path,
                        sheet_name=sheet_name,
                        engine='openpyxl'
                    )
                except Exception as e:
                    logger.error(f"Error reading Excel file {filename}: {e}")
                    return pd.DataFrame()

                # Ensure we have a DataFrame
                if not isinstance(df, pd.DataFrame):
                    logger.warning(f"Excel file {filename} did not return a DataFrame")
                    return pd.DataFrame()

                # Parse date columns
                date_columns = ['Date Logged', 'Target Close Date', 'Last Updated Date',
                                'Approval Date', 'Created Date', 'Start Date', 'Effective Date']
                for col in date_columns:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], errors='coerce')

                return df

        except FileLockError:
            # If can't get lock for reading, try without lock (read-only)
            logger.warning(f"Reading {filename} without lock (read-only)")
            try:
                df = pd.read_excel(
                    file_path,
                    sheet_name=sheet_name,
                    engine='openpyxl'
                )

                # Ensure we have a DataFrame
                if not isinstance(df, pd.DataFrame):
                    logger.warning(f"Excel file {filename} did not return a DataFrame")
                    return pd.DataFrame()

                return df
            except Exception as e:
                logger.error(f"Error reading Excel file {filename}: {e}")
                return pd.DataFrame()

    def write_excel(self, df: pd.DataFrame, filename: str,
                    sheet_name: str = 'Sheet1', backup: bool = True) -> bool:
        """Write DataFrame to Excel with locking and backup"""
        file_path = self.base_path / self.config.data_folder / filename

        try:
            # Create backup if requested and file exists
            if backup and file_path.exists():
                self._create_backup(file_path)

            with self.lock_manager.file_lock(file_path, timeout=30):
                # Ensure directory exists
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # Write to temporary file first
                temp_path = file_path.with_suffix(f"{file_path.suffix}.tmp")

                df.to_excel(
                    temp_path,
                    sheet_name=sheet_name,
                    index=False,
                    engine='openpyxl'
                )

                # Move temp file to final location
                if temp_path.exists():
                    if file_path.exists():
                        file_path.unlink()
                    temp_path.rename(file_path)

                logger.info(f"Successfully wrote {len(df)} rows to {filename}")
                return True

        except FileLockError as e:
            logger.error(f"File locked, cannot write to {filename}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error writing to Excel file {filename}: {e}")
            return False

    def _create_backup(self, file_path: Path):
        """Create backup of file"""
        try:
            backup_dir = file_path.parent / "backups"
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = backup_dir / backup_name

            shutil.copy2(file_path, backup_path)
            logger.debug(f"Created backup: {backup_path}")

            # Clean old backups (keep last 10)
            self._clean_old_backups(backup_dir, file_path.stem)

        except Exception as e:
            logger.warning(f"Failed to create backup for {file_path}: {e}")

    def _clean_old_backups(self, backup_dir: Path, file_stem: str, keep_count: int = 10):
        """Clean old backup files"""
        try:
            pattern = f"{file_stem}_*.xlsx"
            backups = list(backup_dir.glob(pattern))

            if len(backups) > keep_count:
                # Sort by modification time and remove oldest
                backups.sort(key=lambda x: x.stat().st_mtime)
                for backup in backups[:-keep_count]:
                    backup.unlink()
                    logger.debug(f"Removed old backup: {backup}")

        except Exception as e:
            logger.warning(f"Error cleaning old backups: {e}")


class DataManager:
    """Main data manager with Excel file handling and caching"""

    def __init__(self, base_path: Optional[Path] = None):
        self.config = get_config()
        self.base_path = base_path or self.config.base_path
        self.lock_manager = FileLockManager()
        self.excel_manager = ExcelFileManager(self.base_path, self.lock_manager)

        # Data caches
        self._task_cache = None
        self._team_cache = None
        self._legislation_cache = None
        self._cache_timestamps = {}

        # Cache TTL (5 minutes)
        self.cache_ttl = 300

        # File modification tracking
        self._file_mod_times = {}

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache is still valid"""
        if cache_key not in self._cache_timestamps:
            return False

        age = time.time() - self._cache_timestamps[cache_key]
        return age < self.cache_ttl

    def _update_cache_timestamp(self, cache_key: str):
        """Update cache timestamp"""
        self._cache_timestamps[cache_key] = time.time()

    def has_file_changed(self, filename: str) -> bool:
        """Check if file has been modified since last check"""
        file_path = self.base_path / self.config.data_folder / filename

        if not file_path.exists():
            return False

        try:
            current_mod_time = file_path.stat().st_mtime
            last_mod_time = self._file_mod_times.get(filename, 0)

            if current_mod_time > last_mod_time:
                self._file_mod_times[filename] = current_mod_time
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking file modification for {filename}: {e}")
            return False

    def load_tasks(self, force_refresh: bool = False) -> List[Task]:
        """Load tasks from Excel file"""
        if not force_refresh and self._task_cache and self._is_cache_valid('tasks'):
            return self._task_cache

        try:
            df = self.excel_manager.read_excel(self.config.excel_files['tasks'])

            # Check if df is actually a DataFrame and not empty
            if not isinstance(df, pd.DataFrame) or df.empty:
                logger.info("No tasks found or invalid data structure")
                self._task_cache = []
                self._update_cache_timestamp('tasks')
                return []

            tasks = []
            for _, row in df.iterrows():
                try:
                    # Convert row to dict and map columns
                    row_dict = self._map_task_columns(row.to_dict())

                    # Create task if we have required fields
                    if row_dict.get('key') and row_dict.get('title'):
                        task = Task(**row_dict)
                        tasks.append(task)

                except Exception as e:
                    logger.warning(f"Error parsing task row: {e}")
                    continue

            self._task_cache = tasks
            self._update_cache_timestamp('tasks')
            logger.info(f"Loaded {len(self._task_cache)} tasks")
            return self._task_cache

        except Exception as e:
            logger.error(f"Error loading tasks: {e}")
            # Return cached data if available, otherwise empty list
            return self._task_cache or []

    def save_tasks(self, tasks: List[Task]) -> bool:
        """Save tasks to Excel file"""
        try:
            # Convert tasks to DataFrame
            task_data = []
            for task in tasks:
                task_dict = self._unmap_task_columns(task.to_dict())
                task_data.append(task_dict)

            df = pd.DataFrame(task_data)

            # Ensure proper column order
            columns = [
                'Task Key', 'Title', 'Compliance Area', 'Subcategory',
                'Task Setter', 'Task Setter Email', 'Allocated To',
                'Allocated Emails', 'Manager', 'Manager Email',
                'Priority', 'Description', 'Status', 'Date Logged',
                'Target Close Date', 'Completed Date', 'Actions',
                'Attachments', 'Approvals', 'Tags', 'Custom Fields'
            ]

            for col in columns:
                if col not in df.columns:
                    df[col] = ''

            # Reorder columns
            df = df.reindex(columns=columns, fill_value='')

            success = self.excel_manager.write_excel(df, self.config.excel_files['tasks'])

            if success:
                self._task_cache = tasks
                self._update_cache_timestamp('tasks')
                logger.info(f"Saved {len(tasks)} tasks")

            return success

        except Exception as e:
            logger.error(f"Error saving tasks: {e}")
            return False

    def load_team_members(self, force_refresh: bool = False) -> List[TeamMember]:
        """Load team members from Excel file"""
        if not force_refresh and self._team_cache and self._is_cache_valid('team'):
            return self._team_cache

        try:
            df = self.excel_manager.read_excel(self.config.excel_files['team'])

            # Check if df is actually a DataFrame and not empty
            if not isinstance(df, pd.DataFrame) or df.empty:
                logger.info("No team members found or invalid data structure")
                self._team_cache = []
                self._update_cache_timestamp('team')
                return []

            members = []
            for _, row in df.iterrows():
                try:
                    row_dict = row.to_dict()

                    # Map columns if needed
                    member_data = {
                        'name': row_dict.get('Name', ''),
                        'email': row_dict.get('Email', ''),
                        'department': row_dict.get('Department', ''),
                        'role': row_dict.get('Role', 'Team Member'),
                        'location': row_dict.get('Location', ''),
                        'employee_id': row_dict.get('Employee ID', ''),
                        'phone': row_dict.get('Phone', ''),
                        'manager': row_dict.get('Manager', ''),
                        'start_date': row_dict.get('Start Date', ''),
                        'active': row_dict.get('Active', True)
                    }

                    # Create member if we have required fields
                    if member_data['name'] and member_data['email']:
                        member = TeamMember(**member_data)
                        members.append(member)

                except Exception as e:
                    logger.warning(f"Error parsing team member row: {e}")
                    continue

            self._team_cache = members
            self._update_cache_timestamp('team')
            logger.info(f"Loaded {len(self._team_cache)} team members")
            return self._team_cache

        except Exception as e:
            logger.error(f"Error loading team members: {e}")
            return self._team_cache or []

    def save_team_members(self, members: List[TeamMember]) -> bool:
        """Save team members to Excel file"""
        try:
            # Convert members to DataFrame
            member_data = []
            for member in members:
                member_dict = member.to_dict()
                # Map to Excel columns
                excel_dict = {
                    'Name': member_dict.get('name', ''),
                    'Email': member_dict.get('email', ''),
                    'Department': member_dict.get('department', ''),
                    'Role': member_dict.get('role', ''),
                    'Location': member_dict.get('location', ''),
                    'Employee ID': member_dict.get('employee_id', ''),
                    'Phone': member_dict.get('phone', ''),
                    'Manager': member_dict.get('manager', ''),
                    'Start Date': member_dict.get('start_date', ''),
                    'Active': member_dict.get('active', True),
                    'Created Date': member_dict.get('created_date', ''),
                    'Last Login': member_dict.get('last_login', '')
                }
                member_data.append(excel_dict)

            df = pd.DataFrame(member_data)

            # Ensure proper column order
            columns = [
                'Name', 'Email', 'Department', 'Role', 'Location',
                'Employee ID', 'Phone', 'Manager', 'Start Date',
                'Permissions', 'Active', 'Created Date', 'Last Login',
                'Preferences'
            ]

            for col in columns:
                if col not in df.columns:
                    df[col] = ''

            # Reorder columns
            df = df.reindex(columns=columns, fill_value='')

            success = self.excel_manager.write_excel(df, self.config.excel_files['team'])

            if success:
                self._team_cache = members
                self._update_cache_timestamp('team')
                logger.info(f"Saved {len(members)} team members")

            return success

        except Exception as e:
            logger.error(f"Error saving team members: {e}")
            return False

    def load_legislation(self, force_refresh: bool = False) -> List[LegislationReference]:
        """Load legislation references"""
        if not force_refresh and self._legislation_cache and self._is_cache_valid('legislation'):
            return self._legislation_cache

        try:
            df = self.excel_manager.read_excel(
                self.config.excel_files.get('legislation', 'Legislation_References.xlsx'))

            if not isinstance(df, pd.DataFrame) or df.empty:
                logger.info("No legislation references found")
                self._legislation_cache = []
                self._update_cache_timestamp('legislation')
                return []

            legislation = []
            for _, row in df.iterrows():
                try:
                    row_dict = row.to_dict()

                    # Map columns
                    leg_data = {
                        'code': row_dict.get('Code', ''),
                        'title': row_dict.get('Title', ''),
                        'category': row_dict.get('Category', ''),
                        'jurisdiction': row_dict.get('Jurisdiction', ''),
                        'effective_date': row_dict.get('Effective Date', ''),
                        'description': row_dict.get('Description', ''),
                        'last_updated': row_dict.get('Last Updated', ''),
                        'owner': row_dict.get('Owner', '')
                    }

                    if leg_data['code'] and leg_data['title']:
                        leg = LegislationReference(**leg_data)
                        legislation.append(leg)

                except Exception as e:
                    logger.warning(f"Error parsing legislation row: {e}")
                    continue

            self._legislation_cache = legislation
            self._update_cache_timestamp('legislation')
            logger.info(f"Loaded {len(self._legislation_cache)} legislation references")
            return self._legislation_cache

        except Exception as e:
            logger.error(f"Error loading legislation: {e}")
            return self._legislation_cache or []

    def load_legislation_references(self) -> List[LegislationReference]:
        """Load legislation references from Excel"""
        try:
            # Check cache first
            if self._check_cache('legislation'):
                return self._legislation_cache

            # Load from Excel
            df = self.excel_manager.read_excel(
                self.config.excel_files.get('legislation', 'Legislation_References.xlsx')
            )

            if df is None or df.empty:
                logger.info("No legislation references found or invalid data structure")
                return []

            # Convert DataFrame to LegislationReference objects
            legislation_list = []

            for index, row in df.iterrows():
                try:
                    # Parse JSON fields
                    requirements = self._parse_json_field(row.get('Requirements', '[]'))
                    penalties = self._parse_json_field(row.get('Penalties', '[]'))
                    related_tasks = self._parse_json_field(row.get('Related Tasks', '[]'))
                    related_docs = self._parse_json_field(row.get('Related Documents', '[]'))
                    compliance_checks = self._parse_json_field(row.get('Compliance Checks', '[]'))

                    # Create LegislationReference object
                    legislation = LegislationReference(
                        code=str(row.get('Code', '')),
                        full_name=str(row.get('Title', '')),
                        category=str(row.get('Category', '')),
                        jurisdiction=str(row.get('Jurisdiction', '')),
                        effective_date=str(row.get('Effective Date', '')),
                        last_updated=str(row.get('Last Updated', '')),
                        summary=str(row.get('Description', '')),
                        key_requirements=requirements if isinstance(requirements, list) else [],
                        penalties=penalties if isinstance(penalties, list) else [],
                        review_frequency=str(row.get('Review Frequency', 'Annual')),
                        owner=str(row.get('Owner', '')),
                        applicable_areas=[],  # Will be populated based on category
                        related_tasks=related_tasks if isinstance(related_tasks, list) else [],
                        related_documents=related_docs if isinstance(related_docs, list) else [],
                        compliance_checklist=compliance_checks if isinstance(compliance_checks, list) else [],
                        external_links=[],  # Can be populated from a separate field if needed
                        internal_guidance=''  # Can be populated from a separate field if needed
                    )

                    # Determine applicable areas based on category
                    legislation.applicable_areas = self._determine_applicable_areas(
                        legislation.category
                    )

                    legislation_list.append(legislation)

                except Exception as e:
                    logger.error(f"Error parsing legislation reference at row {index}: {e}")
                    continue

            # Update cache
            self._legislation_cache = legislation_list
            self._update_cache_timestamp('legislation')

            logger.info(f"Loaded {len(legislation_list)} legislation references")
            return legislation_list

        except FileNotFoundError:
            logger.warning(f"Excel file not found: {self.config.excel_files.get('legislation')}")
            return []
        except Exception as e:
            logger.error(f"Error loading legislation references: {e}")
            return []

    def _parse_json_field(self, field_value: Any) -> Any:
        """Parse JSON field from Excel"""
        if pd.isna(field_value) or field_value == '':
            return []

        if isinstance(field_value, str):
            try:
                return json.loads(field_value)
            except json.JSONDecodeError:
                # Try to parse as comma-separated list
                if ',' in field_value:
                    return [item.strip() for item in field_value.split(',')]
                return [field_value]

        return field_value

    def _determine_applicable_areas(self, category: str) -> List[str]:
        """Determine applicable compliance areas based on category"""
        category_areas = {
            'Data Protection': ['IT Security', 'Legal', 'Customer Relations'],
            'Anti-Bribery': ['Procurement', 'Sales', 'Finance'],
            'Environmental': ['Operations', 'Logistics', 'Procurement'],
            'Product Safety': ['Quality', 'Operations', 'Customer Relations'],
            'Financial': ['Finance', 'Legal', 'Compliance'],
            'Trade': ['Logistics', 'Procurement', 'Legal'],
            'Employment': ['HR', 'Legal', 'Operations'],
            'Quality': ['Quality', 'Operations', 'Customer Relations']
        }

        return category_areas.get(category, ['Compliance'])

    def save_legislation(self, legislation: List[LegislationReference]) -> bool:
        """Save legislation references"""
        try:
            # Convert legislation to DataFrame
            leg_data = []
            for leg in legislation:
                leg_dict = leg.to_dict()
                # Map to Excel columns
                excel_dict = {
                    'Code': leg_dict.get('code', ''),
                    'Title': leg_dict.get('title', ''),
                    'Category': leg_dict.get('category', ''),
                    'Jurisdiction': leg_dict.get('jurisdiction', ''),
                    'Effective Date': leg_dict.get('effective_date', ''),
                    'Description': leg_dict.get('description', ''),
                    'Requirements': json.dumps(leg_dict.get('requirements', [])),
                    'Penalties': leg_dict.get('penalties', ''),
                    'Last Updated': leg_dict.get('last_updated', ''),
                    'Review Frequency': leg_dict.get('review_frequency', ''),
                    'Owner': leg_dict.get('owner', ''),
                    'Related Tasks': json.dumps(leg_dict.get('related_tasks', [])),
                    'Related Documents': json.dumps(leg_dict.get('related_documents', [])),
                    'Compliance Checks': json.dumps(leg_dict.get('compliance_checks', []))
                }
                leg_data.append(excel_dict)

            df = pd.DataFrame(leg_data)

            # Ensure proper column order
            columns = [
                'Code', 'Title', 'Category', 'Jurisdiction',
                'Effective Date', 'Description', 'Requirements',
                'Penalties', 'Last Updated', 'Review Frequency',
                'Owner', 'Related Tasks', 'Related Documents',
                'Compliance Checks'
            ]

            for col in columns:
                if col not in df.columns:
                    df[col] = ''

            # Reorder columns
            df = df.reindex(columns=columns, fill_value='')

            success = self.excel_manager.write_excel(
                df,
                self.config.excel_files.get('legislation', 'Legislation_References.xlsx')
            )

            if success:
                self._legislation_cache = legislation
                self._update_cache_timestamp('legislation')
                logger.info(f"Saved {len(legislation)} legislation references")

            return success

        except Exception as e:
            logger.error(f"Error saving legislation: {e}")
            return False

    def get_task(self, task_key: str) -> Optional[Task]:
        """Get single task by key"""
        tasks = self.load_tasks()
        for task in tasks:
            if task.key == task_key:
                return task
        return None

    def save_task(self, task: Task) -> bool:
        """Save single task"""
        tasks = self.load_tasks()

        # Update existing or add new
        updated = False
        for i, t in enumerate(tasks):
            if t.key == task.key:
                tasks[i] = task
                updated = True
                break

        if not updated:
            tasks.append(task)

        return self.save_tasks(tasks)

    def delete_task(self, task_key: str) -> bool:
        """Delete task by key"""
        tasks = self.load_tasks()
        original_count = len(tasks)

        tasks = [t for t in tasks if t.key != task_key]

        if len(tasks) < original_count:
            return self.save_tasks(tasks)
        return False

    def get_team_member(self, name: str) -> Optional[TeamMember]:
        """Get team member by name"""
        members = self.load_team_members()
        for member in members:
            if member.name.lower() == name.lower():
                return member
        return None

    def save_team_member(self, member: TeamMember) -> bool:
        """Save single team member"""
        members = self.load_team_members()

        # Update existing or add new
        updated = False
        for i, m in enumerate(members):
            if m.email.lower() == member.email.lower():
                members[i] = member
                updated = True
                break

        if not updated:
            members.append(member)

        return self.save_team_members(members)

    def create_legislation_reference(self, legislation: LegislationReference) -> bool:
        """Create new legislation reference"""
        current_legislation = self.load_legislation()
        current_legislation.append(legislation)
        return self.save_legislation(current_legislation)

    def update_legislation_reference(self, legislation: LegislationReference) -> bool:
        """Update existing legislation reference"""
        current_legislation = self.load_legislation()

        for i, leg in enumerate(current_legislation):
            if leg.code == legislation.code:
                current_legislation[i] = legislation
                break
        else:
            current_legislation.append(legislation)

        return self.save_legislation(current_legislation)

    def load_legislation_references(self, force_refresh: bool = False) -> List[LegislationReference]:
        """Load legislation references - alias for load_legislation"""
        return self.load_legislation(force_refresh)

    def clear_cache(self):
        """Clear all data caches"""
        self._task_cache = None
        self._team_cache = None
        self._legislation_cache = None
        self._cache_timestamps.clear()
        logger.info("Data cache cleared")

    def get_file_status(self, filename: str) -> Dict[str, Any]:
        """Get file status information"""
        file_path = self.base_path / self.config.data_folder / filename

        status = {
            'exists': file_path.exists(),
            'size': 0,
            'modified': None,
            'locked': False,
            'readable': False,
            'writable': False
        }

        if file_path.exists():
            try:
                stat = file_path.stat()
                status.update({
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'readable': os.access(file_path, os.R_OK),
                    'writable': os.access(file_path, os.W_OK),
                    'locked': self.lock_manager.is_file_locked(file_path)
                })
            except Exception as e:
                logger.warning(f"Error getting file status for {filename}: {e}")

        return status

    def cleanup(self):
        """Cleanup resources and stale locks"""
        try:
            self.lock_manager.clear_stale_locks()
            self.clear_cache()
            logger.info("Data manager cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def _map_task_columns(self, row_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Map Excel columns to Task model fields"""
        # Handle various column name formats
        mapped = {
            'key': row_dict.get('Task Key', row_dict.get('Key', '')),
            'title': row_dict.get('Title', ''),
            'compliance_area': row_dict.get('Compliance Area', ''),
            'subcategory': row_dict.get('Subcategory', ''),
            'task_setter': row_dict.get('Task Setter', ''),
            'task_setter_email': row_dict.get('Task Setter Email', ''),
            'allocated_to': self._parse_list(row_dict.get('Allocated To', '')),
            'allocated_emails': self._parse_list(row_dict.get('Allocated Emails', '')),
            'manager': row_dict.get('Manager', ''),
            'manager_email': row_dict.get('Manager Email', ''),
            'priority': row_dict.get('Priority', 'Medium'),
            'description': row_dict.get('Description', row_dict.get('Task Description', '')),
            'status': row_dict.get('Status', 'Open'),
            'date_logged': str(row_dict.get('Date Logged', '')),
            'target_date': str(row_dict.get('Target Close Date', '')),
            'completed_date': str(row_dict.get('Completed Date', '')),
            'created_by': row_dict.get('Created By', ''),
            'created_date': str(row_dict.get('Created Date', '')),
            'modified_by': row_dict.get('Last Updated By', ''),
            'modified_date': str(row_dict.get('Last Updated Date', '')),
            'tags': self._parse_list(row_dict.get('Tags', '')),
            'custom_fields': self._parse_json(row_dict.get('Custom Fields', '{}'))
        }

        # Clean up empty dates
        for date_field in ['date_logged', 'target_date', 'completed_date', 'created_date', 'modified_date']:
            if mapped[date_field] == 'NaT' or mapped[date_field] == 'nan':
                mapped[date_field] = ''

        return mapped

    def _unmap_task_columns(self, task_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Unmap Task model fields to Excel columns"""
        return {
            'Task Key': task_dict.get('key', ''),
            'Title': task_dict.get('title', ''),
            'Compliance Area': task_dict.get('compliance_area', ''),
            'Subcategory': task_dict.get('subcategory', ''),
            'Task Setter': task_dict.get('task_setter', ''),
            'Task Setter Email': task_dict.get('task_setter_email', ''),
            'Allocated To': self._join_list(task_dict.get('allocated_to', [])),
            'Allocated Emails': self._join_list(task_dict.get('allocated_emails', [])),
            'Manager': task_dict.get('manager', ''),
            'Manager Email': task_dict.get('manager_email', ''),
            'Priority': task_dict.get('priority', ''),
            'Description': task_dict.get('description', ''),
            'Status': task_dict.get('status', ''),
            'Date Logged': task_dict.get('date_logged', ''),
            'Target Close Date': task_dict.get('target_date', ''),
            'Completed Date': task_dict.get('completed_date', ''),
            'Actions': json.dumps(task_dict.get('actions', [])),
            'Attachments': json.dumps(task_dict.get('attachments', [])),
            'Approvals': json.dumps(task_dict.get('approvals', [])),
            'Tags': self._join_list(task_dict.get('tags', [])),
            'Custom Fields': json.dumps(task_dict.get('custom_fields', {}))
        }

    def _parse_list(self, value: str) -> List[str]:
        """Parse comma-separated string to list"""
        if not value or pd.isna(value):
            return []
        if isinstance(value, list):
            return value
        return [item.strip() for item in str(value).split(',') if item.strip()]

    def _join_list(self, value: List[str]) -> str:
        """Join list to comma-separated string"""
        if not value:
            return ''
        return ', '.join(value)

    def _parse_json(self, value: str) -> Dict[str, Any]:
        """Parse JSON string to dict"""
        if not value or pd.isna(value):
            return {}
        if isinstance(value, dict):
            return value
        try:
            return json.loads(str(value))
        except:
            return {}


# Global data manager instance
_data_manager = None


def get_data_manager() -> DataManager:
    """Get global data manager instance"""
    global _data_manager
    if _data_manager is None:
        _data_manager = DataManager()
    return _data_manager