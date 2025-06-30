# ui/components/widgets.py
"""
Custom widgets for the Compliance Management System
"""

import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from datetime import datetime, date
from typing import Optional, Callable, List, Dict, Any, Tuple
from pathlib import Path

from ui.styles import UIStyles, get_theme_manager
from ui.components.base_components import (
    ModernFrame, ModernButton, ModernEntry, ModernLabel,
    SearchBar, StatusBadge, PriorityBadge, IconButton,
    Card, ScrollableFrame
)


class TaskTable(ModernFrame):
    """Enhanced task table widget with sorting and filtering"""

    def __init__(self, parent, on_select: Optional[Callable] = None,
                 on_double_click: Optional[Callable] = None, **kwargs):
        super().__init__(parent, **kwargs)

        self.on_select = on_select
        self.on_double_click = on_double_click
        self.tasks = []
        self.filtered_tasks = []
        self.sort_column = None
        self.sort_reverse = False

        # Create table
        self.create_table()

    def create_table(self):
        """Create the task table"""
        # Create treeview with scrollbars
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=BOTH, expand=True)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")

        # Treeview
        self.tree = ttk.Treeview(
            tree_frame,
            columns=('key', 'title', 'area', 'priority', 'status',
                     'assigned', 'target', 'updated'),
            show='tree headings',
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        vsb.configure(command=self.tree.yview)
        hsb.configure(command=self.tree.xview)

        # Configure columns
        self.tree.column('#0', width=0, stretch=NO)
        self.tree.column('key', width=120, minwidth=100)
        self.tree.column('title', width=300, minwidth=200)
        self.tree.column('area', width=150, minwidth=100)
        self.tree.column('priority', width=80, minwidth=60)
        self.tree.column('status', width=100, minwidth=80)
        self.tree.column('assigned', width=150, minwidth=100)
        self.tree.column('target', width=100, minwidth=80)
        self.tree.column('updated', width=150, minwidth=100)

        # Configure headings
        self.tree.heading('key', text='Task ID', command=lambda: self.sort_by('key'))
        self.tree.heading('title', text='Title', command=lambda: self.sort_by('title'))
        self.tree.heading('area', text='Compliance Area', command=lambda: self.sort_by('area'))
        self.tree.heading('priority', text='Priority', command=lambda: self.sort_by('priority'))
        self.tree.heading('status', text='Status', command=lambda: self.sort_by('status'))
        self.tree.heading('assigned', text='Assigned To', command=lambda: self.sort_by('assigned'))
        self.tree.heading('target', text='Target Date', command=lambda: self.sort_by('target'))
        self.tree.heading('updated', text='Last Updated', command=lambda: self.sort_by('updated'))

        # Layout
        self.tree.grid(row=0, column=0, sticky=NSEW)
        vsb.grid(row=0, column=1, sticky=NS)
        hsb.grid(row=1, column=0, sticky=EW)

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Bind events
        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        self.tree.bind('<Double-Button-1>', self._on_double_click)

        # Configure tags for row styling
        self.tree.tag_configure('overdue', foreground='red')
        self.tree.tag_configure('completed', foreground='green')
        self.tree.tag_configure('high_priority', font=('', 10, 'bold'))

    def load_tasks(self, tasks: List[Any]):
        """Load tasks into table"""
        self.tasks = tasks
        self.filtered_tasks = tasks
        self.refresh_display()

    def refresh_display(self):
        """Refresh table display"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add filtered tasks
        for task in self.filtered_tasks:
            self._add_task_row(task)

    def _add_task_row(self, task: Any):
        """Add task row to table"""
        # Prepare values
        values = (
            task.key,
            task.title,
            task.compliance_area,
            task.priority,
            task.status,
            ', '.join(task.allocated_to),
            task.target_date or '',
            task.date_updated or task.created_date
        )

        # Determine tags
        tags = []
        if task.is_overdue():
            tags.append('overdue')
        if task.status in ['Resolved', 'Closed']:
            tags.append('completed')
        if task.priority == 'Critical':
            tags.append('high_priority')

        # Insert row
        self.tree.insert('', 'end', values=values, tags=tags)

    def sort_by(self, column: str):
        """Sort table by column"""
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False

        # Sort tasks
        if column == 'key':
            self.filtered_tasks.sort(key=lambda t: t.key, reverse=self.sort_reverse)
        elif column == 'title':
            self.filtered_tasks.sort(key=lambda t: t.title.lower(), reverse=self.sort_reverse)
        elif column == 'area':
            self.filtered_tasks.sort(key=lambda t: t.compliance_area, reverse=self.sort_reverse)
        elif column == 'priority':
            priority_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}
            self.filtered_tasks.sort(
                key=lambda t: priority_order.get(t.priority, 4),
                reverse=self.sort_reverse
            )
        elif column == 'status':
            self.filtered_tasks.sort(key=lambda t: t.status, reverse=self.sort_reverse)
        elif column == 'assigned':
            self.filtered_tasks.sort(
                key=lambda t: ', '.join(t.allocated_to),
                reverse=self.sort_reverse
            )
        elif column == 'target':
            self.filtered_tasks.sort(
                key=lambda t: t.target_date or '9999-12-31',
                reverse=self.sort_reverse
            )
        elif column == 'updated':
            self.filtered_tasks.sort(
                key=lambda t: t.date_updated or t.created_date,
                reverse=self.sort_reverse
            )

        # Update display
        self.refresh_display()

        # Update heading to show sort direction
        for col in self.tree['columns']:
            heading = self.tree.heading(col)['text'].rstrip(' ▲▼')
            self.tree.heading(col, text=heading)

        # Add sort indicator
        sort_indicator = ' ▼' if self.sort_reverse else ' ▲'
        current_heading = self.tree.heading(column)['text'].rstrip(' ▲▼')
        self.tree.heading(column, text=current_heading + sort_indicator)

    def filter_tasks(self, filters: Dict[str, Any]):
        """Apply filters to tasks"""
        self.filtered_tasks = []

        for task in self.tasks:
            include = True

            # Check each filter
            if filters.get('status') and task.status != filters['status']:
                include = False
            elif filters.get('priority') and task.priority != filters['priority']:
                include = False
            elif filters.get('area') and task.compliance_area != filters['area']:
                include = False
            elif filters.get('assigned') and filters['assigned'] not in task.allocated_to:
                include = False
            elif filters.get('search'):
                search_text = filters['search'].lower()
                if not any(search_text in str(getattr(task, field, '')).lower()
                          for field in ['key', 'title', 'description']):
                    include = False

            if include:
                self.filtered_tasks.append(task)

        self.refresh_display()

    def get_selected_task(self) -> Optional[Any]:
        """Get currently selected task"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            task_key = item['values'][0]
            return next((t for t in self.tasks if t.key == task_key), None)
        return None

    def _on_select(self, event):
        """Handle row selection"""
        if self.on_select:
            task = self.get_selected_task()
            if task:
                self.on_select(task)

    def _on_double_click(self, event):
        """Handle double click"""
        if self.on_double_click:
            task = self.get_selected_task()
            if task:
                self.on_double_click(task)


class TeamTable(ModernFrame):
    """Team member table widget"""

    def __init__(self, parent, on_select: Optional[Callable] = None, **kwargs):
        super().__init__(parent, **kwargs)

        self.on_select = on_select
        self.members = []

        # Create table
        self.create_table()

    def create_table(self):
        """Create the team table"""
        # Create treeview with scrollbars
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=BOTH, expand=True)

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")

        # Treeview
        self.tree = ttk.Treeview(
            tree_frame,
            columns=('name', 'email', 'department', 'role', 'manager', 'active'),
            show='tree headings',
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        vsb.configure(command=self.tree.yview)
        hsb.configure(command=self.tree.xview)

        # Configure columns
        self.tree.column('#0', width=0, stretch=NO)
        self.tree.column('name', width=200, minwidth=150)
        self.tree.column('email', width=250, minwidth=200)
        self.tree.column('department', width=150, minwidth=100)
        self.tree.column('role', width=150, minwidth=100)
        self.tree.column('manager', width=150, minwidth=100)
        self.tree.column('active', width=80, minwidth=60)

        # Configure headings
        self.tree.heading('name', text='Name')
        self.tree.heading('email', text='Email')
        self.tree.heading('department', text='Department')
        self.tree.heading('role', text='Role')
        self.tree.heading('manager', text='Manager')
        self.tree.heading('active', text='Active')

        # Layout
        self.tree.grid(row=0, column=0, sticky=NSEW)
        vsb.grid(row=0, column=1, sticky=NS)
        hsb.grid(row=1, column=0, sticky=EW)

        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Bind events
        self.tree.bind('<<TreeviewSelect>>', self._on_select)

        # Configure tags
        self.tree.tag_configure('inactive', foreground='gray')
        self.tree.tag_configure('manager', font=('', 10, 'bold'))

    def load_members(self, members: List[Any]):
        """Load team members into table"""
        self.members = members
        self.refresh_display()

    def refresh_display(self):
        """Refresh table display"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Add members
        for member in self.members:
            self._add_member_row(member)

    def _add_member_row(self, member: Any):
        """Add member row to table"""
        # Prepare values
        values = (
            member.name,
            member.email,
            member.department,
            member.role,
            member.manager or '',
            'Yes' if member.active else 'No'
        )

        # Determine tags
        tags = []
        if not member.active:
            tags.append('inactive')
        if 'manager' in member.role.lower():
            tags.append('manager')

        # Insert row
        self.tree.insert('', 'end', values=values, tags=tags)

    def get_selected_member(self) -> Optional[Any]:
        """Get currently selected member"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            member_name = item['values'][0]
            return next((m for m in self.members if m.name == member_name), None)
        return None

    def _on_select(self, event):
        """Handle row selection"""
        if self.on_select:
            member = self.get_selected_member()
            if member:
                self.on_select(member)


class NotificationPanel(ModernFrame):
    """Notification display panel"""

    def __init__(self, parent, max_notifications: int = 10, **kwargs):
        super().__init__(parent, style_type='card', **kwargs)

        self.max_notifications = max_notifications
        self.notifications = []

        # Create UI
        self.create_ui()

    def create_ui(self):
        """Create notification UI"""
        # Header
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=X, padx=10, pady=(10, 5))

        title = ModernLabel(
            header_frame,
            text="Notifications",
            style_type='heading3'
        )
        title.pack(side=LEFT)

        # Clear button
        clear_btn = ModernButton(
            header_frame,
            text="Clear All",
            command=self.clear_all,
            style_type='link'
        )
        clear_btn.pack(side=RIGHT)

        # Separator
        ttk.Separator(self, orient='horizontal').pack(fill=X, padx=10, pady=5)

        # Notification area with scrolling
        self.notif_frame = ScrollableFrame(self)
        self.notif_frame.pack(fill=BOTH, expand=True, padx=10, pady=(0, 10))

        # No notifications message
        self.empty_label = ModernLabel(
            self.notif_frame.get_frame(),
            text="No new notifications",
            style_type='caption'
        )
        self.empty_label.pack(pady=20)

    def add_notification(self, message: str, notif_type: str = 'info',
                        timestamp: Optional[datetime] = None):
        """Add notification"""
        if not timestamp:
            timestamp = datetime.now()

        notification = {
            'message': message,
            'type': notif_type,
            'timestamp': timestamp,
            'read': False
        }

        self.notifications.insert(0, notification)

        # Limit notifications
        if len(self.notifications) > self.max_notifications:
            self.notifications = self.notifications[:self.max_notifications]

        self.refresh_display()

    def refresh_display(self):
        """Refresh notification display"""
        # Clear current display
        for widget in self.notif_frame.get_frame().winfo_children():
            widget.destroy()

        if not self.notifications:
            # Show empty message
            self.empty_label = ModernLabel(
                self.notif_frame.get_frame(),
                text="No new notifications",
                style_type='caption'
            )
            self.empty_label.pack(pady=20)
        else:
            # Display notifications
            for i, notif in enumerate(self.notifications):
                self._create_notification_widget(notif, i)

    def _create_notification_widget(self, notification: Dict, index: int):
        """Create notification widget"""
        # Notification frame
        notif_widget = ttk.Frame(
            self.notif_frame.get_frame(),
            relief='solid',
            borderwidth=1
        )
        notif_widget.pack(fill=X, pady=2)

        # Icon based on type
        icon_map = {
            'info': UIStyles.ICONS['info'],
            'warning': UIStyles.ICONS['warning'],
            'error': UIStyles.ICONS['error'],
            'success': UIStyles.ICONS['check']
        }
        icon = icon_map.get(notification['type'], UIStyles.ICONS['info'])

        # Icon label
        icon_label = ttk.Label(notif_widget, text=icon)
        icon_label.pack(side=LEFT, padx=(10, 5), pady=5)

        # Content frame
        content_frame = ttk.Frame(notif_widget)
        content_frame.pack(side=LEFT, fill=BOTH, expand=True, pady=5)

        # Message
        msg_label = ttk.Label(
            content_frame,
            text=notification['message'],
            wraplength=300
        )
        msg_label.pack(anchor=W)

        # Timestamp
        time_label = ModernLabel(
            content_frame,
            text=notification['timestamp'].strftime("%H:%M"),
            style_type='caption'
        )
        time_label.pack(anchor=W)

        # Close button
        close_btn = ttk.Button(
            notif_widget,
            text=UIStyles.ICONS['close'],
            width=3,
            command=lambda: self.remove_notification(index)
        )
        close_btn.pack(side=RIGHT, padx=(5, 10))

        # Mark as read on hover
        notif_widget.bind('<Enter>', lambda e: self._mark_read(index))

    def remove_notification(self, index: int):
        """Remove notification"""
        if 0 <= index < len(self.notifications):
            self.notifications.pop(index)
            self.refresh_display()

    def clear_all(self):
        """Clear all notifications"""
        self.notifications = []
        self.refresh_display()

    def _mark_read(self, index: int):
        """Mark notification as read"""
        if 0 <= index < len(self.notifications):
            self.notifications[index]['read'] = True

    def get_unread_count(self) -> int:
        """Get unread notification count"""
        return sum(1 for n in self.notifications if not n['read'])


class QuickActions(ModernFrame):
    """Quick action buttons panel"""

    def __init__(self, parent, actions: List[Dict[str, Any]], **kwargs):
        super().__init__(parent, **kwargs)

        self.actions = actions
        self.create_buttons()

    def create_buttons(self):
        """Create action buttons"""
        for i, action in enumerate(self.actions):
            btn = ModernButton(
                self,
                text=action.get('text', ''),
                icon=action.get('icon'),
                command=action.get('command'),
                style_type=action.get('style', 'default')
            )
            btn.pack(side=LEFT, padx=(0, 5) if i < len(self.actions) - 1 else 0)


class FilterPanel(ModernFrame):
    """Filter panel for tables"""

    def __init__(self, parent, filters: Dict[str, Any],
                 on_filter: Optional[Callable] = None, **kwargs):
        super().__init__(parent, style_type='card', **kwargs)

        self.filters = filters
        self.on_filter = on_filter
        self.filter_vars = {}

        self.create_ui()

    def create_ui(self):
        """Create filter UI"""
        # Title
        title = ModernLabel(
            self,
            text="Filters",
            style_type='heading3'
        )
        title.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        # Create filter controls
        row = 1
        for filter_name, filter_config in self.filters.items():
            # Label
            label = ttk.Label(self, text=filter_config['label'])
            label.grid(row=row, column=0, sticky=W, pady=2)

            # Control based on type
            filter_type = filter_config.get('type', 'combo')

            if filter_type == 'combo':
                var = tk.StringVar()
                combo = ttk.Combobox(
                    self,
                    textvariable=var,
                    values=filter_config.get('values', []),
                    state='readonly',
                    width=20
                )
                combo.grid(row=row, column=1, sticky=W, pady=2, padx=(10, 0))
                combo.set(filter_config.get('default', ''))

            elif filter_type == 'entry':
                var = tk.StringVar()
                entry = ModernEntry(
                    self,
                    textvariable=var,
                    placeholder=filter_config.get('placeholder', '')
                )
                entry.grid(row=row, column=1, sticky=W, pady=2, padx=(10, 0))

            elif filter_type == 'check':
                var = tk.BooleanVar()
                check = ttk.Checkbutton(
                    self,
                    text=filter_config.get('text', ''),
                    variable=var
                )
                check.grid(row=row, column=1, sticky=W, pady=2, padx=(10, 0))

            self.filter_vars[filter_name] = var
            row += 1

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.grid(row=row, column=0, columnspan=2, pady=(10, 0))

        apply_btn = ModernButton(
            button_frame,
            text="Apply",
            command=self.apply_filters,
            style_type='primary'
        )
        apply_btn.pack(side=LEFT, padx=(0, 5))

        clear_btn = ModernButton(
            button_frame,
            text="Clear",
            command=self.clear_filters,
            style_type='secondary'
        )
        clear_btn.pack(side=LEFT)

    def apply_filters(self):
        """Apply current filters"""
        filter_values = {}

        for filter_name, var in self.filter_vars.items():
            filter_values[filter_name] = var.get()

        if self.on_filter:
            self.on_filter(filter_values)

    def clear_filters(self):
        """Clear all filters"""
        for var in self.filter_vars.values():
            if isinstance(var, tk.StringVar):
                var.set('')
            elif isinstance(var, tk.BooleanVar):
                var.set(False)

        self.apply_filters()


class TaskDetailsPanel(ModernFrame):
    """Task details display panel"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, style_type='card', **kwargs)

        self.current_task = None
        self.create_ui()

    def create_ui(self):
        """Create task details UI"""
        # Title
        self.title_label = ModernLabel(
            self,
            text="Task Details",
            style_type='heading3'
        )
        self.title_label.pack(pady=(0, 10))

        # Content frame with scrolling
        self.content_scroll = ScrollableFrame(self)
        self.content_scroll.pack(fill=BOTH, expand=True)
        self.content_frame = self.content_scroll.get_frame()

        self.show_no_selection()

    def load_task(self, task: Any):
        """Load task details"""
        self.current_task = task

        # Clear content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        if not task:
            self.show_no_selection()
            return

        # Task information sections
        self.create_info_section("Basic Information", [
            ("Task ID", task.key),
            ("Title", task.title),
            ("Compliance Area", task.compliance_area),
            ("Subcategory", task.subcategory),
            ("Priority", task.priority, self._get_priority_widget),
            ("Status", task.status, self._get_status_widget),
            ("Created Date", task.created_date),
            ("Target Date", task.target_date or "Not set")
        ])

        self.create_info_section("Assignment", [
            ("Task Setter", task.task_setter),
            ("Allocated To", ', '.join(task.allocated_to) if task.allocated_to else "Unassigned"),
            ("Manager", task.manager or "Not specified"),
            ("Manager Email", task.manager_email or "Not specified")
        ])

        self.create_info_section("Description", [
            ("", task.description or "No description provided")
        ])

        # Actions taken
        if task.actions_taken:
            self.create_actions_section(task.actions_taken)

        # File attachments
        if task.file_attachments:
            self.create_attachments_section(task.file_attachments)

    def show_no_selection(self):
        """Show no task selected message"""
        label = ModernLabel(
            self.content_frame,
            text="Select a task to view details",
            style_type='caption'
        )
        label.pack(pady=50)

    def create_info_section(self, title: str, fields: List[Tuple]):
        """Create information section"""
        # Section frame
        section = ttk.LabelFrame(self.content_frame, text=title, padding=10)
        section.pack(fill=X, pady=(0, 10))

        # Fields
        for i, field_data in enumerate(fields):
            if len(field_data) == 2:
                label, value = field_data
                widget_func = None
            else:
                label, value, widget_func = field_data

            if label:
                field_label = ttk.Label(section, text=f"{label}:")
                field_label.grid(row=i, column=0, sticky=W, pady=2)

            if widget_func:
                value_widget = widget_func(section, value)
            else:
                value_widget = ttk.Label(section, text=str(value))

            value_widget.grid(row=i, column=1, sticky=W, padx=(10, 0), pady=2)

    def create_actions_section(self, actions: List[Any]):
        """Create actions taken section"""
        section = ttk.LabelFrame(self.content_frame, text="Actions Taken", padding=10)
        section.pack(fill=X, pady=(0, 10))

        for i, action in enumerate(actions[-5:]):  # Show last 5 actions
            # Action frame
            action_frame = ttk.Frame(section)
            action_frame.pack(fill=X, pady=2)

            # Timestamp and user
            info_text = f"{action.timestamp} - {action.user}"
            info_label = ModernLabel(action_frame, text=info_text, style_type='caption')
            info_label.pack(anchor=W)

            # Action details
            details_text = f"{action.action}: {action.details}"
            details_label = ttk.Label(action_frame, text=details_text)
            details_label.pack(anchor=W)

            if i < len(actions) - 1:
                ttk.Separator(section, orient='horizontal').pack(fill=X, pady=5)

    def create_attachments_section(self, attachments: List[Any]):
        """Create file attachments section"""
        section = ttk.LabelFrame(self.content_frame, text="File Attachments", padding=10)
        section.pack(fill=X, pady=(0, 10))

        for attachment in attachments:
            # Attachment frame
            att_frame = ttk.Frame(section)
            att_frame.pack(fill=X, pady=2)

            # Icon and filename
            icon_label = ttk.Label(att_frame, text=UIStyles.ICONS['attachment'])
            icon_label.pack(side=LEFT)

            file_label = ttk.Label(att_frame, text=attachment.filename)
            file_label.pack(side=LEFT, padx=(5, 0))

            # Size
            size_label = ModernLabel(
                att_frame,
                text=f"({attachment.file_size})",
                style_type='caption'
            )
            size_label.pack(side=LEFT, padx=(5, 0))

    def _get_priority_widget(self, parent, priority: str) -> ttk.Widget:
        """Get priority display widget"""
        return PriorityBadge(parent, priority)

    def _get_status_widget(self, parent, status: str) -> ttk.Widget:
        """Get status display widget"""
        return StatusBadge(parent, status)


class ApprovalPanel(ModernFrame):
    """Approval actions panel"""

    def __init__(self, parent, on_approve: Optional[Callable] = None,
                 on_reject: Optional[Callable] = None, **kwargs):
        super().__init__(parent, style_type='card', **kwargs)

        self.on_approve = on_approve
        self.on_reject = on_reject
        self.current_task = None

        self.create_ui()

    def create_ui(self):
        """Create approval UI"""
        # Title
        title = ModernLabel(
            self,
            text="Approval Actions",
            style_type='heading3'
        )
        title.pack(pady=(0, 10))

        # Comments entry
        comment_label = ttk.Label(self, text="Comments:")
        comment_label.pack(anchor=W, pady=(10, 5))

        self.comment_text = tk.Text(self, height=4, width=40)
        self.comment_text.pack(fill=X, pady=(0, 10))

        # Buttons
        button_frame = ttk.Frame(self)
        button_frame.pack()

        self.approve_btn = ModernButton(
            button_frame,
            text="Approve",
            icon='check',
            command=self._on_approve,
            style_type='success'
        )
        self.approve_btn.pack(side=LEFT, padx=(0, 5))

        self.reject_btn = ModernButton(
            button_frame,
            text="Reject",
            icon='close',
            command=self._on_reject,
            style_type='danger'
        )
        self.reject_btn.pack(side=LEFT)

    def set_task(self, task: Any):
        """Set current task"""
        self.current_task = task
        self.comment_text.delete(1.0, END)

        # Enable/disable buttons based on task status
        if task and task.status == 'Pending Approval':
            self.approve_btn.configure(state='normal')
            self.reject_btn.configure(state='normal')
        else:
            self.approve_btn.configure(state='disabled')
            self.reject_btn.configure(state='disabled')

    def _on_approve(self):
        """Handle approve button"""
        if self.on_approve and self.current_task:
            comments = self.comment_text.get(1.0, END).strip()
            self.on_approve(self.current_task, comments)

    def _on_reject(self):
        """Handle reject button"""
        if self.on_reject and self.current_task:
            comments = self.comment_text.get(1.0, END).strip()
            if not comments:
                tk.messagebox.showwarning(
                    "Comments Required",
                    "Please provide a reason for rejection"
                )
                return
            self.on_reject(self.current_task, comments)


class LegislationBrowser(ModernFrame):
    """Legislation reference browser"""

    def __init__(self, parent, on_select: Optional[Callable] = None, **kwargs):
        super().__init__(parent, **kwargs)

        self.on_select = on_select
        self.legislation_items = []

        self.create_ui()

    def create_ui(self):
        """Create legislation browser UI"""
        # Search bar
        self.search_bar = SearchBar(
            self,
            callback=self.search_legislation,
            placeholder="Search legislation..."
        )
        self.search_bar.pack(fill=X, pady=(0, 10))

        # Category filter
        filter_frame = ttk.Frame(self)
        filter_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(filter_frame, text="Category:").pack(side=LEFT)

        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.category_var,
            values=['All', 'Data Protection', 'Anti-Bribery', 'Environmental',
                   'Product Safety', 'Financial', 'Employment'],
            state='readonly',
            width=20
        )
        self.category_combo.pack(side=LEFT, padx=(5, 0))
        self.category_combo.set('All')
        self.category_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_legislation())

        # Legislation list
        list_frame = ttk.Frame(self)
        list_frame.pack(fill=BOTH, expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")

        # Listbox
        self.legislation_list = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            height=15
        )
        scrollbar.configure(command=self.legislation_list.yview)

        self.legislation_list.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Bind selection
        self.legislation_list.bind('<<ListboxSelect>>', self._on_select)

    def load_legislation(self, legislation_list: List[Any]):
        """Load legislation items"""
        self.legislation_items = legislation_list
        self.refresh_display()

    def refresh_display(self):
        """Refresh legislation display"""
        self.legislation_list.delete(0, END)

        for item in self.legislation_items:
            display_text = f"{item.code} - {item.full_name}"
            self.legislation_list.insert(END, display_text)

    def search_legislation(self, search_text: str):
        """Search legislation"""
        # Filter based on search text
        if not search_text:
            filtered = self.legislation_items
        else:
            search_lower = search_text.lower()
            filtered = [
                item for item in self.legislation_items
                if (search_lower in item.code.lower() or
                    search_lower in item.full_name.lower() or
                    search_lower in item.summary.lower())
            ]

        # Apply category filter
        category = self.category_var.get()
        if category != 'All':
            filtered = [item for item in filtered if item.category == category]

        # Update display
        self.legislation_list.delete(0, END)
        for item in filtered:
            display_text = f"{item.code} - {item.full_name}"
            self.legislation_list.insert(END, display_text)

    def filter_legislation(self):
        """Apply category filter"""
        self.search_legislation(self.search_bar.get_search_text())

    def get_selected_legislation(self) -> Optional[Any]:
        """Get selected legislation"""
        selection = self.legislation_list.curselection()
        if selection:
            index = selection[0]
            # Find matching legislation
            display_text = self.legislation_list.get(index)
            code = display_text.split(' - ')[0]
            return next((item for item in self.legislation_items if item.code == code), None)
        return None

    def _on_select(self, event):
        """Handle selection"""
        if self.on_select:
            legislation = self.get_selected_legislation()
            if legislation:
                self.on_select(legislation)


class FileAttachmentWidget(ModernFrame):
    """File attachment management widget"""

    def __init__(self, parent, max_files: int = 10,
                 max_size_mb: int = 10, **kwargs):
        super().__init__(parent, style_type='card', **kwargs)

        self.max_files = max_files
        self.max_size_mb = max_size_mb
        self.attachments = []

        self.create_ui()

    def create_ui(self):
        """Create file attachment UI"""
        # Title
        title = ModernLabel(
            self,
            text="File Attachments",
            style_type='heading3'
        )
        title.pack(pady=(0, 10))

        # Add button
        self.add_btn = ModernButton(
            self,
            text="Add File",
            icon='plus',
            command=self.add_file,
            style_type='primary'
        )
        self.add_btn.pack(pady=(0, 10))

        # File list frame
        self.file_list_frame = ttk.Frame(self)
        self.file_list_frame.pack(fill=BOTH, expand=True)

        # Show empty message
        self.show_empty_message()

    def add_file(self):
        """Add file attachment"""
        from tkinter import filedialog

        if len(self.attachments) >= self.max_files:
            tk.messagebox.showwarning(
                "Maximum Files",
                f"Maximum {self.max_files} files allowed"
            )
            return

        filename = filedialog.askopenfilename(
            title="Select File",
            filetypes=[("All files", "*.*")]
        )

        if filename:
            # Check file size
            file_size = Path(filename).stat().st_size / (1024 * 1024)  # MB
            if file_size > self.max_size_mb:
                tk.messagebox.showwarning(
                    "File Too Large",
                    f"File size ({file_size:.1f} MB) exceeds maximum ({self.max_size_mb} MB)"
                )
                return

            # Add to attachments
            attachment = {
                'path': filename,
                'name': Path(filename).name,
                'size': file_size
            }
            self.attachments.append(attachment)
            self.refresh_display()

    def remove_file(self, index: int):
        """Remove file attachment"""
        if 0 <= index < len(self.attachments):
            self.attachments.pop(index)
            self.refresh_display()

    def refresh_display(self):
        """Refresh file list display"""
        # Clear current display
        for widget in self.file_list_frame.winfo_children():
            widget.destroy()

        if not self.attachments:
            self.show_empty_message()
        else:
            for i, attachment in enumerate(self.attachments):
                self.create_file_widget(attachment, i)

    def show_empty_message(self):
        """Show no files message"""
        label = ModernLabel(
            self.file_list_frame,
            text="No files attached",
            style_type='caption'
        )
        label.pack(pady=20)

    def create_file_widget(self, attachment: Dict, index: int):
        """Create file attachment widget"""
        # File frame
        file_frame = ttk.Frame(self.file_list_frame)
        file_frame.pack(fill=X, pady=2)

        # Icon
        icon_label = ttk.Label(file_frame, text=UIStyles.ICONS['file'])
        icon_label.pack(side=LEFT)

        # Filename
        name_label = ttk.Label(file_frame, text=attachment['name'])
        name_label.pack(side=LEFT, padx=(5, 0))

        # Size
        size_label = ModernLabel(
            file_frame,
            text=f"({attachment['size']:.1f} MB)",
            style_type='caption'
        )
        size_label.pack(side=LEFT, padx=(5, 0))

        # Remove button
        remove_btn = ttk.Button(
            file_frame,
            text=UIStyles.ICONS['delete'],
            width=3,
            command=lambda: self.remove_file(index)
        )
        remove_btn.pack(side=RIGHT)

    def get_attachments(self) -> List[str]:
        """Get list of attachment paths"""
        return [att['path'] for att in self.attachments]

    def clear_attachments(self):
        """Clear all attachments"""
        self.attachments = []
        self.refresh_display()