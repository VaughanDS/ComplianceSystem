# data/archiving.py
"""
Data archiving functionality for Compliance Management System
Manages historical data storage and retrieval
"""

import pandas as pd
import json
import gzip
import shutil
import zipfile
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field

from config import get_config, get_db_config
from core.exceptions import ArchiveError, FileAccessError
from core.models import Task, TeamMember, LegislationReference
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ArchiveMetadata:
    """Metadata for archived data"""
    archive_id: str
    period_start: str
    period_end: str
    record_count: int
    file_size: int
    created_date: str
    created_by: str
    compression_ratio: float
    index_file: str
    data_file: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.__dict__

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArchiveMetadata':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class ArchiveIndex:
    """Index entry for archived records"""
    record_key: str
    record_type: str  # 'task', 'team', 'legislation'
    summary: str
    tags: List[str] = field(default_factory=list)
    date_created: str = ""
    date_modified: str = ""
    archive_id: str = ""
    position: int = 0  # Position in archive file for quick access

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'record_key': self.record_key,
            'record_type': self.record_type,
            'summary': self.summary,
            'tags': json.dumps(self.tags),
            'date_created': self.date_created,
            'date_modified': self.date_modified,
            'archive_id': self.archive_id,
            'position': self.position
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArchiveIndex':
        """Create from dictionary"""
        tags = data.get('tags', '[]')
        if isinstance(tags, str):
            tags = json.loads(tags)

        return cls(
            record_key=data['record_key'],
            record_type=data['record_type'],
            summary=data['summary'],
            tags=tags,
            date_created=data.get('date_created', ''),
            date_modified=data.get('date_modified', ''),
            archive_id=data.get('archive_id', ''),
            position=data.get('position', 0)
        )


class ArchiveManager:
    """Manages data archiving operations"""

    def __init__(self, data_manager):
        self.config = get_config()
        self.db_config = get_db_config()
        self.data_manager = data_manager

        # Set up archive directories
        self.archive_base = self.config.base_path / self.config.archive_folder
        self.index_base = self.archive_base / 'indices'

        # Create directories
        self.archive_base.mkdir(parents=True, exist_ok=True)
        self.index_base.mkdir(parents=True, exist_ok=True)

    def archive_old_tasks(self, cutoff_date: Optional[datetime] = None) -> Tuple[int, str]:
        """Archive tasks older than cutoff date"""
        if not cutoff_date:
            cutoff_date = datetime.now() - timedelta(days=self.config.archive_after_days)

        logger.info(f"Archiving tasks older than {cutoff_date.date()}")

        try:
            # Load all tasks
            tasks = self.data_manager.load_tasks()

            # Separate tasks to archive and keep
            tasks_to_archive = []
            tasks_to_keep = []

            for task in tasks:
                # Parse task date
                try:
                    task_date_str = task.date_logged
                    if task_date_str:
                        task_date = datetime.strptime(task_date_str, "%Y-%m-%d")
                    else:
                        # If no date, keep the task
                        tasks_to_keep.append(task)
                        continue

                    # Check if task should be archived
                    if task_date < cutoff_date and task.status in ["Resolved", "Closed"]:
                        tasks_to_archive.append(task)
                    else:
                        tasks_to_keep.append(task)
                except Exception as e:
                    logger.warning(f"Error parsing date for task {task.key}: {e}")
                    tasks_to_keep.append(task)

            if not tasks_to_archive:
                logger.info("No tasks to archive")
                return 0, ""

            # Create archive
            archive_id = self._create_archive(tasks_to_archive, 'tasks')

            # Update main task file with remaining tasks
            self.data_manager.save_tasks(tasks_to_keep)

            logger.info(f"Archived {len(tasks_to_archive)} tasks to {archive_id}")
            return len(tasks_to_archive), archive_id

        except Exception as e:
            logger.error(f"Error archiving tasks: {e}")
            raise ArchiveError(
                f"Failed to archive tasks: {str(e)}",
                period=str(cutoff_date.date()) if cutoff_date else "unknown"
            )

    def _create_archive(self, records: List[Any], record_type: str) -> str:
        """Create archive file with compression"""
        # Generate archive ID
        archive_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        year_month = datetime.now().strftime("%Y_%m")

        # Create year/month directory
        archive_dir = self.archive_base / year_month
        archive_dir.mkdir(parents=True, exist_ok=True)

        # Prepare data
        if record_type == 'tasks':
            data = [task.to_dict() for task in records]
            df = pd.DataFrame(data)
        else:
            raise ValueError(f"Unsupported record type: {record_type}")

        # Create archive files
        data_file = archive_dir / f"{record_type}_{archive_id}.json.gz"
        index_file = self.index_base / f"{record_type}_{archive_id}_index.json"

        # Write compressed data
        original_size = len(df.to_json().encode())
        with gzip.open(data_file, 'wt', encoding='utf-8') as f:
            df.to_json(f, orient='records', date_format='iso')

        compressed_size = data_file.stat().st_size
        compression_ratio = compressed_size / original_size if original_size > 0 else 1.0

        # Create indices
        indices = self._create_indices(records, record_type, archive_id)

        # Save index file
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump([idx.to_dict() for idx in indices], f, indent=2)

        # Create metadata
        metadata = ArchiveMetadata(
            archive_id=archive_id,
            period_start=min(r.date_logged for r in records if hasattr(r, 'date_logged') and r.date_logged),
            period_end=max(r.date_logged for r in records if hasattr(r, 'date_logged') and r.date_logged),
            record_count=len(records),
            file_size=compressed_size,
            created_date=datetime.now().isoformat(),
            created_by=self.config.author,
            compression_ratio=compression_ratio,
            index_file=str(index_file),
            data_file=str(data_file)
        )

        # Save metadata
        metadata_file = archive_dir / f"{record_type}_{archive_id}_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata.to_dict(), f, indent=2)

        return archive_id

    def _create_indices(self, records: List[Any], record_type: str,
                        archive_id: str) -> List[ArchiveIndex]:
        """Create searchable indices for archived records"""
        indices = []

        for i, record in enumerate(records):
            if record_type == 'tasks' and isinstance(record, Task):
                # Create index for task
                tags = [
                    record.compliance_area,
                    record.subcategory,
                    record.priority,
                    record.status,
                    record.task_setter
                ]

                index = ArchiveIndex(
                    record_key=record.key,
                    record_type='task',
                    summary=f"{record.title} ({record.status})",
                    tags=[tag for tag in tags if tag],
                    date_created=record.created_date,
                    date_modified=record.modified_date,
                    archive_id=archive_id,
                    position=i
                )
                indices.append(index)

        return indices

    def search_archives(self, query: str, record_type: Optional[str] = None,
                        date_from: Optional[datetime] = None,
                        date_to: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Search archived records"""
        results = []
        query_lower = query.lower()

        # Load all index files
        for index_file in self.index_base.glob("*_index.json"):
            if record_type and not index_file.name.startswith(record_type):
                continue

            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    indices = json.load(f)

                for idx_data in indices:
                    index = ArchiveIndex.from_dict(idx_data)

                    # Check date range
                    if date_from or date_to:
                        try:
                            idx_date = datetime.fromisoformat(index.date_created)
                            if date_from and idx_date < date_from:
                                continue
                            if date_to and idx_date > date_to:
                                continue
                        except:
                            continue

                    # Search in summary and tags
                    if (query_lower in index.summary.lower() or
                            any(query_lower in tag.lower() for tag in index.tags)):
                        results.append({
                            'index': index,
                            'archive_id': index.archive_id,
                            'relevance': self._calculate_relevance(query_lower, index)
                        })

            except Exception as e:
                logger.error(f"Error searching index file {index_file}: {e}")

        # Sort by relevance
        results.sort(key=lambda x: x['relevance'], reverse=True)

        return results

    def retrieve_from_archive(self, archive_id: str, record_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve specific record from archive"""
        try:
            # Find archive files
            archive_files = list(self.archive_base.rglob(f"*_{archive_id}.json.gz"))

            if not archive_files:
                logger.error(f"Archive {archive_id} not found")
                return None

            # Load and search archive
            for archive_file in archive_files:
                with gzip.open(archive_file, 'rt', encoding='utf-8') as f:
                    data = json.load(f)

                for record in data:
                    if record.get('key') == record_key or record.get('email') == record_key:
                        return record

            return None

        except Exception as e:
            logger.error(f"Error retrieving from archive {archive_id}: {e}")
            return None

    def restore_from_archive(self, archive_id: str, record_keys: Optional[List[str]] = None) -> Tuple[bool, str, int]:
        """Restore records from archive"""
        try:
            # Find archive files
            archive_files = list(self.archive_base.rglob(f"*_{archive_id}.json.gz"))

            if not archive_files:
                return False, f"Archive {archive_id} not found", 0

            restored_count = 0

            for archive_file in archive_files:
                # Determine record type from filename
                if 'tasks' in archive_file.name:
                    record_type = 'tasks'
                elif 'team' in archive_file.name:
                    record_type = 'team'
                else:
                    continue

                # Load archive data
                with gzip.open(archive_file, 'rt', encoding='utf-8') as f:
                    data = json.load(f)

                # Filter records if specific keys requested
                if record_keys:
                    data = [r for r in data if r.get('key') in record_keys or r.get('email') in record_keys]

                # Restore records
                if record_type == 'tasks':
                    current_tasks = self.data_manager.load_tasks()

                    for record_data in data:
                        # Check if task already exists
                        if not any(t.key == record_data.get('key') for t in current_tasks):
                            task = Task.from_dict(record_data)
                            current_tasks.append(task)
                            restored_count += 1

                    if restored_count > 0:
                        self.data_manager.save_tasks(current_tasks)

            if restored_count > 0:
                return True, f"Restored {restored_count} records from archive", restored_count
            else:
                return False, "No records restored (may already exist)", 0

        except Exception as e:
            logger.error(f"Error restoring from archive {archive_id}: {e}")
            return False, f"Error: {str(e)}", 0

    def get_archive_summary(self) -> Dict[str, Any]:
        """Get summary of all archives"""
        summary = {
            'total_archives': 0,
            'total_size_mb': 0,
            'archives_by_month': {},
            'oldest_archive': None,
            'newest_archive': None
        }

        try:
            # Find all metadata files
            metadata_files = list(self.archive_base.rglob("*_metadata.json"))

            for metadata_file in metadata_files:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = ArchiveMetadata.from_dict(json.load(f))

                summary['total_archives'] += 1
                summary['total_size_mb'] += metadata.file_size / (1024 * 1024)

                # Track by month
                month_key = metadata.created_date[:7]  # YYYY-MM
                if month_key not in summary['archives_by_month']:
                    summary['archives_by_month'][month_key] = {
                        'count': 0,
                        'records': 0,
                        'size_mb': 0
                    }

                summary['archives_by_month'][month_key]['count'] += 1
                summary['archives_by_month'][month_key]['records'] += metadata.record_count
                summary['archives_by_month'][month_key]['size_mb'] += metadata.file_size / (1024 * 1024)

                # Track oldest/newest
                if not summary['oldest_archive'] or metadata.created_date < summary['oldest_archive']:
                    summary['oldest_archive'] = metadata.created_date

                if not summary['newest_archive'] or metadata.created_date > summary['newest_archive']:
                    summary['newest_archive'] = metadata.created_date

        except Exception as e:
            logger.error(f"Error getting archive summary: {e}")

        return summary

    def cleanup_old_archives(self, retention_days: int) -> Tuple[int, int]:
        """Clean up archives older than retention period"""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        removed_count = 0
        freed_space_mb = 0

        try:
            # Find all metadata files
            metadata_files = list(self.archive_base.rglob("*_metadata.json"))

            for metadata_file in metadata_files:
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = ArchiveMetadata.from_dict(json.load(f))

                    archive_date = datetime.fromisoformat(metadata.created_date)

                    if archive_date < cutoff_date:
                        # Remove archive files
                        archive_dir = metadata_file.parent
                        archive_id = metadata.archive_id

                        # Remove data file
                        data_file = Path(metadata.data_file)
                        if data_file.exists():
                            freed_space_mb += data_file.stat().st_size / (1024 * 1024)
                            data_file.unlink()

                        # Remove index file
                        index_file = Path(metadata.index_file)
                        if index_file.exists():
                            index_file.unlink()

                        # Remove metadata file
                        metadata_file.unlink()

                        removed_count += 1
                        logger.info(f"Removed archive {archive_id} from {archive_date.date()}")

                except Exception as e:
                    logger.error(f"Error removing archive {metadata_file}: {e}")

            return removed_count, int(freed_space_mb)

        except Exception as e:
            logger.error(f"Error cleaning up archives: {e}")
            return 0, 0

    def _calculate_relevance(self, query: str, index: ArchiveIndex) -> float:
        """Calculate relevance score for search result"""
        score = 0.0

        # Check summary
        if query in index.summary.lower():
            score += 2.0

        # Check tags
        for tag in index.tags:
            if query in tag.lower():
                score += 1.0

        # Check exact matches
        if query == index.record_key.lower():
            score += 5.0

        return score

    def create_backup(self, backup_name: Optional[str] = None) -> Tuple[bool, str]:
        """Create full backup of all data"""
        try:
            if not backup_name:
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            backup_dir = self.config.base_path / 'backups' / backup_name
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Backup tasks
            tasks = self.data_manager.load_tasks()
            if tasks:
                tasks_df = pd.DataFrame([t.to_dict() for t in tasks])
                tasks_df.to_excel(backup_dir / 'tasks_backup.xlsx', index=False)

            # Backup team members
            members = self.data_manager.load_team_members()
            if members:
                members_df = pd.DataFrame([m.to_dict() for m in members])
                members_df.to_excel(backup_dir / 'team_backup.xlsx', index=False)

            # Backup legislation
            legislation = self.data_manager.load_legislation()
            if legislation:
                leg_df = pd.DataFrame([l.to_dict() for l in legislation])
                leg_df.to_excel(backup_dir / 'legislation_backup.xlsx', index=False)

            # Create ZIP file
            zip_path = self.config.base_path / 'backups' / f"{backup_name}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for file in backup_dir.glob('*.xlsx'):
                    zf.write(file, file.name)

            # Clean up temporary files
            shutil.rmtree(backup_dir)

            logger.info(f"Created backup: {zip_path}")
            return True, str(zip_path)

        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False, str(e)