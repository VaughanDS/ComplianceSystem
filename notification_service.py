# services/notification_service.py
"""
Notification service for in-app and system notifications
Manages user notifications and alerts
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
import json
import threading
import time

from config.settings import get_config
from core.constants import NotificationType, Priority
from utils.logger import get_logger

logger = get_logger(__name__)


class NotificationService:
    """Handles in-app notifications and alerts"""

    def __init__(self):
        self.config = get_config()

        # In-memory notification storage (in production, use a database)
        self._notifications = defaultdict(list)
        self._notification_counter = 0
        self._lock = threading.Lock()

        # Notification settings
        self._max_notifications_per_user = 100
        self._notification_retention_days = 30

    def show_notification(self, message: str, notification_type: str = "info",
                          duration: int = 5000, user: Optional[str] = None):
        """Show notification to user"""
        try:
            with self._lock:
                # Create notification object
                notification = {
                    'id': self._get_next_id(),
                    'message': message,
                    'type': notification_type,
                    'duration': duration,
                    'timestamp': datetime.now(),
                    'read': False,
                    'user': user or 'system'
                }

                # Store notification
                if user:
                    self._notifications[user].append(notification)
                    # Limit notifications per user
                    if len(self._notifications[user]) > self._max_notifications_per_user:
                        self._notifications[user] = self._notifications[user][-self._max_notifications_per_user:]
                else:
                    self._notifications['system'].append(notification)

                # Log notification
                logger.info(f"Notification shown: {message} ({notification_type})")

        except Exception as e:
            logger.error(f"Error showing notification: {e}")

    def create_task_notification(self, notification_type: NotificationType,
                                 task_data: Dict[str, Any], recipients: List[str]):
        """Create task-related notifications"""
        try:
            # Get notification template
            template = NotificationType.get_templates().get(notification_type.value, "{message}")

            # Format message
            message = template.format(
                task_title=task_data.get('task_title', 'Task'),
                due_date=task_data.get('target_date', ''),
                message=task_data.get('message', '')
            )

            # Determine notification level
            if notification_type in [NotificationType.TASK_OVERDUE, NotificationType.TASK_REJECTED]:
                notif_type = 'error'
            elif notification_type in [NotificationType.APPROVAL_NEEDED, NotificationType.REMINDER]:
                notif_type = 'warning'
            elif notification_type == NotificationType.TASK_COMPLETED:
                notif_type = 'success'
            else:
                notif_type = 'info'

            # Create notification for each recipient
            for recipient in recipients:
                self.show_notification(message, notif_type, user=recipient)

        except Exception as e:
            logger.error(f"Error creating task notification: {e}")

    def get_user_notifications(self, user: str, unread_only: bool = False) -> List[Dict]:
        """Get notifications for a specific user"""
        try:
            with self._lock:
                notifications = self._notifications.get(user, [])

                if unread_only:
                    notifications = [n for n in notifications if not n['read']]

                # Clean up old notifications
                cutoff_date = datetime.now() - timedelta(days=self._notification_retention_days)
                notifications = [n for n in notifications if n['timestamp'] > cutoff_date]

                # Update stored notifications
                self._notifications[user] = notifications

                return notifications.copy()

        except Exception as e:
            logger.error(f"Error getting user notifications: {e}")
            return []

    def mark_as_read(self, user: str, notification_id: int) -> bool:
        """Mark notification as read"""
        try:
            with self._lock:
                if user in self._notifications:
                    for notif in self._notifications[user]:
                        if notif['id'] == notification_id:
                            notif['read'] = True
                            return True
                return False

        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False

    def mark_all_as_read(self, user: str) -> int:
        """Mark all notifications as read for a user"""
        try:
            with self._lock:
                count = 0
                if user in self._notifications:
                    for notif in self._notifications[user]:
                        if not notif['read']:
                            notif['read'] = True
                            count += 1
                return count

        except Exception as e:
            logger.error(f"Error marking all notifications as read: {e}")
            return 0

    def clear_user_notifications(self, user: str) -> bool:
        """Clear all notifications for a user"""
        try:
            with self._lock:
                if user in self._notifications:
                    self._notifications[user] = []
                return True

        except Exception as e:
            logger.error(f"Error clearing user notifications: {e}")
            return False

    def get_notification_count(self, user: str, unread_only: bool = True) -> int:
        """Get notification count for a user"""
        try:
            notifications = self.get_user_notifications(user, unread_only)
            return len(notifications)

        except Exception as e:
            logger.error(f"Error getting notification count: {e}")
            return 0

    def create_reminder_notifications(self, reminder_tasks: List[Dict[str, Any]]):
        """Create reminder notifications for tasks"""
        try:
            for task_data in reminder_tasks:
                days_until_due = task_data.get('days_until_due', 0)

                # Determine message and type based on urgency
                if days_until_due < 0:
                    message = f"OVERDUE: {task_data['task_title']}"
                    notif_type = 'error'
                elif days_until_due == 0:
                    message = f"Due Today: {task_data['task_title']}"
                    notif_type = 'warning'
                elif days_until_due <= 3:
                    message = f"Due Soon: {task_data['task_title']} - {days_until_due} days remaining"
                    notif_type = 'warning'
                else:
                    message = f"Reminder: {task_data['task_title']} - Due in {days_until_due} days"
                    notif_type = 'info'

                # Create notifications for assigned users
                recipients = task_data.get('allocated_emails', [])
                if task_data.get('manager_email'):
                    recipients.append(task_data['manager_email'])

                for recipient in recipients:
                    self.show_notification(message, notif_type, user=recipient)

        except Exception as e:
            logger.error(f"Error creating reminder notifications: {e}")

    def export_notifications(self, user: str, format: str = 'json') -> Optional[str]:
        """Export user notifications"""
        try:
            notifications = self.get_user_notifications(user)

            if format == 'json':
                # Convert datetime objects to strings
                export_data = []
                for notif in notifications:
                    export_notif = notif.copy()
                    export_notif['timestamp'] = notif['timestamp'].isoformat()
                    export_data.append(export_notif)

                return json.dumps(export_data, indent=2)

            elif format == 'csv':
                import csv
                import io

                output = io.StringIO()
                writer = csv.DictWriter(
                    output,
                    fieldnames=['id', 'timestamp', 'type', 'message', 'read']
                )
                writer.writeheader()

                for notif in notifications:
                    writer.writerow({
                        'id': notif['id'],
                        'timestamp': notif['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                        'type': notif['type'],
                        'message': notif['message'],
                        'read': 'Yes' if notif['read'] else 'No'
                    })

                return output.getvalue()

            else:
                logger.error(f"Unsupported export format: {format}")
                return None

        except Exception as e:
            logger.error(f"Error exporting notifications: {e}")
            return None

    def _get_next_id(self) -> int:
        """Get next notification ID"""
        self._notification_counter += 1
        return self._notification_counter

    def cleanup_old_notifications(self):
        """Clean up old notifications for all users"""
        try:
            with self._lock:
                cutoff_date = datetime.now() - timedelta(days=self._notification_retention_days)

                for user in list(self._notifications.keys()):
                    # Filter out old notifications
                    self._notifications[user] = [
                        n for n in self._notifications[user]
                        if n['timestamp'] > cutoff_date
                    ]

                    # Remove user if no notifications left
                    if not self._notifications[user]:
                        del self._notifications[user]

                logger.info("Cleaned up old notifications")

        except Exception as e:
            logger.error(f"Error cleaning up notifications: {e}")


class NotificationScheduler:
    """Schedules and manages notification delivery"""

    def __init__(self, notification_service: NotificationService,
                 email_service=None, data_manager=None):
        self.notification_service = notification_service
        self.email_service = email_service
        self.data_manager = data_manager
        self.config = get_config()

        # Scheduler state
        self._running = False
        self._scheduler_thread = None
        self._check_interval = 3600  # Check every hour

    def start(self):
        """Start the notification scheduler"""
        if not self._running:
            self._running = True
            self._scheduler_thread = threading.Thread(target=self._run_scheduler)
            self._scheduler_thread.daemon = True
            self._scheduler_thread.start()
            logger.info("Notification scheduler started")

    def stop(self):
        """Stop the notification scheduler"""
        self._running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        logger.info("Notification scheduler stopped")

    def _run_scheduler(self):
        """Main scheduler loop"""
        while self._running:
            try:
                # Check and send reminders
                self.check_and_send_reminders()

                # Clean up old notifications
                self.notification_service.cleanup_old_notifications()

                # Process any queued notifications
                self.process_notification_queue()

                # Wait for next interval
                time.sleep(self._check_interval)

            except Exception as e:
                logger.error(f"Error in notification scheduler: {e}")
                time.sleep(60)  # Wait a minute before retrying

    def check_and_send_reminders(self):
        """Check for tasks needing reminders and send them"""
        try:
            if not self.data_manager:
                logger.warning("No data manager available for reminder check")
                return

            # Load tasks
            tasks = self.data_manager.load_tasks()

            # Find tasks needing reminders
            reminder_tasks = []
            today = datetime.now().date()

            for task in tasks:
                # Skip completed tasks
                if task.status in ['Resolved', 'Closed', 'Approved']:
                    continue

                # Check if task has a target date
                if not task.target_date:
                    continue

                try:
                    target_date = datetime.strptime(task.target_date, "%Y-%m-%d").date()
                    days_until_due = (target_date - today).days

                    # Check if reminder is needed
                    if days_until_due in self.config.task_reminder_days or days_until_due < 0:
                        task_data = {
                            'task_key': task.key,
                            'task_title': task.title,
                            'priority': task.priority,
                            'compliance_area': task.compliance_area,
                            'status': task.status,
                            'target_date': task.target_date,
                            'days_until_due': days_until_due,
                            'description': task.description,
                            'allocated_emails': task.allocated_emails,
                            'manager': task.manager,
                            'manager_email': task.manager_email
                        }
                        reminder_tasks.append(task_data)

                except ValueError:
                    logger.warning(f"Invalid target date for task {task.key}: {task.target_date}")
                    continue

            # Send reminders
            if reminder_tasks:
                # Create in-app notifications
                self.notification_service.create_reminder_notifications(reminder_tasks)

                # Send email reminders if available
                if self.email_service:
                    for task_data in reminder_tasks:
                        recipients = task_data.get('allocated_emails', [])
                        if task_data.get('manager_email'):
                            recipients.append(task_data['manager_email'])

                        if recipients:
                            self.email_service.send_reminder(task_data, recipients)

                logger.info(f"Sent reminders for {len(reminder_tasks)} tasks")

        except Exception as e:
            logger.error(f"Error checking and sending reminders: {e}")

    def process_notification_queue(self):
        """Process queued notifications from various sources"""
        try:
            # This would process notifications from:
            # 1. Task updates
            # 2. Approval requests
            # 3. System alerts
            # 4. User actions

            # For now, just log that we checked
            logger.debug("Processed notification queue")

        except Exception as e:
            logger.error(f"Error processing notification queue: {e}")

    def send_bulk_notification(self, message: str, recipients: List[str],
                               notification_type: str = 'info',
                               send_email: bool = False):
        """Send notification to multiple recipients"""
        try:
            # Create in-app notifications
            for recipient in recipients:
                self.notification_service.show_notification(
                    message, notification_type, user=recipient
                )

            # Send email if requested
            if send_email and self.email_service:
                subject = f"System Notification: {message[:50]}..."
                body = f"""
System Notification

{message}

This is an automated notification from the Compliance Management System.
"""
                self.email_service.send_email(
                    recipients, subject, body
                )

            logger.info(f"Sent bulk notification to {len(recipients)} recipients")

        except Exception as e:
            logger.error(f"Error sending bulk notification: {e}")

    def schedule_future_notification(self, message: str, recipient: str,
                                     scheduled_time: datetime,
                                     notification_type: str = 'info'):
        """Schedule a notification for future delivery"""
        # This would be implemented with a proper scheduling system
        # For now, just create it immediately
        self.notification_service.show_notification(
            message, notification_type, user=recipient
        )