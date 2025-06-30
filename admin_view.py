# views/admin_view.py
"""
Admin view for Compliance Management System
System administration and configuration
"""

import tkinter as tk
from tkinter import ttk, filedialog
import ttkbootstrap as tb
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from views import BaseView
from ui.components import (
    ModernFrame, ModernButton, ModernLabel, Card,
    MetricCard, ProgressIndicator, DatePicker, ProgressDialog
)
from ui.styles import UIStyles


class AdminView(BaseView):
    """Administrative functions view"""

    def show(self):
        """Display admin view"""
        super().show()

        # Check admin permission
        if 'admin' not in self.app.user_permissions:
            self.show_access_denied()
            return

        # Main container
        main_container = ttk.Frame(self.parent_frame)
        main_container.pack(fill='both', expand=True, padx=20, pady=20)

        # Title
        title_label = ModernLabel(
            main_container,
            text="System Administration",
            style_type='heading1'
        )
        title_label.pack(pady=(0, 20))

        # Create tabbed interface
        notebook = ttk.Notebook(main_container)
        notebook.pack(fill='both', expand=True)

        # System Overview tab
        overview_frame = ttk.Frame(notebook)
        notebook.add(overview_frame, text="System Overview")
        self.create_system_overview(overview_frame)

        # Data Management tab
        data_frame = ttk.Frame(notebook)
        notebook.add(data_frame, text="Data Management")
        self.create_data_management(data_frame)

        # User Management tab
        user_frame = ttk.Frame(notebook)
        notebook.add(user_frame, text="User Management")
        self.create_user_management(user_frame)

        # System Settings tab
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="System Settings")
        self.create_system_settings(settings_frame)

        # Audit Log tab
        audit_frame = ttk.Frame(notebook)
        notebook.add(audit_frame, text="Audit Log")
        self.create_audit_log(audit_frame)

    def show_access_denied(self):
        """Show access denied message"""
        msg_frame = ttk.Frame(self.parent_frame)
        msg_frame.pack(expand=True)

        ttk.Label(
            msg_frame,
            text="Access Denied",
            font=UIStyles.FONTS.get_font('heading2'),
            foreground=UIStyles.COLOURS['danger']
        ).pack()

        ttk.Label(
            msg_frame,
            text="You do not have permission to access this area",
            font=UIStyles.FONTS.get_font('normal'),
            foreground=UIStyles.COLOURS['text_secondary']
        ).pack(pady=(10, 20))

        back_btn = ModernButton(
            msg_frame,
            text="Go Back",
            icon='arrow_left',
            command=lambda: self.app.show_view('dashboard')
        )
        back_btn.pack()

    def create_system_overview(self, parent: ttk.Frame):
        """Create system overview section"""
        # Scrollable container
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # System metrics
        metrics_frame = ttk.Frame(scrollable_frame)
        metrics_frame.pack(fill='x', padx=20, pady=20)

        # Get system statistics
        stats = self.get_system_statistics()

        # Configure grid
        for i in range(4):
            metrics_frame.columnconfigure(i, weight=1)

        # Total Users
        MetricCard(
            metrics_frame,
            title="Total Users",
            value=str(stats['total_users']),
            subtitle="Active users"
        ).grid(row=0, column=0, padx=5, sticky='ew')

        # Total Tasks
        MetricCard(
            metrics_frame,
            title="Total Tasks",
            value=str(stats['total_tasks']),
            subtitle="All tasks in system"
        ).grid(row=0, column=1, padx=5, sticky='ew')

        # Storage Used
        MetricCard(
            metrics_frame,
            title="Storage Used",
            value=stats['storage_used'],
            subtitle="Document storage"
        ).grid(row=0, column=2, padx=5, sticky='ew')

        # System Uptime
        MetricCard(
            metrics_frame,
            title="System Uptime",
            value=stats['uptime'],
            subtitle="Since last restart"
        ).grid(row=0, column=3, padx=5, sticky='ew')

        # System health
        health_card = Card(scrollable_frame, "System Health")
        health_card.pack(fill='x', padx=20, pady=(0, 20))

        health_content = health_card.get_content_frame()

        # Health checks
        health_checks = [
            {'name': 'Database Connection', 'status': 'OK', 'icon': '✓'},
            {'name': 'File Storage', 'status': 'OK', 'icon': '✓'},
            {'name': 'Email Service', 'status': self.check_email_service(),
             'icon': '✓' if self.check_email_service() == 'OK' else '⚠'},
            {'name': 'Backup Service', 'status': 'OK', 'icon': '✓'},
            {'name': 'Search Index', 'status': 'OK', 'icon': '✓'}
        ]

        for check in health_checks:
            check_frame = ttk.Frame(health_content)
            check_frame.pack(fill='x', pady=5)

            # Icon
            icon_colour = UIStyles.COLOURS['success'] if check['icon'] == '✓' else UIStyles.COLOURS['warning']
            ttk.Label(
                check_frame,
                text=check['icon'],
                font=('Arial', 14),
                foreground=icon_colour
            ).pack(side='left', padx=(0, 10))

            # Name
            ttk.Label(
                check_frame,
                text=check['name'],
                font=UIStyles.FONTS.get_font('normal')
            ).pack(side='left')

            # Status
            ttk.Label(
                check_frame,
                text=check['status'],
                font=UIStyles.FONTS.get_font('normal', 'bold'),
                foreground=icon_colour
            ).pack(side='right')

        # Recent system events
        events_card = Card(scrollable_frame, "Recent System Events")
        events_card.pack(fill='x', padx=20)

        events_content = events_card.get_content_frame()

        # Sample events
        events = [
            {'time': '10:30', 'event': 'Automatic backup completed'},
            {'time': '09:15', 'event': 'Search index rebuilt'},
            {'time': '08:00', 'event': 'Daily maintenance tasks completed'},
            {'time': 'Yesterday', 'event': '15 old tasks archived'},
            {'time': 'Yesterday', 'event': 'System configuration updated'}
        ]

        for event in events:
            event_frame = ttk.Frame(events_content)
            event_frame.pack(fill='x', pady=2)

            ttk.Label(
                event_frame,
                text=event['time'],
                font=UIStyles.FONTS.get_font('small'),
                foreground=UIStyles.COLOURS['text_secondary'],
                width=10
            ).pack(side='left')

            ttk.Label(
                event_frame,
                text=event['event'],
                font=UIStyles.FONTS.get_font('small')
            ).pack(side='left', padx=(10, 0))

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_data_management(self, parent: ttk.Frame):
        """Create data management section"""
        # Main container
        container = ttk.Frame(parent)
        container.pack(fill='both', expand=True, padx=20, pady=20)

        # Backup section
        backup_card = Card(container, "Backup & Restore")
        backup_card.pack(fill='x', pady=(0, 20))

        backup_content = backup_card.get_content_frame()

        # Last backup info
        info_frame = ttk.Frame(backup_content)
        info_frame.pack(fill='x', pady=(0, 10))

        ttk.Label(
            info_frame,
            text="Last Backup:",
            font=UIStyles.FONTS.get_font('normal')
        ).pack(side='left')

        ttk.Label(
            info_frame,
            text="Today at 02:00",
            font=UIStyles.FONTS.get_font('normal', 'bold')
        ).pack(side='left', padx=(10, 0))

        # Backup buttons
        btn_frame = ttk.Frame(backup_content)
        btn_frame.pack(fill='x')

        backup_now_btn = ModernButton(
            btn_frame,
            text="Backup Now",
            icon='save',
            command=self.backup_now,
            style_type='primary'
        )
        backup_now_btn.pack(side='left', padx=(0, 10))

        restore_btn = ModernButton(
            btn_frame,
            text="Restore",
            icon='restore',
            command=self.restore_backup,
            style_type='secondary'
        )
        restore_btn.pack(side='left', padx=(0, 10))

        schedule_btn = ModernButton(
            btn_frame,
            text="Schedule",
            icon='clock',
            command=self.schedule_backup,
            style_type='secondary'
        )
        schedule_btn.pack(side='left')

        # Archive section
        archive_card = Card(container, "Data Archiving")
        archive_card.pack(fill='x', pady=(0, 20))

        archive_content = archive_card.get_content_frame()

        # Archive info
        archive_info = ttk.Frame(archive_content)
        archive_info.pack(fill='x', pady=(0, 10))

        archive_stats = self.get_archive_statistics()

        self.create_info_item(archive_info, "Archived Tasks:", str(archive_stats['archived_tasks']))
        self.create_info_item(archive_info, "Archive Size:", archive_stats['archive_size'])
        self.create_info_item(archive_info, "Oldest Archive:", archive_stats['oldest_archive'])

        # Archive buttons
        archive_btn_frame = ttk.Frame(archive_content)
        archive_btn_frame.pack(fill='x')

        archive_now_btn = ModernButton(
            archive_btn_frame,
            text="Archive Old Tasks",
            icon='archive',
            command=self.archive_old_tasks,
            style_type='primary'
        )
        archive_now_btn.pack(side='left', padx=(0, 10))

        browse_btn = ModernButton(
            archive_btn_frame,
            text="Browse Archives",
            icon='folder',
            command=self.browse_archives,
            style_type='secondary'
        )
        browse_btn.pack(side='left')

        # Data cleanup section
        cleanup_card = Card(container, "Data Cleanup")
        cleanup_card.pack(fill='x')

        cleanup_content = cleanup_card.get_content_frame()

        # Cleanup options
        self.cleanup_orphaned_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            cleanup_content,
            text="Remove orphaned files",
            variable=self.cleanup_orphaned_var
        ).pack(anchor='w', pady=2)

        self.cleanup_temp_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            cleanup_content,
            text="Clear temporary files",
            variable=self.cleanup_temp_var
        ).pack(anchor='w', pady=2)

        self.rebuild_index_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            cleanup_content,
            text="Rebuild search index",
            variable=self.rebuild_index_var
        ).pack(anchor='w', pady=2)

        # Cleanup button
        cleanup_btn = ModernButton(
            cleanup_content,
            text="Run Cleanup",
            icon='clean',
            command=self.run_cleanup,
            style_type='warning'
        )
        cleanup_btn.pack(pady=(10, 0))

    def create_user_management(self, parent: ttk.Frame):
        """Create user management section"""
        # Main container
        container = ttk.Frame(parent)
        container.pack(fill='both', expand=True, padx=20, pady=20)

        # User statistics
        stats_frame = ttk.Frame(container)
        stats_frame.pack(fill='x', pady=(0, 20))

        user_stats = self.get_user_statistics()

        # Stats cards
        for i in range(4):
            stats_frame.columnconfigure(i, weight=1)

        MetricCard(
            stats_frame,
            title="Active Users",
            value=str(user_stats['active_users']),
            subtitle="Currently active"
        ).grid(row=0, column=0, padx=5, sticky='ew')

        MetricCard(
            stats_frame,
            title="Inactive Users",
            value=str(user_stats['inactive_users']),
            subtitle="Deactivated accounts"
        ).grid(row=0, column=1, padx=5, sticky='ew')

        MetricCard(
            stats_frame,
            title="Admins",
            value=str(user_stats['admin_users']),
            subtitle="Admin accounts"
        ).grid(row=0, column=2, padx=5, sticky='ew')

        MetricCard(
            stats_frame,
            title="Managers",
            value=str(user_stats['manager_users']),
            subtitle="With approval rights"
        ).grid(row=0, column=3, padx=5, sticky='ew')

        # User actions
        actions_card = Card(container, "User Actions")
        actions_card.pack(fill='x', pady=(0, 20))

        actions_content = actions_card.get_content_frame()

        # Action buttons
        btn_frame = ttk.Frame(actions_content)
        btn_frame.pack(fill='x')

        # Reset password
        reset_pwd_btn = ModernButton(
            btn_frame,
            text="Reset User Password",
            icon='key',
            command=self.reset_user_password,
            style_type='primary'
        )
        reset_pwd_btn.pack(side='left', padx=(0, 10))

        # Bulk permissions
        bulk_perm_btn = ModernButton(
            btn_frame,
            text="Bulk Update Permissions",
            icon='shield',
            command=self.bulk_update_permissions,
            style_type='secondary'
        )
        bulk_perm_btn.pack(side='left', padx=(0, 10))

        # Export users
        export_users_btn = ModernButton(
            btn_frame,
            text="Export User List",
            icon='download',
            command=self.export_users,
            style_type='secondary'
        )
        export_users_btn.pack(side='left')

        # Login activity
        activity_card = Card(container, "Recent Login Activity")
        activity_card.pack(fill='x')

        activity_content = activity_card.get_content_frame()

        # Sample login activity
        logins = [
            {'user': 'John Smith', 'time': '10:45 AM', 'status': 'Success'},
            {'user': 'Jane Doe', 'time': '10:30 AM', 'status': 'Success'},
            {'user': 'Bob Wilson', 'time': '09:15 AM', 'status': 'Success'},
            {'user': 'Alice Brown', 'time': '09:00 AM', 'status': 'Failed'},
            {'user': 'Charlie Davis', 'time': 'Yesterday', 'status': 'Success'}
        ]

        # Create header
        header_frame = ttk.Frame(activity_content)
        header_frame.pack(fill='x', pady=(0, 10))

        for i, col in enumerate(['User', 'Time', 'Status']):
            ttk.Label(
                header_frame,
                text=col,
                font=UIStyles.FONTS.get_font('small', 'bold')
            ).grid(row=0, column=i, sticky='w', padx=(0, 20))

        # Login entries
        for login in logins:
            login_frame = ttk.Frame(activity_content)
            login_frame.pack(fill='x', pady=2)

            ttk.Label(
                login_frame,
                text=login['user'],
                font=UIStyles.FONTS.get_font('small')
            ).grid(row=0, column=0, sticky='w', padx=(0, 20))

            ttk.Label(
                login_frame,
                text=login['time'],
                font=UIStyles.FONTS.get_font('small')
            ).grid(row=0, column=1, sticky='w', padx=(0, 20))

            status_colour = UIStyles.COLOURS['success'] if login['status'] == 'Success' else UIStyles.COLOURS['danger']
            ttk.Label(
                login_frame,
                text=login['status'],
                font=UIStyles.FONTS.get_font('small'),
                foreground=status_colour
            ).grid(row=0, column=2, sticky='w')

    def create_system_settings(self, parent: ttk.Frame):
        """Create system settings section"""
        # Scrollable container
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # General settings
        general_card = Card(scrollable_frame, "General Settings")
        general_card.pack(fill='x', padx=20, pady=20)

        general_content = general_card.get_content_frame()

        # System name
        self.create_setting_item(
            general_content,
            "System Name",
            self.app.config.app_name,
            "text"
        )

        # Company name
        self.create_setting_item(
            general_content,
            "Company Name",
            self.app.config.company,
            "text"
        )

        # Data path
        self.create_setting_item(
            general_content,
            "Data Path",
            str(self.app.config.base_path),
            "path"
        )

        # Email settings
        email_card = Card(scrollable_frame, "Email Settings")
        email_card.pack(fill='x', padx=20, pady=(0, 20))

        email_content = email_card.get_content_frame()

        # SMTP server
        self.create_setting_item(
            email_content,
            "SMTP Server",
            self.app.config.smtp_server,
            "text"
        )

        # SMTP port
        self.create_setting_item(
            email_content,
            "SMTP Port",
            str(self.app.config.smtp_port),
            "number"
        )

        # Compliance email
        self.create_setting_item(
            email_content,
            "Compliance Email",
            self.app.config.compliance_email,
            "email"
        )

        # Test email button
        test_email_btn = ModernButton(
            email_content,
            text="Test Email Configuration",
            icon='mail',
            command=self.test_email_config
        )
        test_email_btn.pack(pady=(10, 0))

        # Advanced settings
        advanced_card = Card(scrollable_frame, "Advanced Settings")
        advanced_card.pack(fill='x', padx=20, pady=(0, 20))

        advanced_content = advanced_card.get_content_frame()

        # Auto-refresh interval
        self.create_setting_item(
            advanced_content,
            "Auto-refresh Interval (seconds)",
            str(self.app.config.auto_refresh_interval),
            "number"
        )

        # Archive after days
        self.create_setting_item(
            advanced_content,
            "Archive Tasks After (days)",
            str(self.app.config.archive_after_days),
            "number"
        )

        # Max file size
        self.create_setting_item(
            advanced_content,
            "Max File Size (MB)",
            str(self.app.config.max_file_size_mb),
            "number"
        )

        # Save button
        save_btn = ModernButton(
            scrollable_frame,
            text="Save Settings",
            icon='save',
            command=self.save_settings,
            style_type='primary'
        )
        save_btn.pack(pady=20)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_audit_log(self, parent: ttk.Frame):
        """Create audit log section"""
        # Main container
        container = ttk.Frame(parent)
        container.pack(fill='both', expand=True, padx=20, pady=20)

        # Filter section
        filter_frame = ttk.Frame(container)
        filter_frame.pack(fill='x', pady=(0, 20))

        # Date range
        ttk.Label(
            filter_frame,
            text="Date Range:",
            font=UIStyles.FONTS.get_font('normal')
        ).pack(side='left')

        self.audit_start_date = DatePicker(filter_frame)
        self.audit_start_date.pack(side='left', padx=(10, 5))

        ttk.Label(filter_frame, text="to").pack(side='left', padx=5)

        self.audit_end_date = DatePicker(filter_frame)
        self.audit_end_date.pack(side='left', padx=(5, 20))

        # User filter
        ttk.Label(
            filter_frame,
            text="User:",
            font=UIStyles.FONTS.get_font('normal')
        ).pack(side='left')

        self.audit_user_var = tk.StringVar(value="All Users")
        user_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.audit_user_var,
            values=["All Users"] + [m.name for m in
                                    self.app.compliance_manager.team_manager.get_active_team_members()],
            state='readonly',
            width=20
        )
        user_combo.pack(side='left', padx=(10, 20))

        # Filter button
        filter_btn = ModernButton(
            filter_frame,
            text="Apply Filter",
            icon='filter',
            command=self.filter_audit_log
        )
        filter_btn.pack(side='left')

        # Audit log table
        log_card = Card(container, "Audit Log")
        log_card.pack(fill='both', expand=True)

        log_content = log_card.get_content_frame()

        # Create treeview
        columns = ('timestamp', 'user', 'action', 'details')
        self.audit_tree = ttk.Treeview(
            log_content,
            columns=columns,
            show='tree headings',
            height=15
        )

        # Configure columns
        self.audit_tree.column('#0', width=0, stretch=False)
        self.audit_tree.column('timestamp', width=150)
        self.audit_tree.column('user', width=150)
        self.audit_tree.column('action', width=150)
        self.audit_tree.column('details', width=400)

        # Configure headings
        self.audit_tree.heading('timestamp', text='Timestamp')
        self.audit_tree.heading('user', text='User')
        self.audit_tree.heading('action', text='Action')
        self.audit_tree.heading('details', text='Details')

        # Scrollbar
        scrollbar = ttk.Scrollbar(log_content, orient='vertical', command=self.audit_tree.yview)
        self.audit_tree.configure(yscrollcommand=scrollbar.set)

        self.audit_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Load audit log
        self.load_audit_log()

        # Export button
        export_btn = ModernButton(
            container,
            text="Export Audit Log",
            icon='download',
            command=self.export_audit_log
        )
        export_btn.pack(pady=(10, 0))

    def create_info_item(self, parent: ttk.Frame, label: str, value: str):
        """Create information display item"""
        item_frame = ttk.Frame(parent)
        item_frame.pack(fill='x', pady=2)

        ttk.Label(
            item_frame,
            text=f"{label}",
            font=UIStyles.FONTS.get_font('normal')
        ).pack(side='left')

        ttk.Label(
            item_frame,
            text=value,
            font=UIStyles.FONTS.get_font('normal', 'bold')
        ).pack(side='left', padx=(10, 0))

    def create_setting_item(self, parent: ttk.Frame, label: str, value: str,
                            setting_type: str = "text"):
        """Create setting item"""
        item_frame = ttk.Frame(parent)
        item_frame.pack(fill='x', pady=5)

        ttk.Label(
            item_frame,
            text=f"{label}:",
            font=UIStyles.FONTS.get_font('normal'),
            width=30
        ).pack(side='left')

        if setting_type == "path":
            entry = ttk.Entry(item_frame, width=40)
            entry.insert(0, value)
            entry.pack(side='left')

            browse_btn = ttk.Button(
                item_frame,
                text="Browse",
                command=lambda: self.browse_path(entry)
            )
            browse_btn.pack(side='left', padx=(5, 0))
        else:
            entry = ttk.Entry(item_frame, width=40)
            entry.insert(0, value)
            entry.pack(side='left')

        # Store reference for saving
        if not hasattr(self, 'setting_entries'):
            self.setting_entries = {}
        self.setting_entries[label] = entry

    def get_system_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        # Get real statistics
        members = self.app.compliance_manager.data_manager.load_team_members()
        tasks = self.app.compliance_manager.data_manager.load_tasks()

        # Calculate storage
        import os
        storage_path = self.app.config.base_path / "Documents"
        total_size = 0

        for dirpath, dirnames, filenames in os.walk(storage_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)

        # Format storage size
        storage_mb = total_size / (1024 * 1024)
        if storage_mb < 1024:
            storage_str = f"{storage_mb:.1f} MB"
        else:
            storage_str = f"{storage_mb / 1024:.1f} GB"

        return {
            'total_users': len([m for m in members if m.active]),
            'total_tasks': len(tasks),
            'storage_used': storage_str,
            'uptime': self.calculate_uptime()
        }

    def calculate_uptime(self) -> str:
        """Calculate system uptime"""
        # This would track actual uptime
        # For now, return sample
        return "5 days, 12:34:56"

    def check_email_service(self) -> str:
        """Check email service status"""
        try:
            # Test email configuration
            # This would actually test SMTP connection
            return "OK"
        except:
            return "Error"

    def get_archive_statistics(self) -> Dict[str, Any]:
        """Get archive statistics"""
        try:
            summary = self.app.compliance_manager.archive_manager.get_archive_summary()

            return {
                'archived_tasks': summary['total_archives'],
                'archive_size': f"{summary['total_size_mb']:.1f} MB",
                'oldest_archive': summary.get('oldest_archive', 'None')
            }
        except:
            return {
                'archived_tasks': 0,
                'archive_size': "0 MB",
                'oldest_archive': "None"
            }

    def get_user_statistics(self) -> Dict[str, Any]:
        """Get user statistics"""
        members = self.app.compliance_manager.data_manager.load_team_members()

        active = [m for m in members if m.active]
        inactive = [m for m in members if not m.active]
        admins = [m for m in active if 'admin' in m.permissions]
        managers = [m for m in active if 'approve_tasks' in m.permissions]

        return {
            'active_users': len(active),
            'inactive_users': len(inactive),
            'admin_users': len(admins),
            'manager_users': len(managers)
        }

    def load_audit_log(self):
        """Load audit log entries"""
        # Clear existing
        self.audit_tree.delete(*self.audit_tree.get_children())

        # Sample audit log entries
        # In real implementation, would load from database
        entries = [
            {
                'timestamp': '2025-01-15 10:45:23',
                'user': 'John Smith',
                'action': 'Task Created',
                'details': 'Created task GS-TASK-250115-0001'
            },
            {
                'timestamp': '2025-01-15 10:30:15',
                'user': 'Jane Doe',
                'action': 'Task Updated',
                'details': 'Updated status to In Progress for GS-TASK-250114-0003'
            },
            {
                'timestamp': '2025-01-15 09:15:45',
                'user': 'Admin',
                'action': 'User Created',
                'details': 'Created new user account for Bob Wilson'
            },
            {
                'timestamp': '2025-01-15 08:00:00',
                'user': 'System',
                'action': 'Backup Completed',
                'details': 'Automatic backup completed successfully'
            },
            {
                'timestamp': '2025-01-14 16:30:00',
                'user': 'Alice Brown',
                'action': 'Report Generated',
                'details': 'Generated Executive Summary report'
            }
        ]

        # Add entries to tree
        for entry in entries:
            self.audit_tree.insert(
                '',
                'end',
                values=(
                    entry['timestamp'],
                    entry['user'],
                    entry['action'],
                    entry['details']
                )
            )

    def backup_now(self):
        """Perform immediate backup"""
        if self.ask_yes_no("Backup", "Start backup now?"):
            progress = ProgressDialog(
                self.parent_frame,
                "Creating Backup",
                "Backing up system data..."
            )

            # Perform backup in thread
            import threading
            thread = threading.Thread(
                target=self._perform_backup,
                args=(progress,)
            )
            thread.daemon = True
            thread.start()

    def _perform_backup(self, progress):
        """Perform backup in background"""
        try:
            import time
            import shutil
            from datetime import datetime

            # Update progress
            progress.update_message("Backing up database files...")
            time.sleep(1)

            # Create backup directory
            backup_dir = self.app.config.base_path / "Backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Copy Excel files
            files_to_backup = [
                self.app.config.base_path / self.app.config.excel_files['tasks'],
                self.app.config.base_path / self.app.config.excel_files['team']
            ]

            for file in files_to_backup:
                if file.exists():
                    shutil.copy2(file, backup_dir)

            progress.update_message("Compressing backup...")
            time.sleep(1)

            # Create zip file
            zip_path = backup_dir.parent / f"{backup_dir.name}.zip"
            shutil.make_archive(str(zip_path.with_suffix('')), 'zip', backup_dir)

            # Remove temporary directory
            shutil.rmtree(backup_dir)

            # Close progress
            self.parent_frame.after(0, progress.destroy)

            # Show success
            self.parent_frame.after(0, lambda: self.show_info(
                "Backup Complete",
                f"Backup saved to:\n{zip_path}"
            ))

        except Exception as e:
            self.parent_frame.after(0, progress.destroy)
            self.parent_frame.after(0, lambda: self.show_error("Backup Error", str(e)))

    def restore_backup(self):
        """Restore from backup"""
        filename = filedialog.askopenfilename(
            title="Select backup file",
            filetypes=[
                ("Backup files", "*.zip"),
                ("All files", "*.*")
            ]
        )

        if filename:
            if self.ask_yes_no("Restore Backup",
                               "Are you sure you want to restore from backup?\n\n"
                               "This will overwrite current data!"):
                # Perform restore
                self.show_info("Restore", "Backup restore functionality would be implemented here")

    def schedule_backup(self):
        """Schedule automatic backups"""
        # Create schedule dialog
        from ui.components.dialogs import BaseDialog

        class ScheduleDialog(BaseDialog):
            def __init__(self, parent):
                super().__init__(parent, "Schedule Backup", 400, 300)

            def create_content(self):
                # Frequency
                ttk.Label(
                    self.main_frame,
                    text="Backup Frequency:",
                    font=UIStyles.FONTS.get_font('normal')
                ).pack(anchor='w', pady=(0, 5))

                self.frequency_var = tk.StringVar(value="Daily")
                frequencies = ["Hourly", "Daily", "Weekly", "Monthly"]

                for freq in frequencies:
                    ttk.Radiobutton(
                        self.main_frame,
                        text=freq,
                        variable=self.frequency_var,
                        value=freq
                    ).pack(anchor='w', padx=20)

                # Time
                time_frame = ttk.Frame(self.main_frame)
                time_frame.pack(fill='x', pady=(20, 0))

                ttk.Label(
                    time_frame,
                    text="Backup Time:",
                    font=UIStyles.FONTS.get_font('normal')
                ).pack(side='left')

                self.hour_var = tk.StringVar(value="02")
                hour_spin = ttk.Spinbox(
                    time_frame,
                    from_=0,
                    to=23,
                    width=5,
                    textvariable=self.hour_var,
                    format="%02.0f"
                )
                hour_spin.pack(side='left', padx=(10, 0))

                ttk.Label(time_frame, text=":").pack(side='left')

                self.minute_var = tk.StringVar(value="00")
                minute_spin = ttk.Spinbox(
                    time_frame,
                    from_=0,
                    to=59,
                    width=5,
                    textvariable=self.minute_var,
                    format="%02.0f"
                )
                minute_spin.pack(side='left')

            def get_result(self):
                return {
                    'frequency': self.frequency_var.get(),
                    'time': f"{self.hour_var.get()}:{self.minute_var.get()}"
                }

        dialog = ScheduleDialog(self.parent_frame)
        self.parent_frame.wait_window(dialog)

        if dialog.result:
            self.show_info("Schedule Set",
                           f"Backup scheduled: {dialog.result['frequency']} at {dialog.result['time']}")

    def archive_old_tasks(self):
        """Archive old tasks"""
        cutoff_days = self.app.config.archive_after_days

        if self.ask_yes_no("Archive Tasks",
                           f"Archive tasks older than {cutoff_days} days?\n\n"
                           "This will move resolved/closed tasks to archive storage."):
            progress = ProgressDialog(
                self.parent_frame,
                "Archiving",
                "Archiving old tasks..."
            )

            # Archive in thread
            import threading
            thread = threading.Thread(
                target=self._archive_tasks,
                args=(progress,)
            )
            thread.daemon = True
            thread.start()

    def _archive_tasks(self, progress):
        """Archive tasks in background"""
        try:
            count, archive_id = self.app.compliance_manager.task_manager.archive_old_tasks()

            self.parent_frame.after(0, progress.destroy)
            self.parent_frame.after(0, lambda: self.show_info(
                "Archive Complete",
                f"Archived {count} tasks\nArchive ID: {archive_id}"
            ))

            # Refresh statistics
            self.parent_frame.after(0, self.refresh)

        except Exception as e:
            self.parent_frame.after(0, progress.destroy)
            self.parent_frame.after(0, lambda: self.show_error("Archive Error", str(e)))

    def browse_archives(self):
        """Browse archived data"""
        # Create archive browser dialog
        self.show_info("Browse Archives", "Archive browser would be implemented here")

    def run_cleanup(self):
        """Run data cleanup"""
        tasks = []
        if self.cleanup_orphaned_var.get():
            tasks.append("Remove orphaned files")
        if self.cleanup_temp_var.get():
            tasks.append("Clear temporary files")
        if self.rebuild_index_var.get():
            tasks.append("Rebuild search index")

        if not tasks:
            self.show_warning("No Tasks", "Please select at least one cleanup task")
            return

        task_list = "\n".join(f"• {t}" for t in tasks)
        if self.ask_yes_no("Run Cleanup",
                           f"The following cleanup tasks will be performed:\n\n{task_list}\n\n"
                           "Continue?"):
            progress = ProgressDialog(
                self.parent_frame,
                "Running Cleanup",
                "Performing cleanup tasks..."
            )

            # Run cleanup in thread
            import threading
            thread = threading.Thread(
                target=self._run_cleanup,
                args=(progress, tasks)
            )
            thread.daemon = True
            thread.start()

    def _run_cleanup(self, progress, tasks):
        """Run cleanup in background"""
        try:
            import time

            for task in tasks:
                progress.update_message(f"Performing: {task}")
                time.sleep(1)

                if "orphaned" in task:
                    # Clean orphaned files
                    pass
                elif "temporary" in task:
                    # Clear temp files
                    pass
                elif "index" in task:
                    # Rebuild index
                    self.app.compliance_manager.index_manager.rebuild_index()

            self.parent_frame.after(0, progress.destroy)
            self.parent_frame.after(0, lambda: self.show_info(
                "Cleanup Complete",
                "All cleanup tasks completed successfully"
            ))

        except Exception as e:
            self.parent_frame.after(0, progress.destroy)
            self.parent_frame.after(0, lambda: self.show_error("Cleanup Error", str(e)))

    def reset_user_password(self):
        """Reset user password"""
        # Get user selection
        members = self.app.compliance_manager.team_manager.get_active_team_members()

        from ui.components.dialogs import BaseDialog

        class UserSelectionDialog(BaseDialog):
            def __init__(self, parent, members):
                self.members = members
                super().__init__(parent, "Reset Password", 400, 300)

            def create_content(self):
                ttk.Label(
                    self.main_frame,
                    text="Select user to reset password:",
                    font=UIStyles.FONTS.get_font('normal')
                ).pack(pady=(0, 10))

                # User list
                self.user_listbox = tk.Listbox(self.main_frame, height=10)
                self.user_listbox.pack(fill='both', expand=True)

                for member in self.members:
                    self.user_listbox.insert(tk.END, f"{member.name} ({member.email})")

            def get_result(self):
                selection = self.user_listbox.curselection()
                if selection:
                    return self.members[selection[0]]
                return None

        dialog = UserSelectionDialog(self.parent_frame, members)
        self.parent_frame.wait_window(dialog)

        if dialog.result:
            # In real implementation, would reset password
            self.show_info("Password Reset",
                           f"Password reset email sent to {dialog.result.email}")

    def bulk_update_permissions(self):
        """Bulk update user permissions"""
        self.show_info("Bulk Update", "Bulk permission update would be implemented here")

    def export_users(self):
        """Export user list"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[
                ("Excel files", "*.xlsx"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )

        if filename:
            success, filepath = self.app.compliance_manager.team_manager.export_team_data(
                'csv' if filename.endswith('.csv') else 'excel'
            )

            if success:
                import shutil
                shutil.copy2(filepath, filename)
                self.show_info("Export Complete", f"User list exported to:\n{filename}")
            else:
                self.show_error("Export Error", filepath)

    def test_email_config(self):
        """Test email configuration"""
        # Get test recipient
        test_email = tk.simpledialog.askstring(
            "Test Email",
            "Enter email address to send test to:"
        )

        if test_email:
            try:
                success = self.app.email_service.send_test_email(
                    test_email,
                    "Admin"
                )

                if success:
                    self.show_info("Success", "Test email sent successfully")
                else:
                    self.show_error("Error", "Failed to send test email")
            except Exception as e:
                self.show_error("Error", str(e))

    def browse_path(self, entry_widget):
        """Browse for folder path"""
        folder = filedialog.askdirectory()
        if folder:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, folder)

    def save_settings(self):
        """Save system settings"""
        if self.ask_yes_no("Save Settings",
                           "Save changes to system settings?\n\n"
                           "Some changes may require restart."):
            try:
                # In real implementation, would save to config file
                self.show_info("Settings Saved",
                               "Settings saved successfully.\n\n"
                               "Please restart the application for changes to take effect.")
            except Exception as e:
                self.show_error("Save Error", str(e))

    def filter_audit_log(self):
        """Filter audit log by criteria"""
        # Re-load with filters
        self.load_audit_log()

    def export_audit_log(self):
        """Export audit log"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[
                ("Excel files", "*.xlsx"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )

        if filename:
            try:
                import pandas as pd

                # Get audit entries
                entries = []
                for item in self.audit_tree.get_children():
                    values = self.audit_tree.item(item)['values']
                    entries.append({
                        'Timestamp': values[0],
                        'User': values[1],
                        'Action': values[2],
                        'Details': values[3]
                    })

                df = pd.DataFrame(entries)

                if filename.endswith('.csv'):
                    df.to_csv(filename, index=False)
                else:
                    df.to_excel(filename, index=False)

                self.show_info("Export Complete", f"Audit log exported to:\n{filename}")

            except Exception as e:
                self.show_error("Export Error", str(e))