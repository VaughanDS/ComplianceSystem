# services/email_service.py
"""
Email service for sending notifications with attachments
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from config.settings import get_config
from utils.logger import get_logger

logger = get_logger(__name__)


class EmailService:
    """Email service with file attachment support"""

    def __init__(self):
        self.config = get_config()
        self.smtp_server = getattr(self.config, 'smtp_server', 'smtp.office365.com')
        self.smtp_port = getattr(self.config, 'smtp_port', 587)
        self.smtp_username = getattr(self.config, 'smtp_username', '')
        self.smtp_password = getattr(self.config, 'smtp_password', '')
        self.from_email = getattr(self.config, 'notification_email', '')
        self.enabled = getattr(self.config, 'enable_notifications', True)

    def send_email(self, recipients: List[str], subject: str, body: str,
                   attachments: Optional[List[str]] = None) -> bool:
        """Send email with optional attachments"""
        if not self.enabled:
            logger.info("Email notifications are disabled")
            return True

        if not self.from_email or not self.smtp_username:
            logger.warning("Email not configured")
            return False

        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"Compliance Manager <{self.from_email}>"
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')

            # Add body
            msg.attach(MIMEText(body, 'plain'))

            # Add attachments if any
            if attachments:
                for file_path in attachments:
                    if os.path.isfile(file_path):
                        self._attach_file(msg, file_path)
                    else:
                        logger.warning(f"Attachment not found: {file_path}")

            # Create SSL context
            context = ssl.create_default_context()

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to: {', '.join(recipients)}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def _attach_file(self, msg: MIMEMultipart, file_path: str):
        """Attach a file to email"""
        try:
            # Open file in binary mode
            with open(file_path, 'rb') as file:
                # Create MIMEBase instance
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(file.read())

            # Encode file
            encoders.encode_base64(part)

            # Add header
            filename = os.path.basename(file_path)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )

            # Add attachment to message
            msg.attach(part)
            logger.debug(f"Attached file: {filename}")

        except Exception as e:
            logger.error(f"Failed to attach file {file_path}: {e}")

    def send_task_notification(self, task_data: Dict[str, Any],
                               notification_type: str = 'created',
                               include_attachments: bool = True) -> bool:
        """Send task-related notification"""
        try:
            # Determine recipients and subject based on notification type
            if notification_type == 'created':
                recipients = task_data.get('allocated_emails', [])
                if isinstance(recipients, str):
                    recipients = [e.strip() for e in recipients.split(',') if e.strip()]

                subject = f"New Task Assigned: {task_data.get('key', 'Unknown')} - {task_data.get('title', 'Untitled')}"
                body = self._get_task_created_body(task_data)

            elif notification_type == 'updated':
                # Get all stakeholders
                recipients = []
                if 'allocated_emails' in task_data:
                    if isinstance(task_data['allocated_emails'], list):
                        recipients.extend(task_data['allocated_emails'])
                    else:
                        recipients.extend([e.strip() for e in task_data['allocated_emails'].split(',')])

                if 'created_by_email' in task_data:
                    recipients.append(task_data['created_by_email'])

                if 'manager_email' in task_data and task_data['manager_email']:
                    recipients.append(task_data['manager_email'])

                # Remove duplicates
                recipients = list(set(recipients))

                subject = f"Task Updated: {task_data.get('key', 'Unknown')} - {task_data.get('title', 'Untitled')}"
                body = self._get_task_updated_body(task_data)

            else:
                logger.warning(f"Unknown notification type: {notification_type}")
                return False

            if not recipients:
                logger.warning("No recipients for task notification")
                return False

            # Get attachments if requested
            attachments = []
            if include_attachments and 'file_attachments' in task_data:
                attachments = task_data['file_attachments']

            # Send email
            return self.send_email(recipients, subject, body, attachments)

        except Exception as e:
            logger.error(f"Error sending task notification: {e}")
            return False

    def _get_task_created_body(self, task_data: Dict[str, Any]) -> str:
        """Get email body for task creation"""
        return f"""You have been assigned a new compliance task.

Task Details:
-------------
Task ID: {task_data.get('key', 'Unknown')}
Title: {task_data.get('title', 'Untitled')}
Priority: {task_data.get('priority', 'Medium')}
Status: {task_data.get('status', 'Open')}
Compliance Area: {task_data.get('compliance_area', 'Unknown')}
Target Date: {task_data.get('target_date', 'Not set')}

Description:
{task_data.get('description', 'No description provided')}

Assigned Team Members:
{', '.join(task_data.get('allocated_to', [])) if isinstance(task_data.get('allocated_to'), list) else task_data.get('allocated_to', 'None')}

Created By: {task_data.get('created_by', 'Unknown')}
Created Date: {task_data.get('created_date', datetime.now().strftime('%Y-%m-%d'))}

Please log into the Compliance Management System to view and update this task.

---
This is an automated notification from the Compliance Management System.
"""

    def _get_task_updated_body(self, task_data: Dict[str, Any]) -> str:
        """Get email body for task update"""
        updates = task_data.get('updates', {})
        updated_by = task_data.get('updated_by', 'Unknown')

        body = f"""Task {task_data.get('key', 'Unknown')} has been updated.

Task: {task_data.get('title', 'Untitled')}
Updated By: {updated_by}
Update Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Changes Made:
-------------
"""

        # Detail the changes
        if 'status' in updates:
            body += f"Status changed to: {updates['status']}\n"

        if 'progress' in updates:
            body += f"Progress updated to: {updates['progress']}%\n"

        if 'actions_taken' in updates:
            body += f"\nNew Actions Taken:\n{updates['actions_taken']}\n"

        if 'team_changes' in updates:
            changes = updates['team_changes']
            if changes.get('added'):
                body += f"\nTeam Members Added: {', '.join([m[0] for m in changes['added']])}\n"
            if changes.get('removed'):
                body += f"Team Members Removed: {', '.join([m[0] for m in changes['removed']])}\n"

        if 'new_files' in updates:
            body += f"\nNew Files Attached: {len(updates['new_files'])} file(s)\n"

        body += f"""
Current Task Details:
--------------------
Status: {task_data.get('status', 'Unknown')}
Priority: {task_data.get('priority', 'Medium')}
Progress: {task_data.get('progress', 0)}%
Target Date: {task_data.get('target_date', 'Not set')}

Please log into the Compliance Management System to view full details.

---
This is an automated notification from the Compliance Management System.
"""
        return body

    def send_reminder(self, task_data: Dict[str, Any], recipients: List[str]) -> bool:
        """Send task reminder"""
        try:
            days = task_data.get('days_until_due', 0)

            if days < 0:
                subject = f"OVERDUE: Task {task_data['task_key']} - {task_data['task_title']}"
                urgency = f"This task is {abs(days)} days overdue!"
            elif days == 0:
                subject = f"DUE TODAY: Task {task_data['task_key']} - {task_data['task_title']}"
                urgency = "This task is due today!"
            else:
                subject = f"Reminder: Task {task_data['task_key']} due in {days} days"
                urgency = f"This task is due in {days} days."

            body = f"""Task Reminder

{urgency}

Task Details:
-------------
Task ID: {task_data['task_key']}
Title: {task_data['task_title']}
Priority: {task_data.get('priority', 'Medium')}
Status: {task_data.get('status', 'Open')}
Target Date: {task_data['target_date']}

Please log into the Compliance Management System to view and update this task.

---
This is an automated reminder from the Compliance Management System.
"""

            return self.send_email(recipients, subject, body)

        except Exception as e:
            logger.error(f"Error sending reminder: {e}")
            return False

    def test_email_configuration(self) -> bool:
        """Test email configuration"""
        try:
            test_recipient = self.from_email
            subject = "Compliance Manager - Email Test"
            body = """This is a test email from the Compliance Management System.

If you received this email, your email configuration is working correctly.

Configuration Details:
SMTP Server: {}
SMTP Port: {}
From Email: {}

---
This is an automated test email.
""".format(self.smtp_server, self.smtp_port, self.from_email)

            return self.send_email([test_recipient], subject, body)

        except Exception as e:
            logger.error(f"Email test failed: {e}")
            return False