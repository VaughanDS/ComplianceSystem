# core/constants.py
"""
Constants and enumerations for Compliance Management System
Provides type safety and centralised management of options
"""

from enum import Enum, auto
from typing import Dict, List, Tuple


class TaskStatus(Enum):
    """Task status enumeration"""
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    PENDING_APPROVAL = "Pending Approval"
    SENT_FOR_APPROVAL = "Sent For Approval"
    APPROVED = "Approved"
    RESOLVED = "Resolved"
    CLOSED = "Closed"
    ON_HOLD = "On Hold"

    @classmethod
    def get_active_statuses(cls) -> List[str]:
        """Get list of active status values"""
        return [
            cls.OPEN.value,
            cls.IN_PROGRESS.value,
            cls.PENDING_APPROVAL.value,
            cls.SENT_FOR_APPROVAL.value,
            cls.ON_HOLD.value
        ]

    @classmethod
    def get_completed_statuses(cls) -> List[str]:
        """Get list of completed status values"""
        return [
            cls.APPROVED.value,
            cls.RESOLVED.value,
            cls.CLOSED.value
        ]

    @classmethod
    def requires_approval(cls, status: str) -> bool:
        """Check if status requires approval"""
        return status in [cls.PENDING_APPROVAL.value, cls.SENT_FOR_APPROVAL.value]


class Priority(Enum):
    """Task priority enumeration"""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

    @classmethod
    def get_sort_order(cls) -> Dict[str, int]:
        """Get priority sort order (lower number = higher priority)"""
        return {
            cls.CRITICAL.value: 1,
            cls.HIGH.value: 2,
            cls.MEDIUM.value: 3,
            cls.LOW.value: 4
        }

    @classmethod
    def get_colour_map(cls) -> Dict[str, str]:
        """Get priority colour mapping for UI"""
        return {
            cls.CRITICAL.value: "#dc3545",  # Red
            cls.HIGH.value: "#fd7e14",  # Orange
            cls.MEDIUM.value: "#ffc107",  # Yellow
            cls.LOW.value: "#28a745"  # Green
        }


class UserRole(Enum):
    """User role enumeration"""
    ADMIN = "Admin"
    COMPLIANCE_MANAGER = "Compliance Manager"
    COMPLIANCE_OFFICER = "Compliance Officer"
    TEAM_LEAD = "Team Lead"
    TEAM_MEMBER = "Team Member"
    VIEWER = "Viewer"

    @classmethod
    def get_permission_levels(cls) -> Dict[str, int]:
        """Get permission levels (lower number = higher permissions)"""
        return {
            cls.ADMIN.value: 1,
            cls.COMPLIANCE_MANAGER.value: 2,
            cls.COMPLIANCE_OFFICER.value: 3,
            cls.TEAM_LEAD.value: 4,
            cls.TEAM_MEMBER.value: 5,
            cls.VIEWER.value: 6
        }

    @classmethod
    def get_capabilities(cls, role: str) -> List[str]:
        """Get capabilities for a role"""
        capabilities_map = {
            cls.ADMIN.value: [
                'view_all', 'edit_all', 'delete_all', 'manage_users',
                'manage_team', 'approve_tasks', 'export_data', 'view_reports',
                'configure_system', 'manage_archives'
            ],
            cls.COMPLIANCE_MANAGER.value: [
                'view_all', 'edit_all', 'delete_own', 'manage_team',
                'approve_tasks', 'export_data', 'view_reports', 'manage_archives'
            ],
            cls.COMPLIANCE_OFFICER.value: [
                'view_all', 'edit_own', 'create_tasks', 'approve_tasks',
                'export_data', 'view_reports'
            ],
            cls.TEAM_LEAD.value: [
                'view_department', 'edit_department', 'create_tasks',
                'view_reports'
            ],
            cls.TEAM_MEMBER.value: [
                'view_assigned', 'edit_assigned', 'create_tasks'
            ],
            cls.VIEWER.value: [
                'view_assigned'
            ]
        }
        return capabilities_map.get(role, [])


class Department(Enum):
    """Department enumeration"""
    EXEC = "Executive"
    FINANCE = "Finance"
    LEGAL = "Legal"
    HR = "Human Resources"
    IT = "Information Technology"
    OPERATIONS = "Operations"
    COMPLIANCE = "Compliance"
    RISK = "Risk Management"
    AUDIT = "Internal Audit"
    MARKETING = "Marketing"
    SALES = "Sales"
    PROCUREMENT = "Procurement"
    LOGISTICS = "Logistics"
    QUALITY = "Quality Assurance"

    @classmethod
    def get_abbreviations(cls) -> Dict[str, str]:
        """Get department abbreviations"""
        return {
            cls.EXEC.value: "EXEC",
            cls.FINANCE.value: "FIN",
            cls.LEGAL.value: "LEG",
            cls.HR.value: "HR",
            cls.IT.value: "IT",
            cls.OPERATIONS.value: "OPS",
            cls.COMPLIANCE.value: "COMP",
            cls.RISK.value: "RISK",
            cls.AUDIT.value: "AUD",
            cls.MARKETING.value: "MKT",
            cls.SALES.value: "SLS",
            cls.PROCUREMENT.value: "PROC",
            cls.LOGISTICS.value: "LOG",
            cls.QUALITY.value: "QA"
        }


class FileType(Enum):
    """File type enumeration"""
    TASKS = "tasks"
    TEAM = "team"
    LEGISLATION = "legislation"
    INDEX = "index"
    ARCHIVE = "archive"
    EXPORT = "export"
    ATTACHMENT = "attachment"

    @classmethod
    def get_extensions(cls) -> Dict[str, List[str]]:
        """Get allowed file extensions for each type"""
        return {
            cls.TASKS.value: ['.xlsx', '.xls'],
            cls.TEAM.value: ['.xlsx', '.xls'],
            cls.LEGISLATION.value: ['.xlsx', '.xls'],
            cls.INDEX.value: ['.xlsx', '.xls'],
            cls.ARCHIVE.value: ['.zip', '.tar', '.gz'],
            cls.EXPORT.value: ['.xlsx', '.csv', '.pdf'],
            cls.ATTACHMENT.value: ['.pdf', '.doc', '.docx', '.xlsx', '.xls',
                                   '.png', '.jpg', '.jpeg', '.txt']
        }


class NotificationType(Enum):
    """Notification type enumeration"""
    TASK_CREATED = "task_created"
    TASK_ASSIGNED = "task_assigned"
    TASK_UPDATED = "task_updated"
    TASK_COMPLETED = "task_completed"
    APPROVAL_REQUIRED = "approval_required"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_REJECTED = "approval_rejected"
    REMINDER = "reminder"
    SYSTEM = "system"

    @classmethod
    def get_templates(cls) -> Dict[str, str]:
        """Get notification message templates"""
        return {
            cls.TASK_CREATED.value: "New task created: {task_title}",
            cls.TASK_ASSIGNED.value: "Task assigned to you: {task_title}",
            cls.TASK_UPDATED.value: "Task updated: {task_title}",
            cls.TASK_COMPLETED.value: "Task completed: {task_title}",
            cls.APPROVAL_REQUIRED.value: "Approval required for: {task_title}",
            cls.APPROVAL_GRANTED.value: "Approval granted for: {task_title}",
            cls.APPROVAL_REJECTED.value: "Approval rejected for: {task_title}",
            cls.REMINDER.value: "Reminder: {task_title} - Due {due_date}",
            cls.SYSTEM.value: "{message}"
        }


class ApprovalStatus(Enum):
    """Approval status enumeration"""
    NOT_REQUIRED = "Not Required"
    PENDING = "Pending"
    IN_REVIEW = "In Review"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    CONDITIONAL = "Conditional"

    @classmethod
    def get_final_statuses(cls) -> List[str]:
        """Get final approval statuses"""
        return [
            cls.NOT_REQUIRED.value,
            cls.APPROVED.value,
            cls.REJECTED.value
        ]


# Compliance area categories
COMPLIANCE_AREAS = [
    "IT Security & Data Protection",
    "Product Liability & Traceability",
    "Restricted Practices & Trade",
    "Legal & Contractual",
    "Environmental & Sustainability",
    "Health & Safety",
    "Data Protection",
    "Financial",
    "Operational"
]

# Task subcategories by compliance area
TASK_SUBCATEGORIES = {
    "IT Security & Data Protection": [
        "Data Protection", "Cybersecurity", "Access Control",
        "Data Retention", "Incident Response", "Other"
    ],
    "Product Liability & Traceability": [
        "Product Safety", "Labelling", "Recalls", "Traceability",
        "Quality Control", "Other"
    ],
    "Restricted Practices & Trade": [
        "Export Controls", "Sanctions", "Anti-Competition",
        "Trade Agreements", "Other"
    ],
    "Legal & Contractual": [
        "Contract Management", "Intellectual Property", "Disputes",
        "Corporate Governance", "Other"
    ],
    "Environmental & Sustainability": [
        "Waste Management", "Emissions", "Energy Efficiency",
        "Sustainable Sourcing", "Other"
    ],
    "Health & Safety": [
        "Workplace Safety", "Risk Assessments", "Safety Training",
        "Incident Reports", "Equipment Checks", "Emergency Procedures", "Other"
    ],
    "Data Protection": [
        "GDPR Compliance", "Data Requests", "Privacy Policies",
        "Data Breaches", "Training", "Other"
    ],
    "Financial": [
        "Tax Compliance", "Financial Reporting", "Audits",
        "Regulatory Returns", "Other"
    ],
    "Operational": [
        "General Compliance", "Process Updates", "System Changes",
        "Documentation", "Other"
    ]
}

# System constants
MAX_FILE_SIZE_MB = 50
MAX_ATTACHMENTS_PER_TASK = 10
SESSION_TIMEOUT_MINUTES = 30
AUTO_SAVE_INTERVAL_SECONDS = 300
SEARCH_RESULTS_LIMIT = 100
EXPORT_BATCH_SIZE = 1000
ARCHIVE_RETENTION_DAYS = 90

# Date and time formats
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DISPLAY_DATE_FORMAT = "%d/%m/%Y"
DISPLAY_DATETIME_FORMAT = "%d/%m/%Y %H:%M"

# Email constants
EMAIL_MAX_RECIPIENTS = 50
EMAIL_SUBJECT_PREFIX = "[Compliance System]"
EMAIL_RETRY_ATTEMPTS = 3
EMAIL_RETRY_DELAY_SECONDS = 60

# UI constants
WINDOW_MIN_WIDTH = 1200
WINDOW_MIN_HEIGHT = 800
TABLE_ROW_HEIGHT = 25
DIALOG_WIDTH = 600
DIALOG_HEIGHT = 400