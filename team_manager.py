# business/team_manager.py - Fixed with missing methods
"""
Team management business logic
Handles team member operations and department management
"""

from typing import List, Dict, Optional, Tuple, Set, Any
from datetime import datetime
from collections import defaultdict

from config.settings import get_config
from core.models import TeamMember
from core.constants import UserRole, Department
from core.exceptions import ValidationError, DataIntegrityError
from data.data_manager import DataManager
from data.indexing import IndexManager
from utils.logger import get_logger

logger = get_logger(__name__)


class TeamManager:
    """Manages team-related business operations"""

    def __init__(self, data_manager: DataManager, index_manager: Optional[IndexManager] = None):
        self.config = get_config()
        self.data_manager = data_manager
        self.index_manager = index_manager
        self._user_permissions_cache = {}

    def get_department_statistics(self) -> Dict[str, Any]:
        """Get comprehensive team statistics"""
        try:
            members = self.data_manager.load_team_members()

            stats = {
                'total_members': len(members),
                'active_members': sum(1 for m in members if m.active),
                'managers_count': sum(1 for m in members if 'manager' in m.role.lower()),
                'by_department': {}
            }

            # Department breakdown
            dept_stats = {}
            for member in members:
                dept = member.department
                if dept not in dept_stats:
                    dept_stats[dept] = {'count': 0, 'managers': 0}

                dept_stats[dept]['count'] += 1
                if 'manager' in member.role.lower():
                    dept_stats[dept]['managers'] += 1

            stats['by_department'] = dept_stats
            return stats

        except Exception as e:
            logger.error(f"Error getting team statistics: {e}")
            return {
                'total_members': 0,
                'active_members': 0,
                'managers_count': 0,
                'by_department': {}
            }

    def get_active_team_members(self) -> List[TeamMember]:
        """Get list of active team members"""
        try:
            members = self.data_manager.load_team_members()
            return [m for m in members if m.active]
        except Exception as e:
            logger.error(f"Error getting active team members: {e}")
            return []

    def create_team_member(self, member_data: Dict, created_by: str) -> Tuple[bool, str, Optional[TeamMember]]:
        """Create new team member with validation"""
        try:
            # Check permissions
            if not self._check_permission(created_by, 'manage_team'):
                raise ValidationError("You don't have permission to manage team members")

            # Validate data
            self._validate_member_data(member_data)

            # Check for duplicates
            existing_members = self.data_manager.load_team_members()
            if any(m.name.lower() == member_data['name'].lower() for m in existing_members):
                raise DataIntegrityError(
                    f"Team member already exists: {member_data['name']}",
                    table="team",
                    record_key=member_data['name'],
                    issue_type="duplicate_name"
                )

            # Check email uniqueness
            if any(m.email.lower() == member_data['email'].lower() for m in existing_members):
                raise DataIntegrityError(
                    f"Email already in use: {member_data['email']}",
                    table="team",
                    record_key=member_data['email'],
                    issue_type="duplicate_email"
                )

            # Create team member
            new_member = TeamMember(
                name=member_data['name'],
                email=member_data['email'],
                department=member_data.get('department', 'General'),
                role=member_data.get('role', UserRole.TEAM_MEMBER.value),
                manager=member_data.get('manager', ''),
                active=member_data.get('active', True),
                permissions=self._get_default_permissions(member_data.get('role', UserRole.TEAM_MEMBER.value)),
                created_date=datetime.now().strftime('%Y-%m-%d'),
                created_by=created_by
            )

            # Add to list and save
            existing_members.append(new_member)
            success = self.data_manager.save_team_members(existing_members)

            if success:
                # Update search index
                if self.index_manager:
                    self.index_manager.index_team_member(new_member)

                return True, "Team member created successfully", new_member
            else:
                return False, "Failed to save team member", None

        except ValidationError as e:
            return False, str(e), None
        except DataIntegrityError as e:
            return False, str(e), None
        except Exception as e:
            logger.error(f"Error creating team member: {e}")
            return False, f"Error creating team member: {str(e)}", None

    def _validate_member_data(self, data: Dict):
        """Validate team member data"""
        required_fields = ['name', 'email']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Missing required field: {field}")

        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data['email']):
            raise ValidationError("Invalid email format")

    def _check_permission(self, user: str, permission: str) -> bool:
        """Check if user has permission"""
        # TODO: Implement proper permission checking
        return True

    def _get_default_permissions(self, role: str) -> List[str]:
        """Get default permissions for role"""
        return UserRole.get_capabilities(role)