# ui/app.py
"""
Main application GUI module - Fixed version
"""

import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox
from tkinter import LEFT, RIGHT, TOP, BOTTOM, BOTH, X, Y, TRUE, FALSE
import threading
import queue
import time
from typing import Dict, Any, Optional
import os

from config.settings import AppConfig, get_config
from business.compliance_manager import ComplianceManager
from services.notification_service import NotificationService
from services.export_service import ExportService
from data.data_manager import DataManager
from ui.styles import UIStyles, get_theme_manager
from views.dashboard_view import DashboardView
from views.task_views import TaskListView
from views.team_view import TeamView
from views.reports_view import ReportsView
from views.legislation_view import LegislationView
from views.admin_view import AdminView
from utils.logger import get_logger

logger = get_logger(__name__)


class ComplianceApp:
    """Main application class"""

    def __init__(self):
        """Initialize application"""
        try:
            # Initialize config first
            self.config = get_config()

            # Initialize root window
            self.root = tk.Tk()
            self.root.withdraw()  # Hide until ready

            # Initialize other attributes
            self.compliance_manager = None
            self.notification_service = None
            self.export_service = None
            self.data_manager = None

            # User session
            self.current_user = ""
            self.current_user_email = ""
            self.user_permissions = []

            # UI state
            self.current_view = None
            self.views = {}
            self.queue = queue.Queue()
            self.running = True
            self.refresh_thread = None
            self.theme_manager = None

            # Call setup method
            self.setup_app()

        except Exception as e:
            logger.error(f"Failed to initialize app: {e}")
            messagebox.showerror("Initialization Error", f"Failed to start application: {str(e)}")
            if hasattr(self, 'root'):
                self.root.destroy()
            raise

    def setup_app(self):
        """Setup application components"""
        try:
            # Configure root window
            self.root.title(f"{self.config.app_name} v{self.config.version}")
            self.root.geometry(self.config.window_size)
            self.root.minsize(800, 600)

            # Setup theme manager - FIXED
            self.theme_manager = get_theme_manager()
            # Apply theme using ttkbootstrap if available
            try:
                import ttkbootstrap as tb
                style = tb.Style(theme='darkly')
                self.root = style.master
            except:
                # Fallback to standard ttk
                style = ttk.Style()
                style.theme_use('clam')

            # Initialize services
            self.initialize_services()

            # Get user info first
            self.get_user_info()

            # Create UI components
            self.create_ui()

            # Initialize views
            self.initialize_views()

            # Show dashboard
            self.show_view('dashboard')

            # Start background tasks
            self.start_background_tasks()

            # Show window
            self.root.deiconify()

            logger.info("Application initialized successfully")

        except Exception as e:
            logger.error(f"Failed to setup application: {e}")
            messagebox.showerror("Setup Error", f"Failed to initialize application:\n{str(e)}")
            if hasattr(self, 'root'):
                self.root.destroy()
            raise

    def initialize_services(self):
        """Initialize backend services"""
        try:
            # Create data manager
            self.data_manager = DataManager()
            logger.info("Data manager initialized")

            # Create compliance manager
            self.compliance_manager = ComplianceManager(self.data_manager)
            logger.info("Compliance manager initialized")

            # Initialize notification service
            self.notification_service = NotificationService()
            logger.info("Notification service initialized")

            # Initialize export service
            self.export_service = ExportService()
            logger.info("Export service initialized")

        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            raise

    def get_user_info(self):
        """Get user information on startup"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Welcome to Compliance Manager")
        dialog.geometry("500x400")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - dialog.winfo_width()) // 2
        y = (dialog.winfo_screenheight() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")

        # Create form
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text="Compliance Management System",
                  font=('Arial', 16, 'bold')).pack(pady=(0, 20))

        ttk.Label(frame, text="Please enter your details to continue:",
                  font=('Arial', 11)).pack(pady=(0, 15))

        # Get team members
        try:
            team_members = self.compliance_manager.team_manager.get_active_team_members()
            team_names = [m.name for m in team_members]
        except:
            team_members = []
            team_names = []

        # Name field
        name_frame = ttk.Frame(frame)
        name_frame.pack(fill='x', pady=5)
        ttk.Label(name_frame, text="Name:", width=10).pack(side='left')

        name_var = tk.StringVar()
        if team_names:
            name_combo = ttk.Combobox(name_frame, textvariable=name_var,
                                      values=team_names, width=35)
            name_combo.pack(side='left', fill='x', expand=True)

            # Auto-fill email when name is selected
            def on_name_selected(event=None):
                selected_name = name_var.get()
                for member in team_members:
                    if member.name == selected_name:
                        email_var.set(member.email)
                        break

            name_combo.bind('<<ComboboxSelected>>', on_name_selected)
        else:
            name_entry = ttk.Entry(name_frame, textvariable=name_var, width=35)
            name_entry.pack(side='left', fill='x', expand=True)

        # Email field
        email_frame = ttk.Frame(frame)
        email_frame.pack(fill='x', pady=5)
        ttk.Label(email_frame, text="Email:", width=10).pack(side='left')

        email_var = tk.StringVar()
        email_entry = ttk.Entry(email_frame, textvariable=email_var, width=35)
        email_entry.pack(side='left', fill='x', expand=True)

        # Message label
        msg_label = ttk.Label(frame, text="", foreground='red')
        msg_label.pack(pady=10)

        result = {'success': False}

        def save_and_continue():
            name = name_var.get().strip()
            email = email_var.get().strip()

            if not name:
                msg_label.config(text="Please enter your name")
                return

            if not email:
                msg_label.config(text="Please enter your email")
                return

            if '@' not in email or '.' not in email.split('@')[1]:
                msg_label.config(text="Please enter a valid email address")
                return

            # Check if user exists
            user_member = None
            for member in team_members:
                if member.email.lower() == email.lower():
                    user_member = member
                    break

            if not user_member and team_members:
                # Ask if they want to add themselves
                response = messagebox.askyesno(
                    "New User",
                    "You are not in the team database.\n\n"
                    "Would you like to add yourself as a team member?"
                )

                if response:
                    # Add to team
                    from core.models import TeamMember
                    new_member = TeamMember(
                        name=name,
                        email=email,
                        department="General",
                        role="Team Member",
                        active=True
                    )

                    success, message, member = self.compliance_manager.team_manager.create_team_member(
                        new_member.to_dict(), name
                    )

                    if success:
                        user_member = member
                    else:
                        msg_label.config(text=f"Error: {message}")
                        return

            # Set user info
            self.current_user = name
            self.current_user_email = email

            # Set permissions based on role
            if user_member:
                role_permissions = {
                    'Admin': ['view_all_tasks', 'create_tasks', 'edit_tasks',
                              'delete_tasks', 'view_all_team', 'manage_team',
                              'view_reports', 'admin'],
                    'Compliance Manager': ['view_all_tasks', 'create_tasks',
                                           'edit_tasks', 'view_all_team',
                                           'manage_team', 'view_reports'],
                    'Compliance Officer': ['view_all_tasks', 'create_tasks',
                                           'edit_tasks', 'view_reports'],
                    'Team Lead': ['view_department_tasks', 'create_tasks',
                                  'edit_department_tasks', 'view_reports'],
                    'Team Member': ['view_assigned_tasks', 'edit_assigned_tasks']
                }

                self.user_permissions = role_permissions.get(
                    user_member.role,
                    ['view_assigned_tasks', 'create_tasks']
                )
            else:
                # Default permissions
                self.user_permissions = ['view_assigned_tasks', 'create_tasks']

            result['success'] = True
            dialog.destroy()

        def cancel():
            dialog.destroy()
            self.root.destroy()

        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=20)

        ttk.Button(button_frame, text="Continue", command=save_and_continue,
                   width=15).pack(side='left', padx=5)

        ttk.Button(button_frame, text="Exit", command=cancel,
                   width=15).pack(side='left', padx=5)

        # Bind Enter key
        email_entry.bind('<Return>', lambda e: save_and_continue())

        # Focus
        if team_names:
            name_combo.focus()
        else:
            name_entry.focus()

        dialog.wait_window()

        if not result['success']:
            self.root.destroy()
            raise SystemExit()

    def create_ui(self):
        """Create main UI components"""
        # Main container
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=BOTH, expand=TRUE)

        # Navigation bar
        self.create_navigation_bar()

        # Content area
        self.content_frame = ttk.Frame(self.main_container)
        self.content_frame.pack(fill=BOTH, expand=TRUE)

        # Status bar
        self.create_status_bar()

    def create_navigation_bar(self):
        """Create navigation bar"""
        nav_frame = ttk.Frame(self.main_container, relief='solid', borderwidth=1)
        nav_frame.pack(fill=X, padx=5, pady=5)

        # Logo/Title
        title_label = ttk.Label(nav_frame, text=self.config.app_name,
                                font=('Arial', 14, 'bold'))
        title_label.pack(side=LEFT, padx=10)

        # Navigation buttons
        nav_items = [
            ("Dashboard", 'dashboard'),
            ("Tasks", 'tasks'),
            ("Team", 'team'),
            ("Reports", 'reports'),
            ("Legislation", 'legislation')
        ]

        for label, view_name in nav_items:
            btn = ttk.Button(
                nav_frame,
                text=label,
                command=lambda v=view_name: self.show_view(v)
            )
            btn.pack(side=LEFT, padx=5)

        # User info
        user_frame = ttk.Frame(nav_frame)
        user_frame.pack(side=RIGHT, padx=10)

        ttk.Label(user_frame, text=f"User: {self.current_user}",
                  font=('Arial', 9)).pack()
        ttk.Label(user_frame, text=self.current_user_email,
                  font=('Arial', 8)).pack()

    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(side=BOTTOM, fill=X)

        # Status text
        self.status_text = tk.StringVar(value="Ready")
        status_label = ttk.Label(self.status_bar, textvariable=self.status_text)
        status_label.pack(side=LEFT, padx=10)

        # Version
        version_label = ttk.Label(self.status_bar, text=f"v{self.config.version}")
        version_label.pack(side=RIGHT, padx=10)

    def initialize_views(self):
        """Initialize all views"""
        self.views = {
            'dashboard': DashboardView(self.content_frame, self),
            'tasks': TaskListView(self.content_frame, self),
            'team': TeamView(self.content_frame, self),
            'reports': ReportsView(self.content_frame, self),
            'legislation': LegislationView(self.content_frame, self)
        }

        # Add admin view if permitted
        if 'admin' in self.user_permissions:
            self.views['admin'] = AdminView(self.content_frame, self)

    def show_view(self, view_name: str, *args, **kwargs):
        """Show specified view"""
        if view_name in self.views:
            # Clear current view
            for widget in self.content_frame.winfo_children():
                widget.destroy()

            # Update current view
            self.current_view = view_name

            # Show new view
            self.views[view_name].show(*args, **kwargs)

            # Update status
            self.update_status(f"Viewing: {view_name.title()}")

    def update_status(self, message: str):
        """Update status bar"""
        self.status_text.set(message)

    def start_background_tasks(self):
        """Start background tasks"""

        # Auto-refresh thread
        def auto_refresh():
            while self.running:
                try:
                    # Check for data changes every 30 seconds
                    time.sleep(30)

                    if self.compliance_manager.check_for_changes():
                        self.queue.put(('refresh', None))

                except Exception as e:
                    logger.error(f"Auto-refresh error: {e}")

        self.refresh_thread = threading.Thread(target=auto_refresh, daemon=True)
        self.refresh_thread.start()

        # Process queue
        self.process_queue()

    def process_queue(self):
        """Process background task queue"""
        try:
            while True:
                task, data = self.queue.get_nowait()

                if task == 'refresh':
                    self.refresh_current_view()
                elif task == 'notification':
                    self.show_notification(data)

        except queue.Empty:
            pass

        if self.running:
            self.root.after(1000, self.process_queue)

    def refresh_current_view(self):
        """Refresh current view"""
        if self.current_view and self.current_view in self.views:
            try:
                self.views[self.current_view].refresh()
            except:
                pass

    def show_notification(self, message: str):
        """Show notification"""
        self.update_status(f"📢 {message}")

    def on_closing(self):
        """Handle application closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.running = False
            self.root.destroy()

    def run(self):
        """Run the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()


def main():
    """Main entry point"""
    try:
        app = ComplianceApp()
        app.run()
    except Exception as e:
        logger.error(f"Application error: {e}")
        messagebox.showerror("Application Error", f"Failed to start: {str(e)}")


if __name__ == "__main__":
    main()