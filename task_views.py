# views/task_views.py
"""
Task-related views for Compliance Management System
Handles task list, details, and creation with proper error handling
"""

import tkinter as tk
from tkinter import ttk, filedialog
import ttkbootstrap as tb
from datetime import datetime, date
from typing import Dict, Any, List, Optional
import pandas as pd

from views import BaseView
from ui.components import (
    ModernFrame, ModernButton, ModernLabel, Card,
    TaskTable, SearchBar, FilterPanel, TaskDetailsPanel,
    ApprovalPanel, FileAttachmentWidget
)
from ui.components.dialogs import TaskDialog, ConfirmDialog
from ui.styles import UIStyles


class TaskListView(BaseView):
    """Task list view with filtering and search"""

    def __init__(self, parent_frame: ttk.Frame, app: Any):
        super().__init__(parent_frame, app)
        self.current_filters = {}
        self.selected_task = None
        self.task_table = None
        self.search_bar = None
        self.filter_panel = None

    def show(self):
        """Display the task list view"""
        super().show()

        # Main container
        main_container = ttk.Frame(self.parent_frame)
        main_container.pack(fill='both', expand=True, padx=20, pady=20)

        # Title and actions
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill='x', pady=(0, 20))

        title_label = ModernLabel(
            header_frame,
            text="Task Management",
            style_type='heading1'
        )
        title_label.pack(side='left')

        # Action buttons
        action_frame = ttk.Frame(header_frame)
        action_frame.pack(side='right')

        if self.check_permission('create_tasks'):
            new_btn = ModernButton(
                action_frame,
                text="New Task",
                icon='plus',
                command=self.create_task,
                style_type='primary'
            )
            new_btn.pack(side='left', padx=(0, 5))

        refresh_btn = ModernButton(
            action_frame,
            text="Refresh",
            icon='refresh',
            command=self.refresh_tasks,
            style_type='secondary'
        )
        refresh_btn.pack(side='left', padx=(0, 5))

        export_btn = ModernButton(
            action_frame,
            text="Export",
            icon='download',
            command=self.export_tasks,
            style_type='secondary'
        )
        export_btn.pack(side='left')

        # Search bar
        search_frame = ttk.Frame(main_container)
        search_frame.pack(fill='x', pady=(0, 10))

        self.search_bar = SearchBar(
            search_frame,
            callback=self.on_search,
            placeholder="Search tasks..."
        )
        self.search_bar.pack(fill='x')

        # Content area with filters and table
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill='both', expand=True)

        # Left: Filters
        self.create_filter_panel(content_frame)

        # Right: Task table
        table_frame = ttk.Frame(content_frame)
        table_frame.pack(side='right', fill='both', expand=True, padx=(10, 0))

        # Task table
        self.task_table = TaskTable(
            table_frame,
            on_select=self.on_task_select,
            on_double_click=self.on_task_double_click
        )
        self.task_table.pack(fill='both', expand=True)

        # Load tasks
        self.load_tasks()

    def create_filter_panel(self, parent: ttk.Frame):
        """Create filter panel"""
        filter_frame = ttk.Frame(parent)
        filter_frame.pack(side='left', fill='y', padx=(0, 10))

        # Build filters based on available data
        filters = self.build_filter_options()

        self.filter_panel = FilterPanel(
            filter_frame,
            filters,
            on_filter=self.on_filter_change
        )
        self.filter_panel.pack(fill='y')

    def build_filter_options(self) -> Dict[str, Any]:
        """Build filter options dynamically"""
        filters = {
            'status': {
                'label': 'Status',
                'type': 'combo',
                'values': ['All', 'Open', 'In Progress', 'Pending Approval',
                           'Approved', 'Resolved', 'Closed'],
                'default': 'All'
            },
            'priority': {
                'label': 'Priority',
                'type': 'combo',
                'values': ['All', 'Critical', 'High', 'Medium', 'Low'],
                'default': 'All'
            }
        }

        # Add compliance areas if available
        if hasattr(self.app, 'config') and hasattr(self.app.config, 'compliance_areas'):
            filters['area'] = {
                'label': 'Compliance Area',
                'type': 'combo',
                'values': ['All'] + list(getattr(self.app.config, 'compliance_areas', [])),
                'default': 'All'
            }

        # Add team member filter if we have access to team data
        try:
            if hasattr(self.app, 'compliance_manager'):
                team_members = self.app.compliance_manager.team_manager.get_active_team_members()
                member_names = [m.name for m in team_members]
                filters['assigned'] = {
                    'label': 'Assigned To',
                    'type': 'combo',
                    'values': ['All', 'Me'] + member_names,
                    'default': 'All'
                }
        except:
            self.logger.debug("Could not load team members for filter")

        filters['overdue'] = {
            'label': 'Overdue Only',
            'type': 'check',
            'default': False
        }

        return filters

    def load_tasks(self):
        """Load all tasks with error handling"""
        try:
            self.show_progress("Loading tasks...")

            # Check if data manager exists
            if not hasattr(self.app, 'compliance_manager'):
                self.show_error("Configuration Error", "Compliance manager not initialized")
                return

            # Get all tasks
            tasks = self.app.compliance_manager.task_manager.get_all_tasks()

            # Check permissions and filter if needed
            if not self.check_permission('view_all_tasks'):
                # Filter to user's tasks only
                current_user = getattr(self.app, 'current_user', None)
                if current_user:
                    tasks = [t for t in tasks if
                             getattr(t, 'task_setter', '') == current_user or
                             current_user in getattr(t, 'allocated_to', []) or
                             getattr(t, 'manager', '') == current_user]

            # Load into table
            if self.task_table:
                self.task_table.load_tasks(tasks)

            # Apply current filters
            if self.current_filters:
                self.apply_filters()

            self.update_status(f"Loaded {len(tasks)} tasks")

        except Exception as e:
            self.logger.error(f"Error loading tasks: {e}")
            self.show_error("Load Error", f"Failed to load tasks: {str(e)}")
        finally:
            self.hide_progress()

    def refresh_tasks(self):
        """Refresh task list"""
        self.load_tasks()

    def on_search(self, query: str):
        """Handle search with debouncing"""
        self.current_filters['search'] = query
        self.apply_filters()

    def on_filter_change(self, filters: Dict[str, Any]):
        """Handle filter change"""
        self.current_filters.update(filters)
        self.apply_filters()

    def apply_filters(self):
        """Apply all current filters to the task table"""
        if self.task_table:
            self.task_table.filter_tasks(self.current_filters)

    def on_task_select(self, task: Any):
        """Handle task selection"""
        self.selected_task = task
        self.set_view_data('selected_task', task)

        # Update app-level selection if needed
        if hasattr(self.app, 'selected_task'):
            self.app.selected_task = task

        self.update_status(f"Selected: {getattr(task, 'key', 'Unknown')}")

    def on_task_double_click(self, task: Any):
        """Handle task double-click"""
        self.show_task_details(task)

    def show_task_details(self, task: Any):
        """Show detailed task view"""
        if hasattr(self.app, 'show_task_details'):
            self.app.show_task_details(task)
        else:
            # Show task details dialog
            self.edit_task(task)

    def create_task(self):
        """Create new task"""
        if not self.require_permission('create_tasks'):
            return

        try:
            # Get required data for dialog
            compliance_areas = []
            team_members = []

            if hasattr(self.app, 'config'):
                compliance_areas = getattr(self.app.config, 'compliance_areas', [])

            if hasattr(self.app, 'compliance_manager'):
                team_members = self.app.compliance_manager.team_manager.get_active_team_members()

            # Show task dialog
            dialog = TaskDialog(
                self.parent_frame,
                task=None,
                compliance_areas=compliance_areas,
                team_members=team_members
            )
            self.track_dialog(dialog)
            self.parent_frame.wait_window(dialog)

            if dialog.result:
                # Create task
                self.save_new_task(dialog.result)

        except Exception as e:
            self.logger.error(f"Error creating task: {e}")
            self.show_error("Create Error", f"Failed to create task: {str(e)}")

    def edit_task(self, task: Any):
        """Edit existing task"""
        if not self.require_permission('edit_tasks'):
            return

        try:
            # Get required data for dialog
            compliance_areas = []
            team_members = []

            if hasattr(self.app, 'config'):
                compliance_areas = getattr(self.app.config, 'compliance_areas', [])

            if hasattr(self.app, 'compliance_manager'):
                team_members = self.app.compliance_manager.team_manager.get_active_team_members()

            # Show task dialog
            dialog = TaskDialog(
                self.parent_frame,
                task=task,
                compliance_areas=compliance_areas,
                team_members=team_members
            )
            self.track_dialog(dialog)
            self.parent_frame.wait_window(dialog)

            if dialog.result:
                # Update task
                self.save_task_changes(task, dialog.result)

        except Exception as e:
            self.logger.error(f"Error editing task: {e}")
            self.show_error("Edit Error", f"Failed to edit task: {str(e)}")

    def save_new_task(self, task_data: Dict[str, Any]):
        """Save new task"""
        try:
            if hasattr(self.app, 'compliance_manager'):
                # Create task through task manager
                self.app.compliance_manager.task_manager.create_task(
                    task_data,
                    created_by=getattr(self.app, 'current_user', 'Unknown')
                )
                self.show_info("Success", "Task created successfully")
                self.refresh_tasks()
            else:
                self.show_error("Configuration Error", "Task manager not available")

        except Exception as e:
            self.logger.error(f"Error saving new task: {e}")
            self.show_error("Save Error", f"Failed to save task: {str(e)}")

    def save_task_changes(self, task: Any, changes: Dict[str, Any]):
        """Save task changes"""
        try:
            if hasattr(self.app, 'compliance_manager'):
                # Update task through task manager
                self.app.compliance_manager.task_manager.update_task(
                    getattr(task, 'key', ''),
                    changes,
                    updated_by=getattr(self.app, 'current_user', 'Unknown')
                )
                self.show_info("Success", "Task updated successfully")
                self.refresh_tasks()
            else:
                self.show_error("Configuration Error", "Task manager not available")

        except Exception as e:
            self.logger.error(f"Error saving task changes: {e}")
            self.show_error("Save Error", f"Failed to save changes: {str(e)}")

    def export_tasks(self):
        """Export tasks to file"""
        if not self.task_table:
            return

        # Get visible tasks
        tasks = self.task_table.get_visible_tasks()

        if not tasks:
            self.show_warning("No Data", "No tasks to export")
            return

        # Ask for file location
        filename = filedialog.asksaveasfilename(
            parent=self.parent_frame,
            title="Export Tasks",
            defaultextension=".xlsx",
            filetypes=[
                ("Excel files", "*.xlsx"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )

        if filename:
            try:
                self.export_tasks_to_file(tasks, filename)
            except Exception as e:
                self.logger.error(f"Export error: {e}")
                self.show_error("Export Error", f"Failed to export: {str(e)}")

    def export_tasks_to_file(self, tasks: List[Any], filename: str):
        """Export tasks to specified file"""
        try:
            # Convert tasks to dataframe
            data = []
            for task in tasks:
                data.append({
                    'Task ID': getattr(task, 'key', ''),
                    'Title': getattr(task, 'title', ''),
                    'Compliance Area': getattr(task, 'compliance_area', ''),
                    'Subcategory': getattr(task, 'subcategory', ''),
                    'Priority': getattr(task, 'priority', ''),
                    'Status': getattr(task, 'status', ''),
                    'Task Setter': getattr(task, 'task_setter', ''),
                    'Allocated To': ', '.join(getattr(task, 'allocated_to', [])),
                    'Manager': getattr(task, 'manager', ''),
                    'Target Date': getattr(task, 'target_date', ''),
                    'Created Date': getattr(task, 'date_logged', ''),
                    'Last Updated': getattr(task, 'modified_date', ''),
                    'Description': getattr(task, 'description', '')
                })

            df = pd.DataFrame(data)

            if filename.endswith('.csv'):
                df.to_csv(filename, index=False)
            else:
                df.to_excel(filename, index=False)

            self.show_info("Export Complete", f"Tasks exported to:\n{filename}")

        except ImportError:
            # Pandas not available, use basic CSV export
            self.export_tasks_basic(data, filename)
        except Exception as e:
            raise e

    def export_tasks_basic(self, data: List[Dict[str, Any]], filename: str):
        """Basic CSV export without pandas"""
        import csv

        if not filename.endswith('.csv'):
            filename = filename.rsplit('.', 1)[0] + '.csv'

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            if data:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)

        self.show_info("Export Complete", f"Tasks exported to:\n{filename}")


class TaskDetailView(BaseView):
    """Task detail view with full task information and actions"""

    def __init__(self, parent_frame: ttk.Frame, app: Any):
        super().__init__(parent_frame, app)
        self.current_task = None
        self.details_panel = None
        self.approval_panel = None
        self.attachment_widget = None

    def show(self):
        """Display task details"""
        super().show()

        # Check if task is provided
        task = self.get_view_data('selected_task') or getattr(self.app, 'selected_task', None)

        if not task:
            self.show_no_task_message()
            return

        self.current_task = task
        self.display_task_details()

    def show_no_task_message(self):
        """Show message when no task is selected"""
        msg_frame = ttk.Frame(self.parent_frame)
        msg_frame.pack(expand=True)

        ttk.Label(
            msg_frame,
            text="No task selected",
            font=UIStyles.FONTS.get_font('heading2')
        ).pack()

        ttk.Label(
            msg_frame,
            text="Please select a task to view details",
            font=UIStyles.FONTS.get_font('normal', 'italic')
        ).pack(pady=10)

        back_btn = ModernButton(
            msg_frame,
            text="Back to Task List",
            icon='arrow-left',
            command=lambda: self.app.show_view('tasks'),
            style_type='primary'
        )
        back_btn.pack(pady=20)

    def display_task_details(self):
        """Display full task details"""
        # Main container
        main_container = ttk.Frame(self.parent_frame)
        main_container.pack(fill='both', expand=True, padx=20, pady=20)

        # Header with back button
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill='x', pady=(0, 20))

        back_btn = ModernButton(
            header_frame,
            text="Back",
            icon='arrow-left',
            command=self.go_back,
            style_type='secondary'
        )
        back_btn.pack(side='left')

        # Title
        title_label = ModernLabel(
            header_frame,
            text=f"Task: {getattr(self.current_task, 'key', 'Unknown')}",
            style_type='heading1'
        )
        title_label.pack(side='left', padx=(20, 0))

        # Action buttons
        if self.check_permission('edit_tasks'):
            action_frame = ttk.Frame(header_frame)
            action_frame.pack(side='right')

            edit_btn = ModernButton(
                action_frame,
                text="Edit",
                icon='edit',
                command=self.edit_task,
                style_type='primary'
            )
            edit_btn.pack(side='left', padx=(0, 5))

            if self.check_permission('delete_tasks'):
                delete_btn = ModernButton(
                    action_frame,
                    text="Delete",
                    icon='trash',
                    command=self.delete_task,
                    style_type='danger'
                )
                delete_btn.pack(side='left')

        # Create scrollable content area
        canvas, scrollable_frame = self.create_scrollable_frame(main_container)

        # Task details panel
        self.details_panel = TaskDetailsPanel(scrollable_frame, self.current_task)
        self.details_panel.pack(fill='both', expand=True, pady=(0, 20))

        # Approval panel if applicable
        if self.should_show_approval_panel():
            self.approval_panel = ApprovalPanel(
                scrollable_frame,
                self.current_task,
                on_approve=self.approve_task,
                on_reject=self.reject_task
            )
            self.approval_panel.pack(fill='x', pady=(0, 20))

        # Attachments
        self.attachment_widget = FileAttachmentWidget(
            scrollable_frame,
            attachments=getattr(self.current_task, 'attachments', []),
            on_add=self.add_attachment,
            on_remove=self.remove_attachment,
            read_only=not self.check_permission('edit_tasks')
        )
        self.attachment_widget.pack(fill='x', pady=(0, 20))

        # Activity log
        self.create_activity_log(scrollable_frame)

    def should_show_approval_panel(self) -> bool:
        """Check if approval panel should be shown"""
        if not self.check_permission('approve_tasks'):
            return False

        status = getattr(self.current_task, 'status', '')
        return status in ['Pending Approval', 'Sent For Approval']

    def create_activity_log(self, parent: ttk.Frame):
        """Create activity log section"""
        log_card = Card(parent, "Activity Log", collapsible=True)
        log_card.pack(fill='x')

        content = log_card.content_frame if hasattr(log_card, 'content_frame') else log_card

        # Get task actions
        actions = getattr(self.current_task, 'actions', [])

        if actions:
            for action in actions[-10:]:  # Show last 10 actions
                self.create_action_item(content, action)
        else:
            ttk.Label(
                content,
                text="No activity recorded",
                font=UIStyles.FONTS.get_font('normal', 'italic')
            ).pack(pady=10)

    def create_action_item(self, parent: ttk.Frame, action: Any):
        """Create single action item"""
        item_frame = ttk.Frame(parent)
        item_frame.pack(fill='x', pady=5, padx=10)

        # Timestamp and user
        info_text = f"{getattr(action, 'timestamp', 'Unknown')} - {getattr(action, 'user', 'Unknown')}"
        info_label = ttk.Label(
            item_frame,
            text=info_text,
            font=UIStyles.FONTS.get_font('small', 'bold')
        )
        info_label.pack(anchor='w')

        # Action details
        details_label = ttk.Label(
            item_frame,
            text=getattr(action, 'details', ''),
            font=UIStyles.FONTS.get_font('small')
        )
        details_label.pack(anchor='w', padx=(20, 0))

    # Action handlers

    def go_back(self):
        """Go back to task list"""
        self.app.show_view('tasks')

    def edit_task(self):
        """Edit current task"""
        task_list_view = TaskListView(self.parent_frame, self.app)
        task_list_view.edit_task(self.current_task)

    def delete_task(self):
        """Delete current task"""
        if self.ask_yes_no(
                "Confirm Delete",
                f"Are you sure you want to delete task {getattr(self.current_task, 'key', 'Unknown')}?"
        ):
            try:
                if hasattr(self.app, 'compliance_manager'):
                    self.app.compliance_manager.task_manager.delete_task(
                        getattr(self.current_task, 'key', ''),
                        deleted_by=getattr(self.app, 'current_user', 'Unknown')
                    )
                    self.show_info("Success", "Task deleted successfully")
                    self.go_back()
            except Exception as e:
                self.logger.error(f"Error deleting task: {e}")
                self.show_error("Delete Error", f"Failed to delete task: {str(e)}")

    def approve_task(self, comments: str):
        """Approve task"""
        try:
            if hasattr(self.app, 'compliance_manager'):
                self.app.compliance_manager.approval_manager.approve_task(
                    getattr(self.current_task, 'key', ''),
                    approved_by=getattr(self.app, 'current_user', 'Unknown'),
                    comments=comments
                )
                self.show_info("Success", "Task approved successfully")
                self.refresh()
        except Exception as e:
            self.logger.error(f"Error approving task: {e}")
            self.show_error("Approval Error", f"Failed to approve task: {str(e)}")

    def reject_task(self, comments: str):
        """Reject task"""
        try:
            if hasattr(self.app, 'compliance_manager'):
                self.app.compliance_manager.approval_manager.reject_task(
                    getattr(self.current_task, 'key', ''),
                    rejected_by=getattr(self.app, 'current_user', 'Unknown'),
                    comments=comments
                )
                self.show_info("Success", "Task rejected")
                self.refresh()
        except Exception as e:
            self.logger.error(f"Error rejecting task: {e}")
            self.show_error("Rejection Error", f"Failed to reject task: {str(e)}")

    def add_attachment(self, files: List[str]):
        """Add attachments to task"""
        # Implementation would depend on file handling system
        self.show_info("Attachments", f"Would add {len(files)} files")

    def remove_attachment(self, attachment: Any):
        """Remove attachment from task"""
        # Implementation would depend on file handling system
        self.show_info("Attachments", "Would remove attachment")