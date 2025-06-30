# core/models.py
"""
Data models for Compliance Management System
Provides structured representations of core business entities
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import json
import re

# Import enums separately to avoid circular imports
from enum import Enum


# Re-define minimal enums needed for validation
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


class Priority(Enum):
    """Task priority enumeration"""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class UserRole(Enum):
    """User role enumeration"""
    ADMIN = "Admin"
    COMPLIANCE_MANAGER = "Compliance Manager"
    COMPLIANCE_OFFICER = "Compliance Officer"
    TEAM_LEAD = "Team Lead"
    TEAM_MEMBER = "Team Member"
    VIEWER = "Viewer"


class ApprovalStatus(Enum):
    """Approval status enumeration"""
    NOT_REQUIRED = "Not Required"
    PENDING = "Pending"
    IN_REVIEW = "In Review"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    CONDITIONAL = "Conditional"


@dataclass
class TaskAction:
    """Represents an action taken on a task"""
    timestamp: str
    user: str
    action: str
    details: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp,
            'user': self.user,
            'action': self.action,
            'details': self.details,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskAction':
        """Create from dictionary"""
        return cls(
            timestamp=data.get('timestamp', ''),
            user=data.get('user', ''),
            action=data.get('action', ''),
            details=data.get('details', ''),
            metadata=data.get('metadata', {})
        )


@dataclass
class FileAttachment:
    """Represents a file attachment"""
    filename: str
    original_name: str
    file_path: str
    file_size: int
    mime_type: str
    uploaded_by: str
    uploaded_date: str
    checksum: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'filename': self.filename,
            'original_name': self.original_name,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'uploaded_by': self.uploaded_by,
            'uploaded_date': self.uploaded_date,
            'checksum': self.checksum
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileAttachment':
        """Create from dictionary"""
        return cls(
            filename=data.get('filename', ''),
            original_name=data.get('original_name', ''),
            file_path=data.get('file_path', ''),
            file_size=data.get('file_size', 0),
            mime_type=data.get('mime_type', ''),
            uploaded_by=data.get('uploaded_by', ''),
            uploaded_date=data.get('uploaded_date', ''),
            checksum=data.get('checksum')
        )


@dataclass
class ApprovalRecord:
    """Represents an approval record"""
    approval_id: str
    task_key: str
    approver: str
    approval_date: str
    approval_status: str
    comments: str = ""
    conditions: List[str] = field(default_factory=list)
    approval_level: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'approval_id': self.approval_id,
            'task_key': self.task_key,
            'approver': self.approver,
            'approval_date': self.approval_date,
            'approval_status': self.approval_status,
            'comments': self.comments,
            'conditions': self.conditions,
            'approval_level': self.approval_level
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApprovalRecord':
        """Create from dictionary"""
        return cls(
            approval_id=data.get('approval_id', ''),
            task_key=data.get('task_key', ''),
            approver=data.get('approver', ''),
            approval_date=data.get('approval_date', ''),
            approval_status=data.get('approval_status', ''),
            comments=data.get('comments', ''),
            conditions=data.get('conditions', []),
            approval_level=data.get('approval_level', 1)
        )


@dataclass
class Task:
    """Main task model"""
    # Required fields
    key: str
    title: str
    compliance_area: str
    subcategory: str
    task_setter: str
    task_setter_email: str
    allocated_to: List[str]
    allocated_emails: List[str]
    manager: str
    manager_email: str
    priority: str
    description: str

    # Optional fields with defaults
    status: str = TaskStatus.OPEN.value
    date_logged: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    target_date: str = ""
    completed_date: str = ""

    # Tracking fields
    created_by: str = ""
    created_date: str = ""
    modified_by: str = ""
    modified_date: str = ""

    # Complex fields
    actions: List[TaskAction] = field(default_factory=list)
    attachments: List[FileAttachment] = field(default_factory=list)
    approvals: List[ApprovalRecord] = field(default_factory=list)

    # Additional metadata
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate task data after initialization"""
        self._validate()

    def _validate(self):
        """Validate task data"""
        errors = []

        # Required field validation
        if not self.key:
            errors.append("Task key is required")
        if not self.title:
            errors.append("Task title is required")
        if not self.compliance_area:
            errors.append("Compliance area is required")
        if not self.priority:
            errors.append("Priority is required")

        # Email validation
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if self.task_setter_email and not email_pattern.match(self.task_setter_email):
            errors.append("Invalid task setter email")
        if self.manager_email and not email_pattern.match(self.manager_email):
            errors.append("Invalid manager email")

        # Status validation
        valid_statuses = [s.value for s in TaskStatus]
        if self.status not in valid_statuses:
            errors.append(f"Invalid status: {self.status}")

        # Priority validation
        valid_priorities = [p.value for p in Priority]
        if self.priority not in valid_priorities:
            errors.append(f"Invalid priority: {self.priority}")

        if errors:
            from core.exceptions import ValidationError
            raise ValidationError(
                f"Task validation failed: {'; '.join(errors)}",
                field="task",
                validation_errors=errors
            )

    def add_action(self, user: str, action: str, details: str,
                   metadata: Optional[Dict[str, Any]] = None):
        """Add an action to the task"""
        action_record = TaskAction(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user=user,
            action=action,
            details=details,
            metadata=metadata or {}
        )
        self.actions.append(action_record)
        self.modified_by = user
        self.modified_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def update_status(self, new_status: str, updated_by: str, comment: str = ""):
        """Update task status with tracking"""
        old_status = self.status
        self.status = new_status
        self.add_action(
            updated_by,
            'status_change',
            f'Status changed from {old_status} to {new_status}. {comment}'.strip()
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'key': self.key,
            'title': self.title,
            'compliance_area': self.compliance_area,
            'subcategory': self.subcategory,
            'task_setter': self.task_setter,
            'task_setter_email': self.task_setter_email,
            'allocated_to': self.allocated_to,
            'allocated_emails': self.allocated_emails,
            'manager': self.manager,
            'manager_email': self.manager_email,
            'priority': self.priority,
            'description': self.description,
            'status': self.status,
            'date_logged': self.date_logged,
            'target_date': self.target_date,
            'completed_date': self.completed_date,
            'created_by': self.created_by,
            'created_date': self.created_date,
            'modified_by': self.modified_by,
            'modified_date': self.modified_date,
            'actions': [a.to_dict() for a in self.actions],
            'attachments': [a.to_dict() for a in self.attachments],
            'approvals': [a.to_dict() for a in self.approvals],
            'tags': self.tags,
            'custom_fields': self.custom_fields
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create task from dictionary"""
        # Create a copy to avoid modifying the original
        data_copy = data.copy()

        # Extract complex fields
        actions_data = data_copy.pop('actions', [])
        attachments_data = data_copy.pop('attachments', [])
        approvals_data = data_copy.pop('approvals', [])

        # Create task
        task = cls(**data_copy)

        # Reconstruct complex fields
        task.actions = [TaskAction.from_dict(a) for a in actions_data]
        task.attachments = [FileAttachment.from_dict(a) for a in attachments_data]
        task.approvals = [ApprovalRecord.from_dict(a) for a in approvals_data]

        return task


@dataclass
class TeamMember:
    """Team member model"""
    name: str
    email: str
    department: str
    role: str
    location: str

    # Optional fields
    employee_id: str = ""
    phone: str = ""
    manager: str = ""
    start_date: str = ""
    permissions: List[str] = field(default_factory=list)
    active: bool = True

    # Metadata
    created_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    last_login: str = ""
    preferences: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate team member data"""
        self._validate()

    def _validate(self):
        """Validate team member data"""
        errors = []

        if not self.name:
            errors.append("Name is required")

        # Email validation with proper regex
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not self.email or not email_pattern.match(self.email):
            errors.append("Valid email is required")

        if not self.department:
            errors.append("Department is required")
        if not self.role:
            errors.append("Role is required")

        # Validate role
        valid_roles = [r.value for r in UserRole]
        if self.role not in valid_roles:
            errors.append(f"Invalid role: {self.role}")

        if errors:
            from core.exceptions import ValidationError
        raise ValidationError(
            f"Team member validation failed: {'; '.join(errors)}",
            field="team_member",
            validation_errors=errors
        )

    def has_permission(self, permission: str) -> bool:
        """Check if member has specific permission"""
        # Check role-based permissions
        role_capabilities = {
            UserRole.ADMIN.value: [
                'view_all', 'edit_all', 'delete_all', 'manage_users',
                'manage_team', 'approve_tasks', 'export_data', 'view_reports',
                'configure_system', 'manage_archives'
            ],
            UserRole.COMPLIANCE_MANAGER.value: [
                'view_all', 'edit_all', 'delete_own', 'manage_team',
                'approve_tasks', 'export_data', 'view_reports', 'manage_archives'
            ],
            UserRole.COMPLIANCE_OFFICER.value: [
                'view_all', 'edit_own', 'create_tasks', 'approve_tasks',
                'export_data', 'view_reports'
            ],
            UserRole.TEAM_LEAD.value: [
                'view_department', 'edit_department', 'create_tasks',
                'view_reports'
            ],
            UserRole.TEAM_MEMBER.value: [
                'view_assigned', 'edit_assigned', 'create_tasks'
            ],
            UserRole.VIEWER.value: [
                'view_assigned'
            ]
        }

        role_permissions = role_capabilities.get(self.role, [])
        if permission in role_permissions:
            return True

        # Check individual permissions
        return permission in self.permissions

    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'email': self.email,
            'department': self.department,
            'role': self.role,
            'location': self.location,
            'employee_id': self.employee_id,
            'phone': self.phone,
            'manager': self.manager,
            'start_date': self.start_date,
            'permissions': self.permissions,
            'active': self.active,
            'created_date': self.created_date,
            'last_login': self.last_login,
            'preferences': self.preferences
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TeamMember':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class LegislationReference:
    """Legislation reference model"""
    code: str
    title: str
    category: str
    jurisdiction: str
    effective_date: str

    # Optional fields
    description: str = ""
    requirements: List[str] = field(default_factory=list)
    penalties: str = ""
    last_updated: str = ""
    review_frequency: str = ""
    owner: str = ""

    # Additional fields for comprehensive tracking
    full_name: str = ""
    subcategory: str = ""
    applicable_areas: List[str] = field(default_factory=list)
    summary: str = ""
    key_requirements: List[str] = field(default_factory=list)
    reference_links: List[str] = field(default_factory=list)
    internal_guidance: str = ""

    # Related items
    related_tasks: List[str] = field(default_factory=list)
    related_documents: List[str] = field(default_factory=list)
    compliance_checks: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        """Validate legislation data"""
        self._validate()
        # Set full_name if not provided
        if not self.full_name and self.title:
            self.full_name = self.title

    def _validate(self):
        """Validate legislation reference"""
        errors = []

        if not self.code:
            errors.append("Legislation code is required")
        if not self.title:
            errors.append("Title is required")
        if not self.category:
            errors.append("Category is required")
        if not self.jurisdiction:
            errors.append("Jurisdiction is required")

        if errors:
            from core.exceptions import ValidationError
            raise ValidationError(
                f"Legislation validation failed: {'; '.join(errors)}",
                field="legislation",
                validation_errors=errors
            )

    def is_current(self) -> bool:
        """Check if legislation is currently in effect"""
        if not self.effective_date:
            return True

        try:
            effective = datetime.strptime(self.effective_date, "%Y-%m-%d")
            return datetime.now() >= effective
        except ValueError:
            return True

    def add_compliance_check(self, check_date: str, compliant: bool,
                             checked_by: str, notes: str = ""):
        """Add a compliance check record"""
        check = {
            'date': check_date,
            'compliant': compliant,
            'checked_by': checked_by,
            'notes': notes
        }
        self.compliance_checks.append(check)

    def get_last_check(self) -> Optional[Dict[str, Any]]:
        """Get the most recent compliance check"""
        if not self.compliance_checks:
            return None

        # Sort by date and return the latest
        sorted_checks = sorted(
            self.compliance_checks,
            key=lambda x: x.get('date', ''),
            reverse=True
        )
        return sorted_checks[0] if sorted_checks else None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'code': self.code,
            'title': self.title,
            'full_name': self.full_name,
            'category': self.category,
            'subcategory': self.subcategory,
            'jurisdiction': self.jurisdiction,
            'effective_date': self.effective_date,
            'description': self.description,
            'requirements': self.requirements,
            'penalties': self.penalties,
            'last_updated': self.last_updated,
            'review_frequency': self.review_frequency,
            'owner': self.owner,
            'applicable_areas': self.applicable_areas,
            'summary': self.summary,
            'key_requirements': self.key_requirements,
            'reference_links': self.reference_links,
            'internal_guidance': self.internal_guidance,
            'related_tasks': self.related_tasks,
            'related_documents': self.related_documents,
            'compliance_checks': self.compliance_checks
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LegislationReference':
        """Create from dictionary"""
        return cls(**data)