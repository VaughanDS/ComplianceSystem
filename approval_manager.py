# business/approval_manager.py
"""
Approval workflow management
Handles task approvals, escalations, and delegation
"""

from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta

from config.settings import get_config
from core.models import Task, TeamMember, ApprovalRecord
from core.constants import TaskStatus, ApprovalStatus, NotificationType
from core.exceptions import ApprovalError, ValidationError
from data.data_manager import DataManager
from utils.logger import get_logger

logger = get_logger(__name__)


class ApprovalManager:
    """Manages approval workflows and processes"""

    def __init__(self, data_manager: DataManager):
        self.config = get_config()
        self.data_manager = data_manager
        self._approval_rules = self._load_approval_rules()

    def _load_approval_rules(self) -> Dict[str, Any]:
        """Load approval rules from configuration"""
        return {
            'auto_escalate_after_hours': 48,
            'max_approval_levels': 3,
            'require_comment_on_rejection': True,
            'allow_delegation': True,
            'approval_thresholds': {
                'Critical': 1,  # Days before escalation
                'High': 2,
                'Medium': 5,
                'Low': 7
            }
        }

    def submit_for_approval(self, task_key: str, submitted_by: str,
                            manager_email: Optional[str] = None,
                            comments: str = '') -> Tuple[bool, str]:
        """Submit task for approval"""
        try:
            # Load task
            task = self.data_manager.get_task(task_key)
            if not task:
                raise ValidationError(f"Task not found: {task_key}")

            # Validate submission
            if task.status not in [TaskStatus.OPEN.value, TaskStatus.IN_PROGRESS.value]:
                raise ApprovalError(
                    f"Task cannot be submitted for approval in status: {task.status}",
                    task_key=task_key,
                    current_status=task.status
                )

            # Determine approver
            if not manager_email:
                manager_email = task.manager_email

            if not manager_email:
                # Find manager for submitter
                members = self.data_manager.load_team_members()
                submitter = next((m for m in members if m.email == submitted_by), None)

                if submitter and submitter.manager:
                    manager = next((m for m in members if m.name == submitter.manager), None)
                    if manager:
                        manager_email = manager.email

            if not manager_email:
                raise ApprovalError(
                    "No manager specified for approval",
                    task_key=task_key
                )

            # Create approval record
            approval = ApprovalRecord(
                task_key=task_key,
                submitted_by=submitted_by,
                submitted_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                approver=manager_email,
                status=ApprovalStatus.PENDING.value,
                level=1,
                comments=comments
            )

            # Update task
            task.status = TaskStatus.PENDING_APPROVAL.value
            task.approval_records.append(approval)
            task.add_action(
                submitted_by,
                'submitted_for_approval',
                f'Submitted to {manager_email} for approval'
            )

            # Save task
            success = self.data_manager.save_task(task)

            if success:
                logger.info(f"Task {task_key} submitted for approval by {submitted_by}")
                return True, f"Task submitted for approval to {manager_email}"
            else:
                return False, "Failed to save task"

        except ApprovalError as e:
            logger.warning(f"Approval error: {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"Error submitting task for approval: {e}")
            return False, f"Error: {str(e)}"

    def approve_task(self, task_key: str, approver_email: str,
                     comments: str = '') -> Tuple[bool, str]:
        """Approve a task"""
        try:
            # Load task
            task = self.data_manager.get_task(task_key)
            if not task:
                raise ValidationError(f"Task not found: {task_key}")

            # Find pending approval
            pending_approval = None
            for approval in task.approval_records:
                if (approval.status == ApprovalStatus.PENDING.value and
                        approval.approver == approver_email):
                    pending_approval = approval
                    break

            if not pending_approval:
                raise ApprovalError(
                    f"No pending approval found for {approver_email}",
                    task_key=task_key
                )

            # Update approval record
            pending_approval.status = ApprovalStatus.APPROVED.value
            pending_approval.approval_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            pending_approval.comments = comments

            # Update task status
            task.status = TaskStatus.APPROVED.value
            task.add_action(
                approver_email,
                'approved',
                f'Task approved{" - " + comments if comments else ""}'
            )

            # Save task
            success = self.data_manager.save_task(task)

            if success:
                logger.info(f"Task {task_key} approved by {approver_email}")
                return True, "Task approved successfully"
            else:
                return False, "Failed to save task"

        except Exception as e:
            logger.error(f"Error approving task: {e}")
            return False, f"Error: {str(e)}"

    def reject_task(self, task_key: str, approver_email: str,
                    reason: str) -> Tuple[bool, str]:
        """Reject a task"""
        try:
            # Load task
            task = self.data_manager.get_task(task_key)
            if not task:
                raise ValidationError(f"Task not found: {task_key}")

            # Validate reason
            if self._approval_rules['require_comment_on_rejection'] and not reason:
                raise ValidationError("Rejection reason is required")

            # Find pending approval
            pending_approval = None
            for approval in task.approval_records:
                if (approval.status == ApprovalStatus.PENDING.value and
                        approval.approver == approver_email):
                    pending_approval = approval
                    break

            if not pending_approval:
                raise ApprovalError(
                    f"No pending approval found for {approver_email}",
                    task_key=task_key
                )

            # Update approval record
            pending_approval.status = ApprovalStatus.REJECTED.value
            pending_approval.approval_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            pending_approval.comments = reason

            # Update task status
            task.status = TaskStatus.OPEN.value
            task.add_action(
                approver_email,
                'rejected',
                f'Task rejected - {reason}'
            )

            # Save task
            success = self.data_manager.save_task(task)

            if success:
                logger.info(f"Task {task_key} rejected by {approver_email}")
                return True, "Task rejected successfully"
            else:
                return False, "Failed to save task"

        except Exception as e:
            logger.error(f"Error rejecting task: {e}")
            return False, f"Error: {str(e)}"

    def escalate_approval(self, task_key: str, escalated_by: str,
                          reason: str = '') -> Tuple[bool, str]:
        """Escalate approval to next level"""
        try:
            # Load task
            task = self.data_manager.get_task(task_key)
            if not task:
                raise ValidationError(f"Task not found: {task_key}")

            # Get current approval
            current_approval = None
            for approval in task.approval_records:
                if approval.status == ApprovalStatus.PENDING.value:
                    current_approval = approval
                    break

            if not current_approval:
                raise ApprovalError("No pending approval to escalate", task_key=task_key)

            # Check escalation level
            if current_approval.level >= self._approval_rules['max_approval_levels']:
                raise ApprovalError(
                    f"Maximum approval level ({self._approval_rules['max_approval_levels']}) reached",
                    task_key=task_key
                )

            # Find supervisor
            supervisor = self._find_supervisor(current_approval.approver)
            if not supervisor:
                raise ApprovalError(
                    "No supervisor found for escalation",
                    task_key=task_key
                )

            # Update current approval
            current_approval.status = ApprovalStatus.CONDITIONAL.value
            current_approval.comments = f"Escalated by {escalated_by} - {reason}"

            # Create new approval record
            new_approval = ApprovalRecord(
                task_key=task_key,
                submitted_by=escalated_by,
                submitted_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                approver=supervisor.email,
                status=ApprovalStatus.PENDING.value,
                level=current_approval.level + 1,
                comments=f"Escalated from {current_approval.approver}"
            )

            task.approval_records.append(new_approval)
            task.add_action(
                escalated_by,
                'escalated',
                f'Escalated to {supervisor.name} - {reason}'
            )

            # Save task
            success = self.data_manager.save_task(task)

            if success:
                logger.info(f"Task {task_key} escalated to {supervisor.email}")
                return True, f"Task escalated to {supervisor.name}"
            else:
                return False, "Failed to save task"

        except Exception as e:
            logger.error(f"Error escalating approval: {e}")
            return False, f"Error: {str(e)}"

    def delegate_approval(self, task_key: str, from_email: str,
                          to_email: str, reason: str = '') -> Tuple[bool, str]:
        """Delegate approval to another manager"""
        try:
            if not self._approval_rules['allow_delegation']:
                raise ApprovalError("Delegation is not allowed", task_key=task_key)

            # Load task
            task = self.data_manager.get_task(task_key)
            if not task:
                raise ValidationError(f"Task not found: {task_key}")

            # Find approval to delegate
            approval_to_delegate = None
            for approval in task.approval_records:
                if (approval.status == ApprovalStatus.PENDING.value and
                        approval.approver == from_email):
                    approval_to_delegate = approval
                    break

            if not approval_to_delegate:
                raise ApprovalError(
                    f"No pending approval found for {from_email}",
                    task_key=task_key
                )

            # Verify delegate is a manager
            members = self.data_manager.load_team_members()
            delegate = next((m for m in members if m.email == to_email), None)

            if not delegate:
                raise ValidationError(f"Delegate not found: {to_email}")

            if not self._is_manager(delegate):
                raise ApprovalError(
                    f"{delegate.name} is not authorized to approve tasks",
                    task_key=task_key
                )

            # Update approval
            approval_to_delegate.approver = to_email
            approval_to_delegate.comments = f"Delegated from {from_email} - {reason}"

            task.add_action(
                from_email,
                'delegated',
                f'Delegated to {delegate.name} - {reason}'
            )

            # Save task
            success = self.data_manager.save_task(task)

            if success:
                logger.info(f"Task {task_key} delegated from {from_email} to {to_email}")
                return True, f"Task delegated to {delegate.name}"
            else:
                return False, "Failed to save task"

        except Exception as e:
            logger.error(f"Error delegating approval: {e}")
            return False, f"Error: {str(e)}"

    def get_pending_approvals(self, manager_email: str) -> List[Task]:
        """Get all pending approvals for a manager"""
        try:
            tasks = self.data_manager.load_tasks()
            pending_tasks = []

            for task in tasks:
                for approval in task.approval_records:
                    if (approval.status == ApprovalStatus.PENDING.value and
                            approval.approver == manager_email):
                        pending_tasks.append(task)
                        break

            return pending_tasks

        except Exception as e:
            logger.error(f"Error getting pending approvals: {e}")
            return []

    def check_approval_timeouts(self) -> List[Tuple[Task, int]]:
        """Check for approvals that have timed out"""
        try:
            tasks = self.data_manager.load_tasks()
            timed_out = []

            for task in tasks:
                for approval in task.approval_records:
                    if approval.status == ApprovalStatus.PENDING.value:
                        # Calculate hours since submission
                        submitted = datetime.strptime(
                            approval.submitted_date,
                            "%Y-%m-%d %H:%M:%S"
                        )
                        hours_pending = (datetime.now() - submitted).total_seconds() / 3600

                        # Check threshold based on priority
                        threshold = self._approval_rules['approval_thresholds'].get(
                            task.priority,
                            self._approval_rules['auto_escalate_after_hours']
                        ) * 24  # Convert days to hours

                        if hours_pending > threshold:
                            timed_out.append((task, int(hours_pending)))

            return timed_out

        except Exception as e:
            logger.error(f"Error checking approval timeouts: {e}")
            return []

    def auto_escalate_timeouts(self) -> Tuple[int, List[str]]:
        """Automatically escalate timed out approvals"""
        escalated = 0
        errors = []

        try:
            timed_out = self.check_approval_timeouts()

            for task, hours in timed_out:
                success, message = self.escalate_approval(
                    task.key,
                    'System',
                    f'Auto-escalated after {hours} hours'
                )

                if success:
                    escalated += 1
                else:
                    errors.append(f"{task.key}: {message}")

        except Exception as e:
            logger.error(f"Error in auto-escalation: {e}")
            errors.append(str(e))

        return escalated, errors

    def get_approval_metrics(self, date_from: Optional[str] = None,
                             date_to: Optional[str] = None) -> Dict[str, Any]:
        """Get approval metrics"""
        try:
            tasks = self.data_manager.load_tasks()

            # Filter by date if specified
            if date_from:
                tasks = [t for t in tasks if t.created_date >= date_from]
            if date_to:
                tasks = [t for t in tasks if t.created_date <= date_to]

            metrics = {
                'total_approvals': 0,
                'approved': 0,
                'rejected': 0,
                'pending': 0,
                'escalations': 0,
                'delegations': 0,
                'average_approval_time_hours': 0,
                'by_manager': {},
                'by_compliance_area': {}
            }

            approval_times = []

            for task in tasks:
                if not task.approval_records:
                    continue

                metrics['total_approvals'] += len(task.approval_records)

                for approval in task.approval_records:
                    # Count by status
                    if approval.status == ApprovalStatus.APPROVED.value:
                        metrics['approved'] += 1

                        # Calculate approval time
                        if approval.approval_date:
                            submitted = datetime.strptime(
                                approval.submitted_date,
                                "%Y-%m-%d %H:%M:%S"
                            )
                            approved = datetime.strptime(
                                approval.approval_date,
                                "%Y-%m-%d %H:%M:%S"
                            )
                            hours = (approved - submitted).total_seconds() / 3600
                            approval_times.append(hours)

                    elif approval.status == ApprovalStatus.REJECTED.value:
                        metrics['rejected'] += 1
                    elif approval.status == ApprovalStatus.PENDING.value:
                        metrics['pending'] += 1

                    # Count by manager
                    manager = approval.approver
                    if manager not in metrics['by_manager']:
                        metrics['by_manager'][manager] = {
                            'total': 0,
                            'approved': 0,
                            'rejected': 0,
                            'pending': 0
                        }

                    metrics['by_manager'][manager]['total'] += 1

                    if approval.status == ApprovalStatus.APPROVED.value:
                        metrics['by_manager'][manager]['approved'] += 1
                    elif approval.status == ApprovalStatus.REJECTED.value:
                        metrics['by_manager'][manager]['rejected'] += 1
                    elif approval.status == ApprovalStatus.PENDING.value:
                        metrics['by_manager'][manager]['pending'] += 1

                # Count escalations and delegations
                for action in task.actions_taken:
                    if action.action == 'escalated':
                        metrics['escalations'] += 1
                    elif action.action == 'delegated':
                        metrics['delegations'] += 1

                # Count by compliance area
                if task.approval_records:
                    area = task.compliance_area
                    metrics['by_compliance_area'][area] = metrics['by_compliance_area'].get(area, 0) + 1

            # Calculate average approval time
            if approval_times:
                metrics['average_approval_time_hours'] = round(
                    sum(approval_times) / len(approval_times), 1
                )

            return metrics

        except Exception as e:
            logger.error(f"Error getting approval metrics: {e}")
            return {}

    def _find_supervisor(self, manager_email: str) -> Optional[TeamMember]:
        """Find supervisor for a manager"""
        members = self.data_manager.load_team_members()

        # Find the manager
        manager = next((m for m in members if m.email == manager_email), None)
        if not manager:
            return None

        # Find their supervisor
        if manager.manager:
            supervisor = next((m for m in members if m.name == manager.manager), None)
            if supervisor and supervisor.active:
                return supervisor

        # If no direct supervisor, find department head or compliance manager
        dept_members = [m for m in members if m.department == manager.department]
        for member in dept_members:
            if 'head' in member.role.lower() or 'director' in member.role.lower():
                return member

        # Fall back to compliance manager
        for member in members:
            if member.department == 'Compliance' and 'manager' in member.role.lower():
                return member

        return None

    def _is_manager(self, member: TeamMember) -> bool:
        """Check if team member is a manager"""
        manager_keywords = ['manager', 'head', 'director', 'lead', 'supervisor']
        return any(keyword in member.role.lower() for keyword in manager_keywords)