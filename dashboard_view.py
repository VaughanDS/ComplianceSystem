# views/dashboard_view.py
"""
Dashboard view for Compliance Management System
Shows overview and key metrics with proper error handling
"""

import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional

from views import BaseView
from ui.components import (
    ModernFrame, ModernButton, ModernLabel, Card, MetricCard,
    TaskTable, NotificationPanel, QuickActions, ProgressIndicator
)
from ui.styles import UIStyles


class DashboardView(BaseView):
    """Dashboard view implementation with comprehensive metrics display"""

    def __init__(self, parent_frame: ttk.Frame, app: Any):
        super().__init__(parent_frame, app)
        self.scrollable_frame = None
        self.canvas = None

    def show(self):
        """Display the dashboard"""
        super().show()

        try:
            # Create main container with scrolling
            self.canvas, self.scrollable_frame = self.create_scrollable_frame()

            # Title
            title_label = ModernLabel(
                self.scrollable_frame,
                text="Compliance Dashboard",
                style_type='heading1'
            )
            title_label.pack(pady=(20, 20))

            # Show loading indicator
            self.show_progress("Loading dashboard data...")

            # Load dashboard data
            self.load_dashboard_data()

        except Exception as e:
            self.logger.error(f"Error showing dashboard: {e}")
            self.show_error("Dashboard Error", "Failed to load dashboard")
        finally:
            self.hide_progress()

    def load_dashboard_data(self):
        """Load and display dashboard data"""
        try:
            # Check if compliance manager exists
            if not hasattr(self.app, 'compliance_manager'):
                self.show_error("Configuration Error", "Compliance manager not initialized")
                return

            # Get dashboard data
            dashboard_data = self.app.compliance_manager.get_dashboard_data(
                getattr(self.app, 'current_user', 'Unknown')
            )

            # Display sections
            self.create_metrics_section(dashboard_data)
            self.create_quick_actions()
            self.create_task_summary(dashboard_data)
            self.create_notifications()
            self.create_compliance_status(dashboard_data)
            self.create_upcoming_deadlines(dashboard_data)
            self.create_team_performance(dashboard_data)

        except Exception as e:
            self.logger.error(f"Error loading dashboard data: {e}")
            self.show_error("Data Error", f"Failed to load dashboard data: {str(e)}")

    def create_metrics_section(self, data: Dict[str, Any]):
        """Create key metrics cards"""
        metrics_frame = ttk.Frame(self.scrollable_frame)
        metrics_frame.pack(fill='x', pady=(0, 20))

        # Configure grid
        for i in range(4):
            metrics_frame.columnconfigure(i, weight=1)

        # Extract metrics safely
        metrics = data.get('metrics', {})

        # Total Tasks
        total_tasks = metrics.get('total_tasks', 0)
        open_tasks = metrics.get('open_tasks', 0)
        self.create_metric_card(
            metrics_frame,
            title="Total Tasks",
            value=str(total_tasks),
            subtitle=f"{open_tasks} open",
            color=getattr(UIStyles.COLOURS, 'primary', '#007bff'),
            row=0, column=0
        )

        # Critical Tasks
        critical_tasks = metrics.get('critical_tasks', 0)
        self.create_metric_card(
            metrics_frame,
            title="Critical Tasks",
            value=str(critical_tasks),
            subtitle="Require immediate attention",
            color=UIStyles.COLOURS.get('danger', '#dc3545'),
            row=0, column=1
        )

        # Overdue Tasks
        overdue_tasks = metrics.get('overdue_tasks', 0)
        self.create_metric_card(
            metrics_frame,
            title="Overdue Tasks",
            value=str(overdue_tasks),
            subtitle="Past target date",
            color=UIStyles.COLOURS.get('warning', '#ffc107'),
            row=0, column=2
        )

        # Completion Rate
        completion_rate = metrics.get('completion_rate', 0)
        self.create_metric_card(
            metrics_frame,
            title="Completion Rate",
            value=f"{completion_rate:.0f}%",
            subtitle="This month",
            color=UIStyles.COLOURS.get('success', '#28a745'),
            row=0, column=3
        )

    def create_metric_card(self, parent: ttk.Frame, title: str, value: str,
                           subtitle: str, color: str, row: int, column: int):
        """Create a single metric card"""
        try:
            card = MetricCard(
                parent,
                title=title,
                value=value,
                subtitle=subtitle,
                color=color
            )
            card.grid(row=row, column=column, padx=10, pady=5, sticky='nsew')
        except Exception as e:
            self.logger.error(f"Error creating metric card: {e}")

    def create_quick_actions(self):
        """Create quick action buttons"""
        actions_card = Card(self.scrollable_frame, "Quick Actions")
        actions_card.pack(fill='x', pady=(0, 20))

        content = actions_card.content_frame if hasattr(actions_card, 'content_frame') else actions_card

        actions = [
            {
                'text': 'New Task',
                'icon': 'plus',
                'command': self.new_task,
                'style': 'primary'
            },
            {
                'text': 'View All Tasks',
                'icon': 'list',
                'command': lambda: self.app.show_view('tasks'),
                'style': 'secondary'
            },
            {
                'text': 'Generate Report',
                'icon': 'file',
                'command': lambda: self.app.show_view('reports'),
                'style': 'secondary'
            },
            {
                'text': 'Team Overview',
                'icon': 'users',
                'command': lambda: self.app.show_view('team'),
                'style': 'secondary'
            }
        ]

        quick_actions = QuickActions(content, actions)
        quick_actions.pack(fill='x', padx=10, pady=10)

    def create_task_summary(self, data: Dict[str, Any]):
        """Create task summary table"""
        summary_card = Card(self.scrollable_frame, "Recent Tasks")
        summary_card.pack(fill='both', expand=True, pady=(0, 20))

        content = summary_card.content_frame if hasattr(summary_card, 'content_frame') else summary_card

        # Create task table
        task_table = TaskTable(
            content,
            on_select=self.on_task_select,
            on_double_click=self.on_task_double_click
        )
        task_table.pack(fill='both', expand=True, padx=10, pady=10)

        # Load recent tasks
        recent_tasks = data.get('recent_tasks', [])[:10]  # Show only 10 most recent
        if recent_tasks:
            task_table.load_tasks(recent_tasks)
        else:
            # Show empty message
            ttk.Label(
                content,
                text="No recent tasks",
                font=UIStyles.FONTS.get_font('normal', 'italic')
            ).pack(pady=20)

    def create_notifications(self):
        """Create notifications panel"""
        notif_card = Card(self.scrollable_frame, "Recent Notifications", collapsible=True)
        notif_card.pack(fill='x', pady=(0, 20))

        content = notif_card.content_frame if hasattr(notif_card, 'content_frame') else notif_card

        # Create notification panel
        self.notification_panel = NotificationPanel(content)
        self.notification_panel.pack(fill='x', padx=10, pady=10)

        # Subscribe to notifications if service exists
        if hasattr(self.app, 'notification_service'):
            try:
                self.app.notification_service.subscribe(self.on_notification)
            except:
                self.logger.warning("Could not subscribe to notifications")

    def create_compliance_status(self, data: Dict[str, Any]):
        """Create compliance status section"""
        status_card = Card(self.scrollable_frame, "Compliance Status")
        status_card.pack(fill='x', pady=(0, 20))

        content = status_card.content_frame if hasattr(status_card, 'content_frame') else status_card

        # Get compliance metrics safely
        compliance_metrics = data.get('compliance_metrics', {})
        compliance_score = compliance_metrics.get('on_time_completion', 0)

        # Score display
        score_frame = ttk.Frame(content)
        score_frame.pack(pady=10)

        score_label = ttk.Label(
            score_frame,
            text=f"{compliance_score:.0f}%",
            font=('Arial', 36, 'bold')
        )
        score_label.pack()

        # Colour based on score
        if compliance_score >= 80:
            colour = UIStyles.COLOURS.get('success', '#28a745')
        elif compliance_score >= 60:
            colour = UIStyles.COLOURS.get('warning', '#ffc107')
        else:
            colour = UIStyles.COLOURS.get('danger', '#dc3545')

        try:
            score_label.configure(foreground=colour)
        except:
            pass

        # Status text
        ttk.Label(
            content,
            text="Overall Compliance Score",
            font=UIStyles.FONTS.get_font('normal')
        ).pack()

        # Progress bar
        try:
            progress = ttk.Progressbar(
                content,
                value=compliance_score,
                mode='determinate',
                bootstyle=('success' if compliance_score >= 80 else
                           'warning' if compliance_score >= 60 else 'danger')
            )
            progress.pack(fill='x', padx=20, pady=10)
        except:
            # Fallback for standard ttk
            progress = ttk.Progressbar(
                content,
                value=compliance_score,
                mode='determinate'
            )
            progress.pack(fill='x', padx=20, pady=10)

        # Key metrics
        metrics_frame = ttk.Frame(content)
        metrics_frame.pack(fill='x', pady=10)

        # Critical resolution rate
        crit_rate = compliance_metrics.get('critical_resolution_rate', 0)
        ttk.Label(
            metrics_frame,
            text=f"Critical Resolution: {crit_rate:.0f}%",
            font=UIStyles.FONTS.get_font('small')
        ).pack()

        # Average completion time
        avg_days = compliance_metrics.get('average_days_to_complete', 0)
        ttk.Label(
            metrics_frame,
            text=f"Avg. Completion Time: {avg_days:.1f} days",
            font=UIStyles.FONTS.get_font('small')
        ).pack()

    def create_upcoming_deadlines(self, data: Dict[str, Any]):
        """Create upcoming deadlines section"""
        deadlines_card = Card(self.scrollable_frame, "Upcoming Deadlines")
        deadlines_card.pack(fill='x', pady=(0, 20))

        content = deadlines_card.content_frame if hasattr(deadlines_card, 'content_frame') else deadlines_card

        # Get upcoming tasks
        upcoming_tasks = data.get('upcoming_deadlines', [])[:5]  # Show only 5

        if upcoming_tasks:
            for task in upcoming_tasks:
                self.create_deadline_item(content, task)
        else:
            ttk.Label(
                content,
                text="No upcoming deadlines",
                font=UIStyles.FONTS.get_font('normal', 'italic')
            ).pack(pady=20)

    def create_deadline_item(self, parent: ttk.Frame, task: Any):
        """Create a single deadline item"""
        item_frame = ttk.Frame(parent)
        item_frame.pack(fill='x', pady=5, padx=10)

        # Task info
        task_info = ttk.Label(
            item_frame,
            text=f"{getattr(task, 'key', 'Unknown')} - {getattr(task, 'title', 'Untitled')}",
            font=UIStyles.FONTS.get_font('small')
        )
        task_info.pack(side='left')

        # Due date
        target_date = getattr(task, 'target_date', None)
        if target_date:
            try:
                due_date = datetime.strptime(target_date, "%Y-%m-%d")
                days_until = (due_date.date() - date.today()).days

                if days_until < 0:
                    due_text = f"Overdue by {abs(days_until)} days"
                    colour = UIStyles.COLOURS.get('danger', '#dc3545')
                elif days_until == 0:
                    due_text = "Due today"
                    colour = UIStyles.COLOURS.get('warning', '#ffc107')
                else:
                    due_text = f"Due in {days_until} days"
                    colour = UIStyles.COLOURS.get('info', '#17a2b8')

                due_label = ttk.Label(
                    item_frame,
                    text=due_text,
                    font=UIStyles.FONTS.get_font('small'),
                    foreground=colour
                )
                due_label.pack(side='right')
            except:
                pass

    def create_team_performance(self, data: Dict[str, Any]):
        """Create team performance section"""
        if not self.check_permission('view_team_performance'):
            return

        perf_card = Card(self.scrollable_frame, "Team Performance")
        perf_card.pack(fill='x', pady=(0, 20))

        content = perf_card.content_frame if hasattr(perf_card, 'content_frame') else perf_card

        # Get team metrics
        team_performance = data.get('team_performance', [])[:5]  # Top 5 performers

        if team_performance:
            # Create header
            header_frame = ttk.Frame(content)
            header_frame.pack(fill='x', padx=10, pady=(10, 5))

            ttk.Label(
                header_frame,
                text="Team Member",
                font=UIStyles.FONTS.get_font('small', 'bold')
            ).pack(side='left')

            ttk.Label(
                header_frame,
                text="Tasks Completed",
                font=UIStyles.FONTS.get_font('small', 'bold')
            ).pack(side='right')

            # Create performance items
            for member_data in team_performance:
                self.create_performance_item(content, member_data)
        else:
            ttk.Label(
                content,
                text="No performance data available",
                font=UIStyles.FONTS.get_font('normal', 'italic')
            ).pack(pady=20)

    def create_performance_item(self, parent: ttk.Frame, member_data: Dict[str, Any]):
        """Create a single performance item"""
        item_frame = ttk.Frame(parent)
        item_frame.pack(fill='x', pady=2, padx=10)

        # Member name
        name_label = ttk.Label(
            item_frame,
            text=member_data.get('name', 'Unknown'),
            font=UIStyles.FONTS.get_font('small')
        )
        name_label.pack(side='left')

        # Completion count
        count_label = ttk.Label(
            item_frame,
            text=str(member_data.get('completed_count', 0)),
            font=UIStyles.FONTS.get_font('small')
        )
        count_label.pack(side='right')

    # Event handlers

    def new_task(self):
        """Create new task"""
        if self.require_permission('create_tasks'):
            if hasattr(self.app, 'new_task'):
                self.app.new_task()
            else:
                self.app.show_view('tasks')

    def on_task_select(self, task: Any):
        """Handle task selection"""
        self.set_view_data('selected_task', task)
        self.update_status(f"Selected: {getattr(task, 'key', 'Unknown')}")

    def on_task_double_click(self, task: Any):
        """Handle task double-click"""
        if hasattr(self.app, 'show_task_details'):
            self.app.show_task_details(task)
        else:
            self.show_info("Task Details", f"Task: {getattr(task, 'title', 'Unknown')}")

    def on_notification(self, notification: Dict[str, Any]):
        """Handle incoming notification"""
        if self.notification_panel:
            self.notification_panel.add_notification(notification)

    def refresh(self):
        """Refresh dashboard data"""
        if self.is_visible:
            self.show()