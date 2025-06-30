# config/database.py
"""
Database configuration and data integrity management
Handles Excel file schemas and validation rules
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
import re

from config.settings import get_config


class DatabaseConfig:
    """Database and Excel configuration settings"""

    def __init__(self):
        self.config = get_config()

        # Excel column schemas - Standardized column names
        self.task_columns = [
            'Task Key', 'Title', 'Compliance Area', 'Subcategory',
            'Task Setter', 'Task Setter Email', 'Allocated To',
            'Allocated Emails', 'Manager', 'Manager Email',
            'Priority', 'Description', 'Status', 'Date Logged',
            'Target Close Date', 'Completed Date', 'Actions',
            'Attachments', 'Approvals', 'Tags', 'Custom Fields'
        ]

        self.team_columns = [
            'Name', 'Email', 'Department', 'Role', 'Location',
            'Employee ID', 'Phone', 'Manager', 'Start Date',
            'Permissions', 'Active', 'Created Date', 'Last Login',
            'Preferences'
        ]

        self.legislation_columns = [
            'Code', 'Title', 'Category', 'Jurisdiction',
            'Effective Date', 'Description', 'Requirements',
            'Penalties', 'Last Updated', 'Review Frequency',
            'Owner', 'Related Tasks', 'Related Documents',
            'Compliance Checks'
        ]

        self.index_columns = [
            'Index Key', 'Table', 'Record Key', 'Field Name',
            'Field Value', 'Last Updated', 'Search Weight'
        ]

        # Required fields for validation
        self.required_task_fields = [
            'Task Key', 'Title', 'Compliance Area', 'Task Setter',
            'Priority', 'Description'
        ]

        self.required_team_fields = [
            'Name', 'Email', 'Department', 'Role', 'Location'
        ]

        self.required_legislation_fields = [
            'Code', 'Title', 'Category', 'Jurisdiction'
        ]

        # Data formats
        self.date_format = "%Y-%m-%d"
        self.datetime_format = "%Y-%m-%d %H:%M:%S"
        self.email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'  # Fixed regex pattern
        )

        # File settings
        self.max_file_size_mb = 10
        self.allowed_extensions = {
            '.pdf', '.doc', '.docx', '.xlsx', '.xls',
            '.png', '.jpg', '.jpeg', '.txt', '.csv'
        }

        # Performance settings
        self.batch_size = 1000
        self.cache_ttl_seconds = 300
        self.lock_timeout_seconds = 30

    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        if not email:
            return False
        return bool(self.email_pattern.match(email.strip()))

    def validate_date(self, date_str: str) -> bool:
        """Validate date format"""
        try:
            datetime.strptime(date_str, self.date_format)
            return True
        except ValueError:
            return False

    def get_file_lock_path(self, file_path: Path) -> Path:
        """Get lock file path for a given file"""
        return file_path.parent / f".{file_path.name}.lock"

    def to_dict(self) -> dict:
        """Convert config to dictionary"""
        return {
            k: v for k, v in self.__dict__.items()
            if not k.startswith('_') and k != 'config'  # Exclude config reference
        }


# Singleton instance
_db_config_instance = None


def get_db_config() -> DatabaseConfig:
    """Get the singleton database configuration instance"""
    global _db_config_instance
    if _db_config_instance is None:
        _db_config_instance = DatabaseConfig()
    return _db_config_instance


def reset_db_config():
    """Reset database configuration (mainly for testing)"""
    global _db_config_instance
    _db_config_instance = None


class DataIntegrityValidator:
    """Validates data integrity for Excel operations"""

    def __init__(self, db_config: DatabaseConfig):
        self.config = db_config

    def validate_task_data(self, data: dict) -> tuple[bool, List[str]]:
        """Validate task data completeness and format"""
        errors = []

        # Check required fields
        for field in self.config.required_task_fields:
            if field not in data or not data[field]:
                errors.append(f"Required field missing: {field}")

        # Validate email formats
        if 'Task Setter Email' in data and data['Task Setter Email']:
            if not self.config.validate_email(data['Task Setter Email']):
                errors.append("Invalid task setter email format")

        # Validate manager email if present
        if 'Manager Email' in data and data['Manager Email']:
            if not self.config.validate_email(data['Manager Email']):
                errors.append("Invalid manager email format")

        # Validate dates
        date_fields = ['Date Logged', 'Target Close Date', 'Completed Date']
        for field in date_fields:
            if field in data and data[field]:
                if not self.config.validate_date(str(data[field])):
                    errors.append(f"Invalid date format for {field}")

        return len(errors) == 0, errors

    def validate_team_data(self, data: dict) -> tuple[bool, List[str]]:
        """Validate team member data"""
        errors = []

        # Check required fields
        for field in self.config.required_team_fields:
            if field not in data or not data[field]:
                errors.append(f"Required field missing: {field}")

        # Validate email
        if 'Email' in data and data['Email']:
            if not self.config.validate_email(data['Email']):
                errors.append("Invalid email format")

        return len(errors) == 0, errors


class ExcelSchema:
    """Defines Excel file schemas and provides validation"""

    def __init__(self, db_config: DatabaseConfig):
        self.config = db_config
        self.schemas = {
            'tasks': self.config.task_columns,
            'team': self.config.team_columns,
            'legislation': self.config.legislation_columns,
            'index': self.config.index_columns
        }

    def get_schema(self, file_type: str) -> List[str]:
        """Get schema for a specific file type"""
        return self.schemas.get(file_type, [])

    def validate_dataframe(self, df, file_type: str) -> tuple[bool, List[str]]:
        """Validate dataframe against schema"""
        errors = []
        expected_columns = self.get_schema(file_type)

        if not expected_columns:
            errors.append(f"Unknown file type: {file_type}")
            return False, errors

        # Check for missing columns
        missing_columns = set(expected_columns) - set(df.columns)
        if missing_columns:
            errors.append(f"Missing columns: {', '.join(missing_columns)}")

        # Check for extra columns (warning only)
        extra_columns = set(df.columns) - set(expected_columns)
        if extra_columns:
            errors.append(f"Warning - Extra columns found: {', '.join(extra_columns)}")

        return len([e for e in errors if not e.startswith('Warning')]) == 0, errors

    def create_empty_dataframe(self, file_type: str):
        """Create empty dataframe with correct schema"""
        import pandas as pd
        columns = self.get_schema(file_type)
        return pd.DataFrame(columns=columns)