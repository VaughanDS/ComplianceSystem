# utils/helpers.py
"""
Helper functions and utilities
"""

import os
import json
import hashlib
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import shutil


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def get_file_hash(file_path: Union[str, Path]) -> str:
    """
    Calculate SHA256 hash of a file

    Args:
        file_path: Path to file

    Returns:
        Hex string of file hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if not

    Args:
        path: Directory path

    Returns:
        Path object
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def backup_file(file_path: Union[str, Path], backup_dir: Optional[Union[str, Path]] = None) -> Path:
    """
    Create backup of file

    Args:
        file_path: File to backup
        backup_dir: Backup directory (default: same directory)

    Returns:
        Path to backup file
    """
    source = Path(file_path)
    if not source.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Determine backup directory
    if backup_dir is None:
        backup_dir = source.parent
    else:
        backup_dir = Path(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)

    # Generate backup filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{source.stem}_backup_{timestamp}{source.suffix}"
    backup_path = backup_dir / backup_name

    # Copy file
    shutil.copy2(source, backup_path)
    return backup_path


def format_date(date_obj: Union[date, datetime, str], format: str = "%d/%m/%Y") -> str:
    """
    Format date object to string

    Args:
        date_obj: Date object or string
        format: Output format

    Returns:
        Formatted date string
    """
    if isinstance(date_obj, str):
        # Try to parse if string
        try:
            date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
        except ValueError:
            return date_obj

    if isinstance(date_obj, datetime):
        date_obj = date_obj.date()

    return date_obj.strftime(format)


def format_datetime(dt_obj: Union[datetime, str], format: str = "%d/%m/%Y %H:%M") -> str:
    """
    Format datetime object to string

    Args:
        dt_obj: Datetime object or string
        format: Output format

    Returns:
        Formatted datetime string
    """
    if isinstance(dt_obj, str):
        # Try to parse if string
        try:
            dt_obj = datetime.strptime(dt_obj, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return dt_obj

    return dt_obj.strftime(format)


def parse_date(date_str: str, format: str = "%d/%m/%Y") -> Optional[date]:
    """
    Parse date string to date object

    Args:
        date_str: Date string
        format: Input format

    Returns:
        Date object or None if parsing fails
    """
    try:
        return datetime.strptime(date_str, format).date()
    except ValueError:
        return None


def parse_datetime(dt_str: str, format: str = "%d/%m/%Y %H:%M") -> Optional[datetime]:
    """
    Parse datetime string to datetime object

    Args:
        dt_str: Datetime string
        format: Input format

    Returns:
        Datetime object or None if parsing fails
    """
    try:
        return datetime.strptime(dt_str, format)
    except ValueError:
        return None


def get_business_days(start_date: date, end_date: date) -> int:
    """
    Calculate number of business days between two dates

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        Number of business days
    """
    business_days = 0
    current_date = start_date

    while current_date <= end_date:
        if current_date.weekday() < 5:  # Monday = 0, Friday = 4
            business_days += 1
        current_date += timedelta(days=1)

    return business_days


def add_business_days(start_date: date, days: int) -> date:
    """
    Add business days to a date

    Args:
        start_date: Start date
        days: Number of business days to add

    Returns:
        Resulting date
    """
    current_date = start_date
    days_added = 0

    while days_added < days:
        current_date += timedelta(days=1)
        if current_date.weekday() < 5:  # Monday = 0, Friday = 4
            days_added += 1

    return current_date


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    Safely load JSON string

    Args:
        json_str: JSON string
        default: Default value if parsing fails

    Returns:
        Parsed object or default value
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """
    Safely dump object to JSON string

    Args:
        obj: Object to serialize
        default: Default string if serialization fails

    Returns:
        JSON string or default
    """
    try:
        return json.dumps(obj, default=str)
    except (TypeError, ValueError):
        return default


def get_quarter(date_obj: date) -> int:
    """
    Get quarter number for a date

    Args:
        date_obj: Date object

    Returns:
        Quarter number (1-4)
    """
    return (date_obj.month - 1) // 3 + 1


def get_week_number(date_obj: date) -> int:
    """
    Get ISO week number for a date

    Args:
        date_obj: Date object

    Returns:
        Week number
    """
    return date_obj.isocalendar()[1]


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate string to maximum length

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def generate_unique_id(prefix: str = "") -> str:
    """
    Generate unique identifier

    Args:
        prefix: Optional prefix

    Returns:
        Unique ID string
    """
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    if prefix:
        return f"{prefix}_{timestamp}_{unique_id}"
    return f"{timestamp}_{unique_id}"