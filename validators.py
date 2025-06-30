# utils/validators.py
"""
Input validation utilities
"""

import re
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pathlib import Path


def validate_email(email: str) -> bool:
    """
    Validate email address format

    Args:
        email: Email address to validate

    Returns:
        True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_date_string(date_str: str, format: str = "%Y-%m-%d") -> bool:
    """
    Validate date string format

    Args:
        date_str: Date string to validate
        format: Expected date format

    Returns:
        True if valid, False otherwise
    """
    try:
        datetime.strptime(date_str, format)
        return True
    except ValueError:
        return False


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """
    Validate file extension

    Args:
        filename: Filename to check
        allowed_extensions: List of allowed extensions (with dots, e.g., ['.pdf', '.docx'])

    Returns:
        True if valid, False otherwise
    """
    file_path = Path(filename)
    return file_path.suffix.lower() in [ext.lower() for ext in allowed_extensions]


def validate_file_size(file_path: str, max_size_mb: float) -> bool:
    """
    Validate file size

    Args:
        file_path: Path to file
        max_size_mb: Maximum size in megabytes

    Returns:
        True if within size limit, False otherwise
    """
    try:
        file_size = Path(file_path).stat().st_size
        max_size_bytes = max_size_mb * 1024 * 1024
        return file_size <= max_size_bytes
    except:
        return False


def validate_task_key(key: str) -> bool:
    """
    Validate task key format (GS-TASK-YYMMDD-XXXX)

    Args:
        key: Task key to validate

    Returns:
        True if valid, False otherwise
    """
    pattern = r'^GS-TASK-\d{6}-\d{4}$'
    return bool(re.match(pattern, key))


def validate_priority(priority: str) -> bool:
    """
    Validate priority value

    Args:
        priority: Priority to validate

    Returns:
        True if valid, False otherwise
    """
    valid_priorities = ['Critical', 'High', 'Medium', 'Low']
    return priority in valid_priorities


def validate_status(status: str) -> bool:
    """
    Validate task status

    Args:
        status: Status to validate

    Returns:
        True if valid, False otherwise
    """
    valid_statuses = [
        'Open', 'In Progress', 'Pending Approval', 'Sent For Approval',
        'Approved', 'Resolved', 'Closed', 'On Hold'
    ]
    return status in valid_statuses


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """
    Validate required fields are present and non-empty

    Args:
        data: Dictionary to validate
        required_fields: List of required field names

    Returns:
        List of missing field names
    """
    missing = []
    for field in required_fields:
        if field not in data or not data[field]:
            missing.append(field)
    return missing


def validate_text_length(text: str, min_length: int = 0,
                         max_length: Optional[int] = None) -> bool:
    """
    Validate text length

    Args:
        text: Text to validate
        min_length: Minimum length
        max_length: Maximum length (None for no limit)

    Returns:
        True if valid, False otherwise
    """
    text_len = len(text.strip())
    if text_len < min_length:
        return False
    if max_length is not None and text_len > max_length:
        return False
    return True


def validate_phone_number(phone: str) -> bool:
    """
    Validate UK phone number format

    Args:
        phone: Phone number to validate

    Returns:
        True if valid, False otherwise
    """
    # Remove spaces and dashes
    phone_clean = re.sub(r'[\s\-]', '', phone)

    # UK phone number patterns
    patterns = [
        r'^(?:\+44|0044|0)(?:7\d{9}|[1-9]\d{8,9})$',  # UK mobile or landline
        r'^\d{10,11}$'  # Simple 10-11 digit format
    ]

    return any(re.match(pattern, phone_clean) for pattern in patterns)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = Path(filename).name

    # Replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')

    # Limit length
    name, ext = Path(filename).stem, Path(filename).suffix
    if len(name) > 200:
        name = name[:200]

    return name + ext


def validate_compliance_area(area: str, valid_areas: List[str]) -> bool:
    """
    Validate compliance area

    Args:
        area: Compliance area to validate
        valid_areas: List of valid compliance areas

    Returns:
        True if valid, False otherwise
    """
    return area in valid_areas