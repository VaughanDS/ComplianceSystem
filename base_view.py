# views/base_view.py
"""
Enhanced base view class for all UI views
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Optional, Dict, List, Callable
from abc import ABC, abstractmethod
import logging

from utils.logger import get_logger
from utils.decorators import log_execution, handle_exceptions


class BaseView(ABC):
    """Enhanced base class for all views with common functionality"""

    def __init__(self, parent_frame: ttk.Frame, app: Any):
        """
        Initialize base view

        Args:
            parent_frame: Parent frame to render view in
            app: Reference to main application
        """
        self.parent_frame = parent_frame
        self.app = app
        self.widgets = {}
        self.is_visible = False
        self.logger = get_logger(self.__class__.__name__)

        # Store references to ongoing operations
        self._active_threads = []
        self._active_dialogs = []

        # View-specific data
        self._view_data = {}

    @log_execution()
    def clear(self):
        """Clear all widgets from the view with proper cleanup"""
        try:
            # Cancel any active threads
            self._cleanup_threads()

            # Close any open dialogs
            self._cleanup_dialogs()

            # Clear all widgets from the parent frame
            for widget in self.parent_frame.winfo_children():
                try:
                    # Special handling for canvas widgets
                    if isinstance(widget, tk.Canvas):
                        widget.unbind_all("<MouseWheel>")

                    # Destroy the widget
                    widget.destroy()
                except tk.TclError as e:
                    # Widget was already destroyed or invalid
                    self.logger.debug(f"Widget cleanup error: {e}")
                    pass

            # Clear the widgets dictionary
            self.widgets.clear()

            # Clear view data
            self._view_data.clear()

            # Mark as not visible
            self.is_visible = False

        except Exception as e:
            self.logger.error(f"Error during view cleanup: {e}")

    @abstractmethod
    def show(self):
        """
        Display the view - must be implemented by subclasses
        """
        self.clear()
        self.is_visible = True
        self.logger.info(f"Showing {self.__class__.__name__}")

    def refresh(self):
        """Refresh the view with latest data"""
        if self.is_visible:
            self.logger.debug(f"Refreshing {self.__class__.__name__}")
            self.show()

    def hide(self):
        """Hide the view"""
        self.clear()
        self.is_visible = False
        self.logger.debug(f"Hiding {self.__class__.__name__}")

    # Status and messaging methods

    def update_status(self, message: str):
        """Update application status bar"""
        if hasattr(self.app, 'update_status'):
            self.app.update_status(message)

    def show_error(self, title: str, message: str):
        """Show error dialog"""
        self.logger.error(f"{title}: {message}")
        messagebox.showerror(title, message)

    def show_info(self, title: str, message: str):
        """Show info dialog"""
        self.logger.info(f"{title}: {message}")
        messagebox.showinfo(title, message)

    def show_warning(self, title: str, message: str):
        """Show warning dialog"""
        self.logger.warning(f"{title}: {message}")
        messagebox.showwarning(title, message)

    def ask_yes_no(self, title: str, message: str) -> bool:
        """Show yes/no dialog"""
        result = messagebox.askyesno(title, message)
        self.logger.debug(f"Yes/No dialog '{title}': {result}")
        return result

    def ask_ok_cancel(self, title: str, message: str) -> bool:
        """Show OK/Cancel dialog"""
        result = messagebox.askokcancel(title, message)
        self.logger.debug(f"OK/Cancel dialog '{title}': {result}")
        return result

    # Widget management methods

    def add_widget(self, name: str, widget: tk.Widget):
        """
        Add widget to internal registry

        Args:
            name: Widget identifier
            widget: Widget instance
        """
        self.widgets[name] = widget

    def get_widget(self, name: str) -> Optional[tk.Widget]:
        """
        Get widget by name

        Args:
            name: Widget identifier

        Returns:
            Widget instance or None
        """
        return self.widgets.get(name)

    def remove_widget(self, name: str):
        """
        Remove widget from registry and destroy it

        Args:
            name: Widget identifier
        """
        if name in self.widgets:
            try:
                self.widgets[name].destroy()
            except:
                pass
            del self.widgets[name]

    # Data management methods

    def set_view_data(self, key: str, value: Any):
        """
        Store view-specific data

        Args:
            key: Data key
            value: Data value
        """
        self._view_data[key] = value

    def get_view_data(self, key: str, default: Any = None) -> Any:
        """
        Retrieve view-specific data

        Args:
            key: Data key
            default: Default value if key not found

        Returns:
            Data value or default
        """
        return self._view_data.get(key, default)

    # Thread management methods

    def run_in_background(self, func: Callable, *args, **kwargs):
        """
        Run function in background thread

        Args:
            func: Function to run
            args: Function arguments
            kwargs: Function keyword arguments
        """
        import threading

        def wrapped_func():
            try:
                func(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Background task error: {e}")
                self.parent_frame.after(0, lambda: self.show_error(
                    "Background Task Error", str(e)
                ))
            finally:
                # Remove from active threads
                if thread in self._active_threads:
                    self._active_threads.remove(thread)

        thread = threading.Thread(target=wrapped_func, daemon=True)
        self._active_threads.append(thread)
        thread.start()

    def _cleanup_threads(self):
        """Clean up active threads"""
        for thread in self._active_threads:
            if thread.is_alive():
                self.logger.debug(f"Active thread still running: {thread.name}")
        self._active_threads.clear()

    # Dialog management methods

    def track_dialog(self, dialog: tk.Toplevel):
        """
        Track an open dialog

        Args:
            dialog: Dialog window
        """
        self._active_dialogs.append(dialog)

    def _cleanup_dialogs(self):
        """Close all open dialogs"""
        for dialog in self._active_dialogs:
            try:
                if dialog.winfo_exists():
                    dialog.destroy()
            except:
                pass
        self._active_dialogs.clear()

    # Common UI creation methods

    def create_scrollable_frame(self, parent: tk.Widget = None) -> tuple:
        """
        Create a scrollable frame

        Args:
            parent: Parent widget (defaults to parent_frame)

        Returns:
            Tuple of (canvas, scrollable_frame)
        """
        if parent is None:
            parent = self.parent_frame

        # Create canvas
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack widgets
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", on_mousewheel)

        return canvas, scrollable_frame

    def create_labeled_frame(self, parent: tk.Widget, title: str, **kwargs) -> ttk.LabelFrame:
        """
        Create a labeled frame

        Args:
            parent: Parent widget
            title: Frame title
            kwargs: Additional frame arguments

        Returns:
            LabelFrame widget
        """
        frame = ttk.LabelFrame(parent, text=title, **kwargs)
        return frame

    # Permission checking methods

    def check_permission(self, permission: str) -> bool:
        """
        Check if user has permission

        Args:
            permission: Permission to check

        Returns:
            True if user has permission
        """
        return permission in getattr(self.app, 'user_permissions', [])

    def require_permission(self, permission: str) -> bool:
        """
        Check permission and show error if missing

        Args:
            permission: Required permission

        Returns:
            True if user has permission
        """
        if not self.check_permission(permission):
            self.show_error(
                "Permission Denied",
                f"You don't have permission to {permission.replace('_', ' ')}"
            )
            return False
        return True

    # Validation helper methods

    @staticmethod
    def validate_required_fields(fields: Dict[str, tk.Widget]) -> List[str]:
        """
        Validate required fields are filled

        Args:
            fields: Dictionary of field_name: widget

        Returns:
            List of empty field names
        """
        empty_fields = []

        for field_name, widget in fields.items():
            value = None

            if isinstance(widget, tk.Entry):
                value = widget.get().strip()
            elif isinstance(widget, tk.Text):
                value = widget.get("1.0", "end-1c").strip()
            elif hasattr(widget, 'get'):
                value = widget.get()

            if not value:
                empty_fields.append(field_name)

        return empty_fields

    # Event handling helpers

    def bind_shortcuts(self, shortcuts: Dict[str, Callable]):
        """
        Bind keyboard shortcuts

        Args:
            shortcuts: Dictionary of key_sequence: callback
        """
        for key_sequence, callback in shortcuts.items():
            self.parent_frame.bind_all(key_sequence, lambda e, cb=callback: cb())

    def unbind_shortcuts(self, shortcuts: List[str]):
        """
        Unbind keyboard shortcuts

        Args:
            shortcuts: List of key sequences to unbind
        """
        for key_sequence in shortcuts:
            self.parent_frame.unbind_all(key_sequence)

    # Cleanup method

    def cleanup(self):
        """Perform cleanup when view is destroyed"""
        self.clear()
        self.logger.debug(f"Cleaned up {self.__class__.__name__}")