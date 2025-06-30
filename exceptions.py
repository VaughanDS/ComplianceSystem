# core/exceptions.py
"""
Custom exceptions for Compliance Management System
Provides specific error handling for different scenarios
"""

from typing import Optional, List, Dict, Any


class ComplianceException(Exception):
    """Base exception for all compliance system errors"""

    def __init__(self, message: str, error_code: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code or "COMPLIANCE_ERROR"
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/API responses"""
        return {
            'error': self.error_code,
            'message': self.message,
            'details': self.details
        }


class ValidationError(ComplianceException):
    """Raised when data validation fails"""

    def __init__(self, message: str, field: Optional[str] = None,
                 validation_errors: Optional[List[str]] = None):
        details = {}
        if field:
            details['field'] = field
        if validation_errors:
            details['validation_errors'] = validation_errors

        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details
        )


class DataIntegrityError(ComplianceException):
    """Raised when data integrity issues are detected"""

    def __init__(self, message: str, table: Optional[str] = None,
                 record_key: Optional[str] = None, issue_type: Optional[str] = None):
        details = {}
        if table:
            details['table'] = table
        if record_key:
            details['record_key'] = record_key
        if issue_type:
            details['issue_type'] = issue_type

        super().__init__(
            message=message,
            error_code="DATA_INTEGRITY_ERROR",
            details=details
        )


class FileAccessError(ComplianceException):
    """Raised when file operations fail"""

    def __init__(self, message: str, file_path: Optional[str] = None,
                 operation: Optional[str] = None, permission_issue: bool = False):
        details = {}
        if file_path:
            details['file_path'] = file_path
        if operation:
            details['operation'] = operation
        if permission_issue:
            details['permission_issue'] = permission_issue

        super().__init__(
            message=message,
            error_code="FILE_ACCESS_ERROR",
            details=details
        )


class FileLockError(ComplianceException):
    """Raised when file locking operations fail"""

    def __init__(self, message: str, file_path: Optional[str] = None,
                 lock_holder: Optional[str] = None, timeout: bool = False):
        details = {}
        if file_path:
            details['file_path'] = file_path
        if lock_holder:
            details['lock_holder'] = lock_holder
        if timeout:
            details['timeout'] = timeout

        super().__init__(
            message=message,
            error_code="FILE_LOCK_ERROR",
            details=details
        )


class AuthenticationError(ComplianceException):
    """Raised when authentication fails"""

    def __init__(self, message: str, username: Optional[str] = None,
                 reason: Optional[str] = None):
        details = {}
        if username:
            details['username'] = username
        if reason:
            details['reason'] = reason

        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            details=details
        )


class ApprovalError(ComplianceException):
    """Raised when approval operations fail"""

    def __init__(self, message: str, task_key: Optional[str] = None,
                 approver: Optional[str] = None, approval_level: Optional[int] = None):
        details = {}
        if task_key:
            details['task_key'] = task_key
        if approver:
            details['approver'] = approver
        if approval_level:
            details['approval_level'] = approval_level

        super().__init__(
            message=message,
            error_code="APPROVAL_ERROR",
            details=details
        )


class ArchiveError(ComplianceException):
    """Raised when archive operations fail"""

    def __init__(self, message: str, archive_path: Optional[str] = None,
                 period: Optional[str] = None):
        details = {}
        if archive_path:
            details['archive_path'] = archive_path
        if period:
            details['period'] = period

        super().__init__(
            message=message,
            error_code="ARCHIVE_ERROR",
            details=details
        )


class ConfigurationError(ComplianceException):
    """Raised when configuration issues are detected"""

    def __init__(self, message: str, config_key: Optional[str] = None,
                 config_file: Optional[str] = None):
        details = {}
        if config_key:
            details['config_key'] = config_key
        if config_file:
            details['config_file'] = config_file

        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=details
        )


class NetworkError(ComplianceException):
    """Raised when network operations fail"""

    def __init__(self, message: str, url: Optional[str] = None,
                 status_code: Optional[int] = None, timeout: bool = False):
        details = {}
        if url:
            details['url'] = url
        if status_code:
            details['status_code'] = status_code
        if timeout:
            details['timeout'] = timeout

        super().__init__(
            message=message,
            error_code="NETWORK_ERROR",
            details=details
        )


class LegislationError(ComplianceException):
    """Raised when legislation reference operations fail"""

    def __init__(self, message: str, legislation_code: Optional[str] = None,
                 operation: Optional[str] = None):
        details = {}
        if legislation_code:
            details['legislation_code'] = legislation_code
        if operation:
            details['operation'] = operation

        super().__init__(
            message=message,
            error_code="LEGISLATION_ERROR",
            details=details
        )


class ExportError(ComplianceException):
    """Raised when export operations fail"""

    def __init__(self, message: str, export_format: Optional[str] = None,
                 export_path: Optional[str] = None, record_count: Optional[int] = None):
        details = {}
        if export_format:
            details['export_format'] = export_format
        if export_path:
            details['export_path'] = export_path
        if record_count:
            details['record_count'] = record_count

        super().__init__(
            message=message,
            error_code="EXPORT_ERROR",
            details=details
        )