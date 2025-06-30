# business/task_manager.py - Fixed with missing methods
"""
Task management business logic
Handles task operations and workflow management
"""

from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta

from config.settings import get_config
from core.models import Task
from core.constants import TaskStatus, Priority
from core.exceptions import ValidationError, DataIntegrityError
from data.data_manager import DataManager
from data.indexing import IndexManager
from utils.logger import get_logger

logger = get_logger(__name__)


class TaskManager:
    """Manages task-related business operations"""

    def __init__(self, data_manager: DataManager, index_manager: Optional[IndexManager] = None):
        self.config = get_config()
        self.data_manager = data_manager
        self.index_manager = index_manager

    def get_all_tasks(self) -> List[Task]:
        """Get all tasks"""
        try:
            return self.data_manager.load_tasks()
        except Exception as e:
            logger.error(f"Error getting all tasks: {e}")
            return []

    def get_tasks_for_user(self, user_email: str) -> List[Task]:
        """Get tasks assigned to or created by user"""
        try:
            all_tasks = self.data_manager.load_tasks()
            user_tasks = []

            for task in all_tasks:
                # Check if user is assigned or is the task setter
                if (user_email in task.allocated_emails or
                        task.task_setter_email == user_email or
                        task.manager_email == user_email):
                    user_tasks.append(task)

            return user_tasks
        except Exception as e:
            logger.error(f"Error getting tasks for user {user_email}: {e}")
            return []

    def create_task(self, task_data: Dict, created_by: str) -> Tuple[bool, str, Optional[Task]]:
        """Create new task with validation and email notification"""
        try:
            # Validate task data
            self._validate_task_data(task_data)

            # Generate task key
            task_key = self._generate_task_key(task_data['compliance_area'])

            # Create task object
            new_task = Task(
                key=task_key,
                title=task_data['title'],
                compliance_area=task_data['compliance_area'],
                subcategory=task_data.get('subcategory', 'Other'),
                task_setter=created_by,
                task_setter_email=task_data.get('task_setter_email', ''),
                allocated_to=task_data.get('allocated_to', []),
                allocated_emails=task_data.get('allocated_emails', []),
                manager=task_data.get('manager', ''),
                manager_email=task_data.get('manager_email', ''),
                priority=task_data.get('priority', Priority.MEDIUM.value),
                description=task_data['description'],
                status=TaskStatus.OPEN.value,
                date_logged=datetime.now().strftime('%Y-%m-%d'),
                target_date=task_data.get('target_date', ''),
                completed_date='',
                actions=[],
                attachments=[],
                approvals=[],
                tags=task_data.get('tags', []),
                custom_fields=task_data.get('custom_fields', {})
            )

            # Load existing tasks and add new one
            tasks = self.data_manager.load_tasks()
            tasks.append(new_task)

            # Save tasks
            success = self.data_manager.save_tasks(tasks)

            if success:
                # Update search index
                if self.index_manager:
                    self.index_manager.index_task(new_task)

                # Send email notifications
                try:
                    from services.email_service import EmailService
                    from core.constants import NotificationType

                    email_service = EmailService()

                    # Prepare task data for email
                    email_task_data = {
                        'task_key': new_task.key,
                        'task_title': new_task.title,
                        'priority': new_task.priority,
                        'compliance_area': new_task.compliance_area,
                        'target_date': new_task.target_date,
                        'description': new_task.description,
                        'task_setter': created_by
                    }

                    # Send to all assigned team members
                    if new_task.allocated_emails:
                        email_service.send_task_notification(
                            NotificationType.TASK_CREATED,
                            email_task_data,
                            new_task.allocated_emails
                        )
                        logger.info(f"Sent task creation emails to: {', '.join(new_task.allocated_emails)}")

                    # Also send to manager if specified
                    if new_task.manager_email and new_task.manager_email not in new_task.allocated_emails:
                        email_service.send_task_notification(
                            NotificationType.TASK_CREATED,
                            email_task_data,
                            new_task.manager_email
                        )
                        logger.info(f"Sent task creation email to manager: {new_task.manager_email}")

                except Exception as e:
                    # Don't fail task creation if email fails
                    logger.error(f"Failed to send email notification: {e}")

                return True, "Task created successfully", new_task
            else:
                return False, "Failed to save task", None

        except ValidationError as e:
            return False, str(e), None
        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return False, f"Error creating task: {str(e)}", None

    def _validate_task_data(self, data: Dict):
        """Validate task data"""
        required_fields = ['title', 'compliance_area', 'description']
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Missing required field: {field}")

    def _generate_task_key(self, compliance_area: str) -> str:
        """Generate unique task key"""
        # Get area prefix
        area_prefixes = {
            "IT Security & Data Protection": "IT",
            "Product Liability & Traceability": "PL",
            "Restricted Practices & Trade": "RP",
            "Legal & Contractual": "LC",
            "Environmental & Sustainability": "ES",
            "Health & Safety": "HS",
            "Data Protection": "DP",
            "Financial": "FN",
            "Operational": "OP"
        }

        prefix = area_prefixes.get(compliance_area, "GN")

        # Get next number
        tasks = self.data_manager.load_tasks()
        area_tasks = [t for t in tasks if t.key.startswith(prefix)]

        if area_tasks:
            # Extract numbers and find max
            numbers = []
            for task in area_tasks:
                try:
                    num = int(task.key.split('-')[1])
                    numbers.append(num)
                except:
                    pass
            next_num = max(numbers) + 1 if numbers else 1
        else:
            next_num = 1

        return f"{prefix}-{next_num:04d}"