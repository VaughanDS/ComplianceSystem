# ui/components/dialogs.py
"""
Dialog windows for the Compliance Management System
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from datetime import datetime, date, timedelta
from typing import Optional, Callable, List, Dict, Any, Tuple
from pathlib import Path
import re
import webbrowser

from ui.styles import UIStyles, get_theme_manager
from ui.components.base_components import (
    ModernFrame, ModernButton, ModernEntry, ModernLabel,
    DatePicker, Card, SearchBar
)

# Module-level email pattern - Fixed with proper regex
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$'


class BaseDialog(tb.Toplevel):
    """Base class for all dialog windows"""

    def __init__(self, parent, title: str, width: int = 600, height: int = 400):
        super().__init__(parent)

        self.title(title)
        self.geometry(f"{width}x{height}")

        # Centre on parent
        self.transient(parent)
        self.grab_set()

        # Result
        self.result = None

        # Configure close behaviour
        self.protocol("WM_DELETE_WINDOW", self.cancel)

        # Create main frame
        self.main_frame = ttk.Frame(self, padding=20)
        self.main_frame.pack(fill=BOTH, expand=TRUE)

        # Create content
        self.create_content()

        # Create buttons
        self.create_buttons()

        # Centre window
        self.centre_window()

    def create_content(self):
        """Create dialog content - to be overridden"""
        pass

    def create_buttons(self):
        """Create dialog buttons"""
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(side=BOTTOM, fill=X, pady=(20, 0))

        # Cancel button
        cancel_btn = ModernButton(
            button_frame,
            text="Cancel",
            command=self.cancel,
            style_type='secondary'
        )
        cancel_btn.pack(side=RIGHT, padx=(5, 0))

        # OK button
        ok_btn = ModernButton(
            button_frame,
            text="OK",
            command=self.ok,
            style_type='primary'
        )
        ok_btn.pack(side=RIGHT)

    def centre_window(self):
        """Centre dialog on parent"""
        self.update_idletasks()

        # Get parent position
        parent_x = self.master.winfo_x()
        parent_y = self.master.winfo_y()
        parent_width = self.master.winfo_width()
        parent_height = self.master.winfo_height()

        # Get dialog size
        dialog_width = self.winfo_width()
        dialog_height = self.winfo_height()

        # Calculate position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2

        # Set position
        self.geometry(f"+{x}+{y}")

    def ok(self):
        """OK button handler - to be overridden"""
        self.result = True
        self.destroy()

    def cancel(self):
        """Cancel button handler"""
        self.result = None
        self.destroy()


class TaskDialog(tk.Toplevel):
    """Dialog for creating/editing tasks"""

    def __init__(self, parent, task=None, compliance_areas=None, team_members=None):
        super().__init__(parent)
        self.task = task
        self.compliance_areas = compliance_areas or []
        self.team_members = team_members or []
        self.result = None

        self.title("New Task" if task is None else "Edit Task")
        self.geometry("600x500")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        self.center_window()

    def create_widgets(self):
        """Create dialog widgets"""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill='both', expand=True)

        # Title
        ttk.Label(main_frame, text="Title:").grid(row=0, column=0, sticky='w', pady=5)
        self.title_var = tk.StringVar(value=getattr(self.task, 'title', ''))
        ttk.Entry(main_frame, textvariable=self.title_var, width=50).grid(row=0, column=1, pady=5)

        # Compliance Area
        ttk.Label(main_frame, text="Compliance Area:").grid(row=1, column=0, sticky='w', pady=5)
        self.area_var = tk.StringVar(value=getattr(self.task, 'compliance_area', ''))
        area_combo = ttk.Combobox(main_frame, textvariable=self.area_var, values=self.compliance_areas, width=47)
        area_combo.grid(row=1, column=1, pady=5)

        # Priority
        ttk.Label(main_frame, text="Priority:").grid(row=2, column=0, sticky='w', pady=5)
        self.priority_var = tk.StringVar(value=getattr(self.task, 'priority', 'Medium'))
        priority_combo = ttk.Combobox(main_frame, textvariable=self.priority_var,
                                      values=['Critical', 'High', 'Medium', 'Low'], width=47)
        priority_combo.grid(row=2, column=1, pady=5)

        # Task Setter
        ttk.Label(main_frame, text="Task Setter:").grid(row=3, column=0, sticky='w', pady=5)
        self.setter_var = tk.StringVar(value=getattr(self.task, 'task_setter', ''))
        setter_combo = ttk.Combobox(main_frame, textvariable=self.setter_var,
                                    values=[m.name for m in self.team_members], width=47)
        setter_combo.grid(row=3, column=1, pady=5)

        # Description
        ttk.Label(main_frame, text="Description:").grid(row=4, column=0, sticky='nw', pady=5)
        self.description_text = tk.Text(main_frame, width=50, height=6)
        self.description_text.grid(row=4, column=1, pady=5)
        if self.task:
            self.description_text.insert('1.0', getattr(self.task, 'description', ''))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Save", command=self.save).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side='left', padx=5)

    def center_window(self):
        """Center the dialog on screen"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def save(self):
        """Save the task"""
        if not self.title_var.get().strip():
            messagebox.showerror("Error", "Title is required")
            return

        self.result = {
            'title': self.title_var.get().strip(),
            'compliance_area': self.area_var.get(),
            'priority': self.priority_var.get(),
            'task_setter': self.setter_var.get(),
            'description': self.description_text.get('1.0', 'end-1c'),
            'status': 'Open'
        }
        self.destroy()

    def cancel(self):
        """Cancel the dialog"""
        self.result = None
        self.destroy()


class TeamMemberDialog(tk.Toplevel):
    """Dialog for creating/editing team members"""

    def __init__(self, parent, member=None):
        super().__init__(parent)
        self.member = member
        self.result = None

        self.title("New Team Member" if member is None else "Edit Team Member")
        self.geometry("500x400")
        self.transient(parent)
        self.grab_set()

        self.create_widgets()
        self.center_window()

    def create_widgets(self):
        """Create dialog widgets"""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill='both', expand=True)

        # Name
        ttk.Label(main_frame, text="Name:").grid(row=0, column=0, sticky='w', pady=5)
        self.name_var = tk.StringVar(value=getattr(self.member, 'name', ''))
        ttk.Entry(main_frame, textvariable=self.name_var, width=40).grid(row=0, column=1, pady=5)

        # Email
        ttk.Label(main_frame, text="Email:").grid(row=1, column=0, sticky='w', pady=5)
        self.email_var = tk.StringVar(value=getattr(self.member, 'email', ''))
        ttk.Entry(main_frame, textvariable=self.email_var, width=40).grid(row=1, column=1, pady=5)

        # Department
        ttk.Label(main_frame, text="Department:").grid(row=2, column=0, sticky='w', pady=5)
        self.dept_var = tk.StringVar(value=getattr(self.member, 'department', ''))
        dept_combo = ttk.Combobox(main_frame, textvariable=self.dept_var,
                                  values=['HR', 'IT', 'Finance', 'Operations', 'Legal'], width=37)
        dept_combo.grid(row=2, column=1, pady=5)

        # Role
        ttk.Label(main_frame, text="Role:").grid(row=3, column=0, sticky='w', pady=5)
        self.role_var = tk.StringVar(value=getattr(self.member, 'role', ''))
        role_combo = ttk.Combobox(main_frame, textvariable=self.role_var,
                                  values=['Manager', 'Senior', 'Junior', 'Consultant'], width=37)
        role_combo.grid(row=3, column=1, pady=5)

        # Location
        ttk.Label(main_frame, text="Location:").grid(row=4, column=0, sticky='w', pady=5)
        self.location_var = tk.StringVar(value=getattr(self.member, 'location', ''))
        ttk.Entry(main_frame, textvariable=self.location_var, width=40).grid(row=4, column=1, pady=5)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Save", command=self.save).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side='left', padx=5)

    def center_window(self):
        """Center the dialog on screen"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def save(self):
        """Save the team member"""
        if not self.name_var.get().strip() or not self.email_var.get().strip():
            messagebox.showerror("Error", "Name and email are required")
            return

        self.result = {
            'name': self.name_var.get().strip(),
            'email': self.email_var.get().strip(),
            'department': self.dept_var.get(),
            'role': self.role_var.get(),
            'location': self.location_var.get(),
            'active': True
        }
        self.destroy()

    def cancel(self):
        """Cancel the dialog"""
        self.result = None
        self.destroy()


class ConfirmDialog(BaseDialog):
    """Confirmation dialog"""

    def __init__(self, parent, title: str, message: str,
                 confirm_text: str = "OK", cancel_text: str = "Cancel"):
        self.message = message
        self.confirm_text = confirm_text
        self.cancel_text = cancel_text
        super().__init__(parent, title, width=400, height=200)

    def create_content(self):
        """Create confirmation message"""
        # Icon
        icon_label = ttk.Label(
            self.main_frame,
            text=UIStyles.ICONS.get('question', '?'),
            font=('', 24)
        )
        icon_label.pack(pady=(0, 10))

        # Message
        msg_label = ttk.Label(
            self.main_frame,
            text=self.message,
            wraplength=350
        )
        msg_label.pack(pady=(0, 20))

    def create_buttons(self):
        """Create dialog buttons"""
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(side=BOTTOM, fill=X, pady=(20, 0))

        # Cancel button
        cancel_btn = ModernButton(
            button_frame,
            text=self.cancel_text,
            command=self.cancel,
            style_type='secondary'
        )
        cancel_btn.pack(side=RIGHT, padx=(5, 0))

        # Confirm button
        confirm_btn = ModernButton(
            button_frame,
            text=self.confirm_text,
            command=self.ok,
            style_type='primary'
        )
        confirm_btn.pack(side=RIGHT)


class ProgressDialog(BaseDialog):
    """Progress dialog with cancellable progress bar"""

    def __init__(self, parent, title: str = "Processing...",
                 message: str = "Please wait...", cancellable: bool = False):
        self.message = message
        self.cancellable = cancellable
        self.cancelled = False
        super().__init__(parent, title, width=400, height=200)

    def create_content(self):
        """Create progress content"""
        # Message
        msg_label = ttk.Label(
            self.main_frame,
            text=self.message
        )
        msg_label.pack(pady=(0, 20))

        # Progress bar
        self.progress = ttk.Progressbar(
            self.main_frame,
            mode='indeterminate',
            length=300
        )
        self.progress.pack(pady=(0, 20))
        self.progress.start(10)

        # Status label
        self.status_var = tk.StringVar(value="")
        self.status_label = ttk.Label(
            self.main_frame,
            textvariable=self.status_var
        )
        self.status_label.pack()

    def create_buttons(self):
        """Create dialog buttons"""
        if self.cancellable:
            button_frame = ttk.Frame(self.main_frame)
            button_frame.pack(side=BOTTOM, fill=X, pady=(20, 0))

            cancel_btn = ModernButton(
                button_frame,
                text="Cancel",
                command=self.cancel_operation,
                style_type='secondary'
            )
            cancel_btn.pack()

    def set_progress(self, value: float, message: str = ""):
        """Set progress value (0-100)"""
        if not self.cancelled:
            self.progress.configure(mode='determinate', value=value)
            if message:
                self.status_var.set(message)
            self.update()

    def cancel_operation(self):
        """Cancel the operation"""
        self.cancelled = True
        self.cancel()


class FilePickerDialog(BaseDialog):
    """File picker dialog for attachments"""

    def __init__(self, parent, title: str = "Select Files",
                 filetypes: List[Tuple[str, str]] = None,
                 multiple: bool = True):
        self.filetypes = filetypes or [("All Files", "*.*")]
        self.multiple = multiple
        self.selected_files = []
        super().__init__(parent, title, width=600, height=400)

    def create_content(self):
        """Create file picker content"""
        # Instructions
        inst_label = ttk.Label(
            self.main_frame,
            text="Select files to attach:"
        )
        inst_label.pack(anchor=W, pady=(0, 10))

        # File list frame
        list_frame = ttk.Frame(self.main_frame)
        list_frame.pack(fill=BOTH, expand=True, pady=(0, 10))

        # File listbox
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=RIGHT, fill=Y)

        self.file_listbox = tk.Listbox(
            list_frame,
            selectmode=tk.MULTIPLE if self.multiple else tk.SINGLE,
            yscrollcommand=scrollbar.set
        )
        self.file_listbox.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.config(command=self.file_listbox.yview)

        # Button frame
        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(fill=X)

        # Add file button
        add_btn = ModernButton(
            btn_frame,
            text="Add Files",
            icon='plus',
            command=self.add_files,
            style_type='secondary'
        )
        add_btn.pack(side=LEFT, padx=(0, 5))

        # Remove file button
        remove_btn = ModernButton(
            btn_frame,
            text="Remove",
            icon='trash',
            command=self.remove_files,
            style_type='secondary'
        )
        remove_btn.pack(side=LEFT)

    def add_files(self):
        """Add files to the list"""
        if self.multiple:
            files = filedialog.askopenfilenames(
                parent=self,
                title="Select Files",
                filetypes=self.filetypes
            )
        else:
            file = filedialog.askopenfilename(
                parent=self,
                title="Select File",
                filetypes=self.filetypes
            )
            files = [file] if file else []

        for file in files:
            if file and file not in self.selected_files:
                self.selected_files.append(file)
                self.file_listbox.insert(tk.END, Path(file).name)

    def remove_files(self):
        """Remove selected files from the list"""
        selected = self.file_listbox.curselection()
        for index in reversed(selected):
            self.file_listbox.delete(index)
            del self.selected_files[index]

    def ok(self):
        """Handle OK button"""
        self.result = self.selected_files
        self.destroy()


class DateRangeDialog(BaseDialog):
    """Date range selection dialog"""

    def __init__(self, parent, title: str = "Select Date Range",
                 start_date: Optional[date] = None,
                 end_date: Optional[date] = None):
        self.initial_start = start_date
        self.initial_end = end_date
        super().__init__(parent, title, width=400, height=250)

    def create_content(self):
        """Create date range content"""
        # Start date
        ttk.Label(self.main_frame, text="Start Date:").grid(row=0, column=0, sticky=W, pady=10)
        self.start_picker = DatePicker(self.main_frame)
        if self.initial_start:
            self.start_picker.set_date(self.initial_start)
        self.start_picker.grid(row=0, column=1, sticky=W, pady=10, padx=(10, 0))

        # End date
        ttk.Label(self.main_frame, text="End Date:").grid(row=1, column=0, sticky=W, pady=10)
        self.end_picker = DatePicker(self.main_frame)
        if self.initial_end:
            self.end_picker.set_date(self.initial_end)
        self.end_picker.grid(row=1, column=1, sticky=W, pady=10, padx=(10, 0))

        # Quick select buttons
        quick_frame = ttk.LabelFrame(self.main_frame, text="Quick Select", padding=10)
        quick_frame.grid(row=2, column=0, columnspan=2, sticky=EW, pady=(20, 0))

        # Quick select options
        quick_options = [
            ("Today", lambda: self.set_range(date.today(), date.today())),
            ("This Week", lambda: self.set_week_range()),
            ("This Month", lambda: self.set_month_range()),
            ("Last 30 Days", lambda: self.set_days_range(30)),
            ("This Year", lambda: self.set_year_range())
        ]

        for i, (text, command) in enumerate(quick_options):
            btn = ttk.Button(quick_frame, text=text, command=command)
            btn.grid(row=0, column=i, padx=2)

    def set_range(self, start: date, end: date):
        """Set date range"""
        self.start_picker.set_date(start)
        self.end_picker.set_date(end)

    def set_week_range(self):
        """Set current week range"""
        today = date.today()
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        self.set_range(start, end)

    def set_month_range(self):
        """Set current month range"""
        today = date.today()
        start = date(today.year, today.month, 1)
        if today.month == 12:
            end = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end = date(today.year, today.month + 1, 1) - timedelta(days=1)
        self.set_range(start, end)

    def set_days_range(self, days: int):
        """Set range for last N days"""
        end = date.today()
        start = end - timedelta(days=days - 1)
        self.set_range(start, end)

    def set_year_range(self):
        """Set current year range"""
        today = date.today()
        start = date(today.year, 1, 1)
        end = date(today.year, 12, 31)
        self.set_range(start, end)

    def validate_input(self) -> Tuple[bool, str]:
        """Validate date range"""
        start = self.start_picker.selected_date
        end = self.end_picker.selected_date

        if start > end:
            return False, "Start date must be before or equal to end date"

        return True, ""

    def ok(self):
        """Handle OK button"""
        valid, message = self.validate_input()
        if not valid:
            messagebox.showerror("Validation Error", message)
            return

        self.result = {
            'start_date': self.start_picker.selected_date,
            'end_date': self.end_picker.selected_date
        }
        self.destroy()


class SearchDialog(BaseDialog):
    """Advanced search dialog"""

    def __init__(self, parent, search_areas: List[str] = None):
        self.search_areas = search_areas or ['Tasks', 'Team', 'Legislation']
        super().__init__(parent, "Advanced Search", width=600, height=500)

    def create_content(self):
        """Create search content"""
        # Search query
        ttk.Label(self.main_frame, text="Search for:").grid(row=0, column=0, sticky=W, pady=5)
        self.query_var = tk.StringVar()
        self.query_entry = ModernEntry(
            self.main_frame,
            textvariable=self.query_var,
            placeholder="Enter search terms..."
        )
        self.query_entry.grid(row=0, column=1, sticky=EW, pady=5, padx=(10, 0))

        # Search in
        ttk.Label(self.main_frame, text="Search in:").grid(row=1, column=0, sticky=W, pady=5)
        area_frame = ttk.Frame(self.main_frame)
        area_frame.grid(row=1, column=1, sticky=W, pady=5, padx=(10, 0))

        self.area_vars = {}
        for area in self.search_areas:
            var = tk.BooleanVar(value=True)
            self.area_vars[area] = var
            cb = ttk.Checkbutton(area_frame, text=area, variable=var)
            cb.pack(side=LEFT, padx=(0, 10))

        # Filters
        filter_frame = ttk.LabelFrame(self.main_frame, text="Filters", padding=10)
        filter_frame.grid(row=2, column=0, columnspan=2, sticky=EW, pady=(10, 0))

        # Status filter
        ttk.Label(filter_frame, text="Status:").grid(row=0, column=0, sticky=W, pady=5)
        self.status_var = tk.StringVar(value="All")
        status_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.status_var,
            values=['All', 'Open', 'In Progress', 'Completed', 'Closed'],
            state='readonly',
            width=15
        )
        status_combo.grid(row=0, column=1, sticky=W, pady=5, padx=(10, 0))

        # Priority filter
        ttk.Label(filter_frame, text="Priority:").grid(row=0, column=2, sticky=W, pady=5, padx=(20, 0))
        self.priority_var = tk.StringVar(value="All")
        priority_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.priority_var,
            values=['All', 'Critical', 'High', 'Medium', 'Low'],
            state='readonly',
            width=15
        )
        priority_combo.grid(row=0, column=3, sticky=W, pady=5, padx=(10, 0))

        # Date range
        ttk.Label(filter_frame, text="Date Range:").grid(row=1, column=0, sticky=W, pady=5)
        date_frame = ttk.Frame(filter_frame)
        date_frame.grid(row=1, column=1, columnspan=3, sticky=W, pady=5, padx=(10, 0))

        self.date_enabled = tk.BooleanVar(value=False)
        date_check = ttk.Checkbutton(
            date_frame,
            text="Enable",
            variable=self.date_enabled,
            command=self.toggle_date_range
        )
        date_check.pack(side=LEFT)

        self.start_date = DatePicker(date_frame)
        self.start_date.pack(side=LEFT, padx=(10, 5))
        ttk.Label(date_frame, text="to").pack(side=LEFT)
        self.end_date = DatePicker(date_frame)
        self.end_date.pack(side=LEFT, padx=(5, 0))

        # Initially disable date pickers
        self.toggle_date_range()

        # Search options
        options_frame = ttk.LabelFrame(self.main_frame, text="Options", padding=10)
        options_frame.grid(row=3, column=0, columnspan=2, sticky=EW, pady=(10, 0))

        self.case_sensitive = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame,
            text="Case sensitive",
            variable=self.case_sensitive
        ).pack(anchor=W)

        self.whole_words = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame,
            text="Whole words only",
            variable=self.whole_words
        ).pack(anchor=W)

        self.include_archived = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame,
            text="Include archived items",
            variable=self.include_archived
        ).pack(anchor=W)

        # Configure grid
        self.main_frame.grid_columnconfigure(1, weight=1)

    def toggle_date_range(self):
        """Enable/disable date range pickers"""
        state = 'normal' if self.date_enabled.get() else 'disabled'
        for child in self.start_date.winfo_children():
            if isinstance(child, (ttk.Button, ttk.Entry)):
                child.configure(state=state)
        for child in self.end_date.winfo_children():
            if isinstance(child, (ttk.Button, ttk.Entry)):
                child.configure(state=state)

    def validate_input(self) -> Tuple[bool, str]:
        """Validate search input"""
        if not self.query_var.get().strip():
            return False, "Please enter search terms"

        if not any(var.get() for var in self.area_vars.values()):
            return False, "Please select at least one area to search"

        if self.date_enabled.get():
            if self.start_date.selected_date > self.end_date.selected_date:
                return False, "Start date must be before end date"

        return True, ""

    def ok(self):
        """Handle OK button"""
        valid, message = self.validate_input()
        if not valid:
            messagebox.showerror("Validation Error", message)
            return

        self.result = {
            'query': self.query_var.get().strip(),
            'areas': [area for area, var in self.area_vars.items() if var.get()],
            'status': self.status_var.get(),
            'priority': self.priority_var.get(),
            'date_range': {
                'enabled': self.date_enabled.get(),
                'start': self.start_date.selected_date if self.date_enabled.get() else None,
                'end': self.end_date.selected_date if self.date_enabled.get() else None
            },
            'options': {
                'case_sensitive': self.case_sensitive.get(),
                'whole_words': self.whole_words.get(),
                'include_archived': self.include_archived.get()
            }
        }
        self.destroy()


class ExportDialog(BaseDialog):
    """Export options dialog"""

    def __init__(self, parent, export_types: List[str] = None):
        self.export_types = export_types or ['Excel', 'PDF', 'CSV']
        super().__init__(parent, "Export Data", width=500, height=400)

    def create_content(self):
        """Create export options"""
        # Export type
        ttk.Label(self.main_frame, text="Export Format:").grid(row=0, column=0, sticky=W, pady=10)
        self.format_var = tk.StringVar(value=self.export_types[0])
        format_frame = ttk.Frame(self.main_frame)
        format_frame.grid(row=0, column=1, sticky=W, pady=10, padx=(10, 0))

        for format_type in self.export_types:
            rb = ttk.Radiobutton(
                format_frame,
                text=format_type,
                variable=self.format_var,
                value=format_type
            )
            rb.pack(side=LEFT, padx=(0, 20))

        # Content options
        content_frame = ttk.LabelFrame(self.main_frame, text="Content", padding=10)
        content_frame.grid(row=1, column=0, columnspan=2, sticky=EW, pady=(10, 0))

        self.include_options = {
            'summary': tk.BooleanVar(value=True),
            'details': tk.BooleanVar(value=True),
            'attachments': tk.BooleanVar(value=False),
            'history': tk.BooleanVar(value=False)
        }

        option_labels = {
            'summary': 'Include summary',
            'details': 'Include detailed data',
            'attachments': 'Include attachment references',
            'history': 'Include change history'
        }

        for i, (key, var) in enumerate(self.include_options.items()):
            cb = ttk.Checkbutton(
                content_frame,
                text=option_labels[key],
                variable=var
            )
            cb.grid(row=i, column=0, sticky=W, pady=2)

        # Date range
        date_frame = ttk.LabelFrame(self.main_frame, text="Date Range", padding=10)
        date_frame.grid(row=2, column=0, columnspan=2, sticky=EW, pady=(10, 0))

        self.date_option = tk.StringVar(value="all")
        ttk.Radiobutton(
            date_frame,
            text="All data",
            variable=self.date_option,
            value="all",
            command=self.toggle_date_range
        ).grid(row=0, column=0, sticky=W)

        ttk.Radiobutton(
            date_frame,
            text="Date range:",
            variable=self.date_option,
            value="range",
            command=self.toggle_date_range
        ).grid(row=1, column=0, sticky=W)

        # Date pickers
        self.date_frame = ttk.Frame(date_frame)
        self.date_frame.grid(row=1, column=1, sticky=W, padx=(10, 0))

        self.start_date = DatePicker(self.date_frame)
        self.start_date.pack(side=LEFT)
        ttk.Label(self.date_frame, text=" to ").pack(side=LEFT, padx=5)
        self.end_date = DatePicker(self.date_frame)
        self.end_date.pack(side=LEFT)

        # Initially disable date pickers
        self.toggle_date_range()

        # File location
        ttk.Label(self.main_frame, text="Save to:").grid(row=3, column=0, sticky=W, pady=(20, 0))
        location_frame = ttk.Frame(self.main_frame)
        location_frame.grid(row=3, column=1, sticky=EW, pady=(20, 0), padx=(10, 0))

        self.location_var = tk.StringVar(value=str(Path.home() / "Downloads"))
        location_entry = ttk.Entry(location_frame, textvariable=self.location_var)
        location_entry.pack(side=LEFT, fill=X, expand=True)

        browse_btn = ttk.Button(
            location_frame,
            text="Browse",
            command=self.browse_location
        )
        browse_btn.pack(side=LEFT, padx=(5, 0))

        # Configure grid
        self.main_frame.grid_columnconfigure(1, weight=1)

    def toggle_date_range(self):
        """Enable/disable date range based on selection"""
        if self.date_option.get() == "range":
            for child in self.date_frame.winfo_children():
                if isinstance(child, DatePicker):
                    for widget in child.winfo_children():
                        if isinstance(widget, (ttk.Button, ttk.Entry)):
                            widget.configure(state='normal')
        else:
            for child in self.date_frame.winfo_children():
                if isinstance(child, DatePicker):
                    for widget in child.winfo_children():
                        if isinstance(widget, (ttk.Button, ttk.Entry)):
                            widget.configure(state='disabled')

    def browse_location(self):
        """Browse for save location"""
        directory = filedialog.askdirectory(
            parent=self,
            title="Select Export Location",
            initialdir=self.location_var.get()
        )
        if directory:
            self.location_var.set(directory)

    def validate_input(self) -> Tuple[bool, str]:
        """Validate export options"""
        if not any(var.get() for var in self.include_options.values()):
            return False, "Please select at least one content option"

        if self.date_option.get() == "range":
            if self.start_date.selected_date > self.end_date.selected_date:
                return False, "Start date must be before end date"

        if not Path(self.location_var.get()).exists():
            return False, "Invalid save location"

        return True, ""

    def ok(self):
        """Handle OK button"""
        valid, message = self.validate_input()
        if not valid:
            messagebox.showerror("Validation Error", message)
            return

        self.result = {
            'format': self.format_var.get(),
            'include': {k: v.get() for k, v in self.include_options.items()},
            'date_option': self.date_option.get(),
            'date_range': {
                'start': self.start_date.selected_date,
                'end': self.end_date.selected_date
            } if self.date_option.get() == "range" else None,
            'location': self.location_var.get()
        }
        self.destroy()


class CustomReportDialog(BaseDialog):
    """Custom report configuration dialog"""

    def __init__(self, parent, available_fields: Dict[str, List[str]] = None):
        self.available_fields = available_fields or {
            'Task': ['Key', 'Title', 'Status', 'Priority', 'Assigned To'],
            'Team': ['Name', 'Email', 'Department', 'Role'],
            'Compliance': ['Area', 'Requirements', 'Status']
        }
        super().__init__(parent, "Custom Report", width=700, height=500)

    def create_content(self):
        """Create custom report configuration"""
        # Report name
        ttk.Label(self.main_frame, text="Report Name:").grid(row=0, column=0, sticky=W, pady=5)
        self.name_var = tk.StringVar()
        name_entry = ModernEntry(
            self.main_frame,
            textvariable=self.name_var,
            placeholder="Enter report name..."
        )
        name_entry.grid(row=0, column=1, columnspan=2, sticky=EW, pady=5, padx=(10, 0))

        # Data source
        ttk.Label(self.main_frame, text="Data Source:").grid(row=1, column=0, sticky=W, pady=5)
        self.source_var = tk.StringVar(value=list(self.available_fields.keys())[0])
        source_combo = ttk.Combobox(
            self.main_frame,
            textvariable=self.source_var,
            values=list(self.available_fields.keys()),
            state='readonly'
        )
        source_combo.grid(row=1, column=1, sticky=W, pady=5, padx=(10, 0))
        source_combo.bind('<<ComboboxSelected>>', self.update_field_lists)

        # Field selection
        field_frame = ttk.LabelFrame(self.main_frame, text="Select Fields", padding=10)
        field_frame.grid(row=2, column=0, columnspan=3, sticky=NSEW, pady=(10, 0))

        # Available fields
        ttk.Label(field_frame, text="Available Fields:").grid(row=0, column=0)

        avail_frame = ttk.Frame(field_frame)
        avail_frame.grid(row=1, column=0, sticky=NSEW, padx=(0, 5))

        avail_scroll = ttk.Scrollbar(avail_frame)
        avail_scroll.pack(side=RIGHT, fill=Y)

        self.available_list = tk.Listbox(
            avail_frame,
            selectmode=tk.MULTIPLE,
            yscrollcommand=avail_scroll.set
        )
        self.available_list.pack(side=LEFT, fill=BOTH, expand=True)
        avail_scroll.config(command=self.available_list.yview)

        # Buttons
        button_frame = ttk.Frame(field_frame)
        button_frame.grid(row=1, column=1, padx=10)

        ttk.Button(
            button_frame,
            text=">>",
            command=self.add_fields,
            width=5
        ).pack(pady=5)

        ttk.Button(
            button_frame,
            text="<<",
            command=self.remove_fields,
            width=5
        ).pack(pady=5)

        # Selected fields
        ttk.Label(field_frame, text="Selected Fields:").grid(row=0, column=2)

        selected_frame = ttk.Frame(field_frame)
        selected_frame.grid(row=1, column=2, sticky=NSEW, padx=(5, 0))

        selected_scroll = ttk.Scrollbar(selected_frame)
        selected_scroll.pack(side=RIGHT, fill=Y)

        self.selected_list = tk.Listbox(
            selected_frame,
            selectmode=tk.MULTIPLE,
            yscrollcommand=selected_scroll.set
        )
        self.selected_list.pack(side=LEFT, fill=BOTH, expand=True)
        selected_scroll.config(command=self.selected_list.yview)

        # Configure field frame grid
        field_frame.grid_rowconfigure(1, weight=1)
        field_frame.grid_columnconfigure(0, weight=1)
        field_frame.grid_columnconfigure(2, weight=1)

        # Sort and group options
        options_frame = ttk.LabelFrame(self.main_frame, text="Options", padding=10)
        options_frame.grid(row=3, column=0, columnspan=3, sticky=EW, pady=(10, 0))

        # Sort by
        ttk.Label(options_frame, text="Sort by:").grid(row=0, column=0, sticky=W)
        self.sort_var = tk.StringVar()
        self.sort_combo = ttk.Combobox(
            options_frame,
            textvariable=self.sort_var,
            state='readonly',
            width=20
        )
        self.sort_combo.grid(row=0, column=1, sticky=W, padx=(10, 0))

        # Group by
        ttk.Label(options_frame, text="Group by:").grid(row=1, column=0, sticky=W, pady=(5, 0))
        self.group_var = tk.StringVar()
        self.group_combo = ttk.Combobox(
            options_frame,
            textvariable=self.group_var,
            state='readonly',
            width=20
        )
        self.group_combo.grid(row=1, column=1, sticky=W, padx=(10, 0), pady=(5, 0))

        # Summary options
        self.include_summary = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Include summary statistics",
            variable=self.include_summary
        ).grid(row=2, column=0, columnspan=2, sticky=W, pady=(10, 0))

        # Configure main grid
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)

        # Initialize field lists
        self.update_field_lists()

    def update_field_lists(self, event=None):
        """Update field lists based on selected source"""
        source = self.source_var.get()
        fields = self.available_fields.get(source, [])

        # Clear lists
        self.available_list.delete(0, tk.END)
        self.selected_list.delete(0, tk.END)

        # Populate available fields
        for field in fields:
            self.available_list.insert(tk.END, field)

        # Update sort/group options
        self.sort_combo['values'] = fields
        self.group_combo['values'] = ['None'] + fields

    def add_fields(self):
        """Add selected fields to report"""
        selected = self.available_list.curselection()
        for index in reversed(selected):
            field = self.available_list.get(index)
            self.selected_list.insert(tk.END, field)
            self.available_list.delete(index)

    def remove_fields(self):
        """Remove fields from report"""
        selected = self.selected_list.curselection()
        for index in reversed(selected):
            field = self.selected_list.get(index)
            self.available_list.insert(tk.END, field)
            self.selected_list.delete(index)

    def validate_input(self) -> Tuple[bool, str]:
        """Validate report configuration"""
        if not self.name_var.get().strip():
            return False, "Please enter a report name"

        if self.selected_list.size() == 0:
            return False, "Please select at least one field"

        return True, ""

    def ok(self):
        """Handle OK button"""
        valid, message = self.validate_input()
        if not valid:
            messagebox.showerror("Validation Error", message)
            return

        # Collect selected fields
        selected_fields = []
        for i in range(self.selected_list.size()):
            selected_fields.append(self.selected_list.get(i))

        self.result = {
            'name': self.name_var.get().strip(),
            'source': self.source_var.get(),
            'fields': selected_fields,
            'sort_by': self.sort_var.get() if self.sort_var.get() else None,
            'group_by': self.group_var.get() if self.group_var.get() != 'None' else None,
            'include_summary': self.include_summary.get()
        }
        self.destroy()


class LoginDialog(BaseDialog):
    """Login dialog for user authentication"""

    def __init__(self, parent, allow_register: bool = False):
        self.allow_register = allow_register
        super().__init__(parent, "Login", width=400, height=300)

    def create_content(self):
        """Create login form"""
        # Logo or title
        title_label = ModernLabel(
            self.main_frame,
            text="Compliance Management System",
            style_type='heading2'
        )
        title_label.pack(pady=(0, 30))

        # Login frame
        login_frame = ttk.Frame(self.main_frame)
        login_frame.pack(fill=BOTH, expand=True)

        # Username
        ttk.Label(login_frame, text="Username:").grid(row=0, column=0, sticky=W, pady=10)
        self.username_var = tk.StringVar()
        self.username_entry = ModernEntry(
            login_frame,
            textvariable=self.username_var,
            placeholder="Enter username or email"
        )
        self.username_entry.grid(row=0, column=1, sticky=EW, pady=10, padx=(10, 0))

        # Password
        ttk.Label(login_frame, text="Password:").grid(row=1, column=0, sticky=W, pady=10)
        self.password_var = tk.StringVar()
        self.password_entry = ModernEntry(
            login_frame,
            textvariable=self.password_var,
            show="*"
        )
        self.password_entry.grid(row=1, column=1, sticky=EW, pady=10, padx=(10, 0))

        # Remember me
        self.remember_var = tk.BooleanVar(value=False)
        remember_check = ttk.Checkbutton(
            login_frame,
            text="Remember me",
            variable=self.remember_var
        )
        remember_check.grid(row=2, column=1, sticky=W, pady=(10, 0), padx=(10, 0))

        # Configure grid
        login_frame.grid_columnconfigure(1, weight=1)

        # Bind Enter key
        self.username_entry.bind('<Return>', lambda e: self.password_entry.focus())
        self.password_entry.bind('<Return>', lambda e: self.ok())

    def create_buttons(self):
        """Create dialog buttons"""
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(side=BOTTOM, fill=X, pady=(20, 0))

        # Cancel button
        cancel_btn = ModernButton(
            button_frame,
            text="Cancel",
            command=self.cancel,
            style_type='secondary'
        )
        cancel_btn.pack(side=RIGHT, padx=(5, 0))

        # Login button
        login_btn = ModernButton(
            button_frame,
            text="Login",
            command=self.ok,
            style_type='primary'
        )
        login_btn.pack(side=RIGHT)

        if self.allow_register:
            # Register button
            register_btn = ModernButton(
                button_frame,
                text="Register",
                command=self.register,
                style_type='link'
            )
            register_btn.pack(side=LEFT)

    def validate_input(self) -> Tuple[bool, str]:
        """Validate login input"""
        if not self.username_var.get().strip():
            return False, "Please enter username or email"

        if not self.password_var.get():
            return False, "Please enter password"

        return True, ""

    def ok(self):
        """Handle login"""
        valid, message = self.validate_input()
        if not valid:
            messagebox.showerror("Validation Error", message)
            return

        self.result = {
            'username': self.username_var.get().strip(),
            'password': self.password_var.get(),
            'remember': self.remember_var.get()
        }
        self.destroy()

    def register(self):
        """Handle register request"""
        self.result = {'action': 'register'}
        self.destroy()


class SettingsDialog(BaseDialog):
    """Application settings dialog"""

    def __init__(self, parent, current_settings: Dict[str, Any] = None):
        self.current_settings = current_settings or {}
        super().__init__(parent, "Settings", width=600, height=500)

    def create_content(self):
        """Create settings tabs"""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.main_frame)
        notebook.pack(fill=BOTH, expand=True)

        # General settings tab
        general_frame = ttk.Frame(notebook, padding=20)
        notebook.add(general_frame, text="General")
        self.create_general_settings(general_frame)

        # Appearance tab
        appearance_frame = ttk.Frame(notebook, padding=20)
        notebook.add(appearance_frame, text="Appearance")
        self.create_appearance_settings(appearance_frame)

        # Notifications tab
        notif_frame = ttk.Frame(notebook, padding=20)
        notebook.add(notif_frame, text="Notifications")
        self.create_notification_settings(notif_frame)

        # Data tab
        data_frame = ttk.Frame(notebook, padding=20)
        notebook.add(data_frame, text="Data")
        self.create_data_settings(data_frame)

    def create_general_settings(self, parent):
        """Create general settings"""
        # Auto-save
        self.auto_save = tk.BooleanVar(
            value=self.current_settings.get('auto_save', True)
        )
        ttk.Checkbutton(
            parent,
            text="Enable auto-save",
            variable=self.auto_save
        ).grid(row=0, column=0, sticky=W, pady=5)

        # Auto-save interval
        ttk.Label(parent, text="Auto-save interval (minutes):").grid(row=1, column=0, sticky=W, pady=5)
        self.save_interval = tk.IntVar(
            value=self.current_settings.get('save_interval', 5)
        )
        interval_spin = ttk.Spinbox(
            parent,
            from_=1,
            to=60,
            textvariable=self.save_interval,
            width=10
        )
        interval_spin.grid(row=1, column=1, sticky=W, pady=5, padx=(10, 0))

        # Default view
        ttk.Label(parent, text="Default view:").grid(row=2, column=0, sticky=W, pady=5)
        self.default_view = tk.StringVar(
            value=self.current_settings.get('default_view', 'Dashboard')
        )
        view_combo = ttk.Combobox(
            parent,
            textvariable=self.default_view,
            values=['Dashboard', 'Tasks', 'Team', 'Reports'],
            state='readonly',
            width=20
        )
        view_combo.grid(row=2, column=1, sticky=W, pady=5, padx=(10, 0))

    def create_appearance_settings(self, parent):
        """Create appearance settings"""
        # Theme
        ttk.Label(parent, text="Theme:").grid(row=0, column=0, sticky=W, pady=5)
        self.theme_var = tk.StringVar(
            value=self.current_settings.get('theme', 'default')
        )
        theme_combo = ttk.Combobox(
            parent,
            textvariable=self.theme_var,
            values=['default', 'dark', 'light', 'blue', 'green'],
            state='readonly',
            width=20
        )
        theme_combo.grid(row=0, column=1, sticky=W, pady=5, padx=(10, 0))

        # Font size
        ttk.Label(parent, text="Font size:").grid(row=1, column=0, sticky=W, pady=5)
        self.font_size = tk.IntVar(
            value=self.current_settings.get('font_size', 10)
        )
        size_spin = ttk.Spinbox(
            parent,
            from_=8,
            to=16,
            textvariable=self.font_size,
            width=10
        )
        size_spin.grid(row=1, column=1, sticky=W, pady=5, padx=(10, 0))

        # Compact mode
        self.compact_mode = tk.BooleanVar(
            value=self.current_settings.get('compact_mode', False)
        )
        ttk.Checkbutton(
            parent,
            text="Enable compact mode",
            variable=self.compact_mode
        ).grid(row=2, column=0, columnspan=2, sticky=W, pady=5)

    def create_notification_settings(self, parent):
        """Create notification settings"""
        # Enable notifications
        self.enable_notif = tk.BooleanVar(
            value=self.current_settings.get('enable_notifications', True)
        )
        ttk.Checkbutton(
            parent,
            text="Enable notifications",
            variable=self.enable_notif
        ).grid(row=0, column=0, columnspan=2, sticky=W, pady=5)

        # Notification types
        ttk.Label(parent, text="Notify me about:").grid(row=1, column=0, sticky=NW, pady=(15, 5))

        notif_frame = ttk.Frame(parent)
        notif_frame.grid(row=1, column=1, sticky=W, pady=(15, 5), padx=(10, 0))

        self.notif_types = {
            'task_assigned': tk.BooleanVar(value=self.current_settings.get('notify_task_assigned', True)),
            'task_due': tk.BooleanVar(value=self.current_settings.get('notify_task_due', True)),
            'task_completed': tk.BooleanVar(value=self.current_settings.get('notify_task_completed', True)),
            'approval_required': tk.BooleanVar(value=self.current_settings.get('notify_approval_required', True))
        }

        notif_labels = {
            'task_assigned': 'New tasks assigned to me',
            'task_due': 'Tasks approaching due date',
            'task_completed': 'Tasks completed',
            'approval_required': 'Approvals required'
        }

        for i, (key, var) in enumerate(self.notif_types.items()):
            cb = ttk.Checkbutton(
                notif_frame,
                text=notif_labels[key],
                variable=var
            )
            cb.grid(row=i, column=0, sticky=W, pady=2)

        # Email notifications
        self.email_notif = tk.BooleanVar(
            value=self.current_settings.get('email_notifications', False)
        )
        ttk.Checkbutton(
            parent,
            text="Send email notifications",
            variable=self.email_notif
        ).grid(row=2, column=0, columnspan=2, sticky=W, pady=(15, 5))

    def create_data_settings(self, parent):
        """Create data settings"""
        # Data location
        ttk.Label(parent, text="Data location:").grid(row=0, column=0, sticky=W, pady=5)

        data_frame = ttk.Frame(parent)
        data_frame.grid(row=0, column=1, sticky=EW, pady=5, padx=(10, 0))

        self.data_location = tk.StringVar(
            value=self.current_settings.get('data_location', str(Path.home() / 'ComplianceData'))
        )
        location_entry = ttk.Entry(data_frame, textvariable=self.data_location)
        location_entry.pack(side=LEFT, fill=X, expand=True)

        browse_btn = ttk.Button(
            data_frame,
            text="Browse",
            command=self.browse_data_location
        )
        browse_btn.pack(side=LEFT, padx=(5, 0))

        # Backup
        self.auto_backup = tk.BooleanVar(
            value=self.current_settings.get('auto_backup', True)
        )
        ttk.Checkbutton(
            parent,
            text="Enable automatic backups",
            variable=self.auto_backup
        ).grid(row=1, column=0, columnspan=2, sticky=W, pady=(15, 5))

        # Backup frequency
        ttk.Label(parent, text="Backup frequency:").grid(row=2, column=0, sticky=W, pady=5)
        self.backup_freq = tk.StringVar(
            value=self.current_settings.get('backup_frequency', 'Daily')
        )
        freq_combo = ttk.Combobox(
            parent,
            textvariable=self.backup_freq,
            values=['Daily', 'Weekly', 'Monthly'],
            state='readonly',
            width=20
        )
        freq_combo.grid(row=2, column=1, sticky=W, pady=5, padx=(10, 0))

        # Archive old data
        self.auto_archive = tk.BooleanVar(
            value=self.current_settings.get('auto_archive', False)
        )
        ttk.Checkbutton(
            parent,
            text="Automatically archive old data",
            variable=self.auto_archive
        ).grid(row=3, column=0, columnspan=2, sticky=W, pady=(15, 5))

        # Archive after days
        ttk.Label(parent, text="Archive data older than (days):").grid(row=4, column=0, sticky=W, pady=5)
        self.archive_days = tk.IntVar(
            value=self.current_settings.get('archive_days', 365)
        )
        days_spin = ttk.Spinbox(
            parent,
            from_=30,
            to=1825,
            textvariable=self.archive_days,
            width=10
        )
        days_spin.grid(row=4, column=1, sticky=W, pady=5, padx=(10, 0))

        # Configure grid
        parent.grid_columnconfigure(1, weight=1)

    def browse_data_location(self):
        """Browse for data location"""
        directory = filedialog.askdirectory(
            parent=self,
            title="Select Data Location",
            initialdir=self.data_location.get()
        )
        if directory:
            self.data_location.set(directory)

    def ok(self):
        """Handle OK button"""
        # Collect all settings
        self.result = {
            # General
            'auto_save': self.auto_save.get(),
            'save_interval': self.save_interval.get(),
            'default_view': self.default_view.get(),

            # Appearance
            'theme': self.theme_var.get(),
            'font_size': self.font_size.get(),
            'compact_mode': self.compact_mode.get(),

            # Notifications
            'enable_notifications': self.enable_notif.get(),
            'notify_task_assigned': self.notif_types['task_assigned'].get(),
            'notify_task_due': self.notif_types['task_due'].get(),
            'notify_task_completed': self.notif_types['task_completed'].get(),
            'notify_approval_required': self.notif_types['approval_required'].get(),
            'email_notifications': self.email_notif.get(),

            # Data
            'data_location': self.data_location.get(),
            'auto_backup': self.auto_backup.get(),
            'backup_frequency': self.backup_freq.get(),
            'auto_archive': self.auto_archive.get(),
            'archive_days': self.archive_days.get()
        }
        self.destroy()


class HelpDialog(BaseDialog):
    """Help and documentation dialog"""

    def __init__(self, parent):
        super().__init__(parent, "Help", width=700, height=500)

    def create_content(self):
        """Create help content"""
        # Create notebook for help topics
        notebook = ttk.Notebook(self.main_frame)
        notebook.pack(fill=BOTH, expand=True)

        # Getting Started
        start_frame = ttk.Frame(notebook, padding=20)
        notebook.add(start_frame, text="Getting Started")
        self.create_getting_started(start_frame)

        # Features
        features_frame = ttk.Frame(notebook, padding=20)
        notebook.add(features_frame, text="Features")
        self.create_features(features_frame)

        # FAQ
        faq_frame = ttk.Frame(notebook, padding=20)
        notebook.add(faq_frame, text="FAQ")
        self.create_faq(faq_frame)

        # About
        about_frame = ttk.Frame(notebook, padding=20)
        notebook.add(about_frame, text="About")
        self.create_about(about_frame)

    def create_getting_started(self, parent):
        """Create getting started content"""
        # Create scrollable text
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill=BOTH, expand=True)

        scroll = ttk.Scrollbar(text_frame)
        scroll.pack(side=RIGHT, fill=Y)

        text = tk.Text(
            text_frame,
            wrap=WORD,
            yscrollcommand=scroll.set,
            padx=10,
            pady=10
        )
        text.pack(side=LEFT, fill=BOTH, expand=True)
        scroll.config(command=text.yview)

        # Add content
        content = """Welcome to the Compliance Management System!

Getting Started:

1. Dashboard Overview
   The dashboard provides a quick overview of your compliance status, including:
   - Active tasks and their priorities
   - Upcoming deadlines
   - Team performance metrics
   - Recent activities

2. Managing Tasks
   - Click 'Tasks' to view all compliance tasks
   - Use the 'New Task' button to create new tasks
   - Double-click any task to view details or edit
   - Assign tasks to team members and set priorities

3. Team Management
   - View and manage team members from the 'Team' view
   - Add new members with appropriate roles and permissions
   - Track individual workloads and performance

4. Compliance Tracking
   - Monitor compliance areas and requirements
   - Link tasks to specific legislation
   - Generate compliance reports

5. Reports and Analytics
   - Access comprehensive reports from the 'Reports' section
   - Export data in various formats
   - Create custom reports for specific needs

For more detailed information, please refer to the other help sections or contact support.
"""
        text.insert(1.0, content)
        text.config(state='disabled')

    def create_features(self, parent):
        """Create features content"""
        # Create scrollable frame
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas_frame = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def configure_canvas(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas.bind("<Configure>", configure_canvas)

        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        # Add feature cards
        features = [
            {
                'title': 'Task Management',
                'icon': '📋',
                'description': 'Create, assign, and track compliance tasks with priorities and deadlines.'
            },
            {
                'title': 'Team Collaboration',
                'icon': '👥',
                'description': 'Manage team members, assign roles, and track individual workloads.'
            },
            {
                'title': 'Legislative Tracking',
                'icon': '📚',
                'description': 'Keep track of relevant legislation and link requirements to tasks.'
            },
            {
                'title': 'Automated Notifications',
                'icon': '🔔',
                'description': 'Receive alerts for deadlines, assignments, and approval requests.'
            },
            {
                'title': 'Comprehensive Reporting',
                'icon': '📊',
                'description': 'Generate detailed reports and export data in multiple formats.'
            },
            {
                'title': 'Approval Workflows',
                'icon': '✅',
                'description': 'Manage approval processes with complete audit trails.'
            }
        ]

        for i, feature in enumerate(features):
            frame = Card(scrollable_frame, title=feature['title'])
            frame.grid(row=i // 2, column=i % 2, padx=10, pady=10, sticky=EW)

            # Icon
            icon_label = ttk.Label(
                frame.content_frame,
                text=feature['icon'],
                font=('', 24)
            )
            icon_label.pack(pady=(0, 10))

            # Description
            desc_label = ttk.Label(
                frame.content_frame,
                text=feature['description'],
                wraplength=250
            )
            desc_label.pack()

        # Configure grid
        scrollable_frame.grid_columnconfigure(0, weight=1)
        scrollable_frame.grid_columnconfigure(1, weight=1)

    def create_faq(self, parent):
        """Create FAQ content"""
        # Create scrollable text
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill=BOTH, expand=True)

        scroll = ttk.Scrollbar(text_frame)
        scroll.pack(side=RIGHT, fill=Y)

        text = tk.Text(
            text_frame,
            wrap=WORD,
            yscrollcommand=scroll.set,
            padx=10,
            pady=10
        )
        text.pack(side=LEFT, fill=BOTH, expand=True)
        scroll.config(command=text.yview)

        # FAQ content
        faqs = [
            {
                'q': 'How do I create a new task?',
                'a': 'Navigate to the Tasks view and click the "New Task" button. Fill in the required fields and click OK.'
            },
            {
                'q': 'Can I assign tasks to multiple people?',
                'a': 'Yes, when creating or editing a task, you can select multiple team members in the "Allocated To" field.'
            },
            {
                'q': 'How do I export my data?',
                'a': 'Use the Export button in any view, or go to Reports and select "Export Data". Choose your format and options.'
            },
            {
                'q': 'What roles are available for team members?',
                'a': 'Available roles include Admin, Compliance Manager, Compliance Officer, Team Lead, and Team Member.'
            },
            {
                'q': 'How often is data backed up?',
                'a': 'Data is backed up according to your settings (daily by default). You can change this in Settings > Data.'
            },
            {
                'q': 'Can I customize reports?',
                'a': 'Yes, use the "Custom Report" option in the Reports section to select specific fields and filters.'
            }
        ]

        # Add FAQs
        for i, faq in enumerate(faqs):
            # Question
            text.insert(tk.END, f"Q: {faq['q']}\n", 'question')
            # Answer
            text.insert(tk.END, f"A: {faq['a']}\n\n", 'answer')

        # Configure tags
        text.tag_config('question', font=('', 10, 'bold'))
        text.tag_config('answer', lmargin1=20, lmargin2=20)

        text.config(state='disabled')

    def create_about(self, parent):
        """Create about content"""
        # Logo/Icon
        icon_label = ttk.Label(
            parent,
            text="⚖️",
            font=('', 48)
        )
        icon_label.pack(pady=20)

        # Title
        title_label = ModernLabel(
            parent,
            text="Compliance Management System",
            style_type='heading2'
        )
        title_label.pack()

        # Version
        version_label = ttk.Label(
            parent,
            text="Version 1.0.0"
        )
        version_label.pack(pady=5)

        # Description
        desc_text = """A comprehensive compliance management system designed to help organizations
track, manage, and report on their compliance activities efficiently.

Key Features:
• Task management with priority and status tracking
• Team member management and assignment
• Legislative reference tracking
• Automated notifications and reminders
• Comprehensive reporting

For support, please contact:
compliance-support@company.com
        """

        desc_label = ttk.Label(
            parent,
            text=desc_text,
            justify=CENTER
        )
        desc_label.pack(pady=20)

        # Links frame
        links_frame = ttk.Frame(parent)
        links_frame.pack()

        # User manual link
        manual_btn = ModernButton(
            links_frame,
            text="User Manual",
            style_type='link',
            command=lambda: self.open_link("manual")
        )
        manual_btn.pack(side=LEFT, padx=10)

        # Website link
        website_btn = ModernButton(
            links_frame,
            text="Company Website",
            style_type='link',
            command=lambda: self.open_link("website")
        )
        website_btn.pack(side=LEFT, padx=10)

    def create_buttons(self):
        """Create dialog buttons"""
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(side=BOTTOM, fill=X, pady=(20, 0))

        # Close button only
        close_btn = ModernButton(
            button_frame,
            text="Close",
            command=self.cancel,
            style_type='primary'
        )
        close_btn.pack()

    def open_link(self, link_type: str):
        """Open external link"""
        links = {
            'manual': 'https://company.com/compliance/manual',
            'website': 'https://company.com'
        }

        if link_type in links:
            webbrowser.open(links[link_type])

class TaskUpdateDialog(BaseDialog):
    """Enhanced dialog for updating tasks with team modification"""

    def __init__(self, parent, task, team_members=None):
        self.task = task
        self.team_members = team_members or []
        self.selected_members = []
        self.new_files = []

        # Initialize with current allocated members
        if hasattr(task, 'allocated_to'):
            self.selected_members = [m for m in self.team_members
                                     if m.name in task.allocated_to]

        super().__init__(parent, "Update Task", width=800, height=700)

    def create_content(self):
        """Create update form content"""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=BOTH, expand=True, pady=(0, 10))

        # Update Actions tab
        actions_frame = ttk.Frame(self.notebook)
        self.notebook.add(actions_frame, text="Update Actions")
        self.create_actions_tab(actions_frame)

        # Team Assignment tab
        team_frame = ttk.Frame(self.notebook)
        self.notebook.add(team_frame, text="Team Assignment")
        self.create_team_tab(team_frame)

        # Attachments tab
        files_frame = ttk.Frame(self.notebook)
        self.notebook.add(files_frame, text="Attachments")
        self.create_files_tab(files_frame)

        # Task Info tab
        info_frame = ttk.Frame(self.notebook)
        self.notebook.add(info_frame, text="Task Information")
        self.create_info_tab(info_frame)

    def create_actions_tab(self, parent):
        """Create actions update tab"""
        # Scrollable frame
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Status update
        status_frame = ttk.LabelFrame(scrollable_frame, text="Status Update", padding=10)
        status_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(status_frame, text="Current Status:").grid(row=0, column=0, sticky=W, pady=5)
        ttk.Label(status_frame, text=self.task.status,
                  font=('Arial', 10, 'bold')).grid(row=0, column=1, sticky=W, pady=5)

        ttk.Label(status_frame, text="New Status:").grid(row=1, column=0, sticky=W, pady=5)
        self.status_var = tk.StringVar(value=self.task.status)
        status_combo = ttk.Combobox(
            status_frame,
            textvariable=self.status_var,
            values=['Open', 'In Progress', 'Pending Approval', 'Resolved', 'On Hold'],
            state='readonly',
            width=20
        )
        status_combo.grid(row=1, column=1, sticky=W, pady=5)

        # Progress percentage
        ttk.Label(status_frame, text="Progress:").grid(row=2, column=0, sticky=W, pady=5)
        self.progress_var = tk.IntVar(value=getattr(self.task, 'progress', 0))
        progress_scale = ttk.Scale(
            status_frame,
            from_=0,
            to=100,
            orient='horizontal',
            variable=self.progress_var,
            length=200
        )
        progress_scale.grid(row=2, column=1, sticky=W, pady=5)

        self.progress_label = ttk.Label(status_frame, text=f"{self.progress_var.get()}%")
        self.progress_label.grid(row=2, column=2, padx=5)

        progress_scale.configure(command=lambda v: self.progress_label.config(
            text=f"{int(float(v))}%"
        ))

        # Actions taken
        actions_frame = ttk.LabelFrame(scrollable_frame, text="Actions Taken", padding=10)
        actions_frame.pack(fill=BOTH, expand=True, pady=(0, 10))

        ttk.Label(actions_frame, text="Describe actions taken:").pack(anchor=W)

        self.actions_text = tk.Text(actions_frame, height=8, wrap='word')
        self.actions_text.pack(fill=BOTH, expand=True, pady=5)

        # Show previous actions
        if hasattr(self.task, 'actions_taken') and self.task.actions_taken:
            prev_frame = ttk.LabelFrame(scrollable_frame, text="Previous Actions", padding=10)
            prev_frame.pack(fill=X)

            prev_text = tk.Text(prev_frame, height=6, wrap='word', state='disabled')
            prev_text.pack(fill=X)

            # Display previous actions
            prev_text.config(state='normal')
            for action in self.task.actions_taken[-5:]:  # Show last 5 actions
                prev_text.insert('end', f"{action.timestamp} - {action.user}\n")
                prev_text.insert('end', f"{action.description}\n\n")
            prev_text.config(state='disabled')

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_team_tab(self, parent):
        """Create team assignment modification tab"""
        # Current team
        current_frame = ttk.LabelFrame(parent, text="Current Team Assignment", padding=10)
        current_frame.pack(fill=X, pady=(0, 10))

        if self.selected_members:
            current_text = ", ".join([m.name for m in self.selected_members])
        else:
            current_text = "No team members assigned"

        ttk.Label(current_frame, text=current_text, wraplength=700).pack()

        # Modify team
        modify_frame = ttk.LabelFrame(parent, text="Modify Team Assignment", padding=10)
        modify_frame.pack(fill=BOTH, expand=True)

        # Instructions
        ttk.Label(modify_frame,
                  text="Select team members to add or remove from this task:",
                  font=('Arial', 10)).pack(pady=(0, 10))

        # Search
        search_frame = ttk.Frame(modify_frame)
        search_frame.pack(fill=X, pady=(0, 10))

        ttk.Label(search_frame, text="Search:").pack(side=LEFT, padx=(0, 5))
        self.member_search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.member_search_var)
        search_entry.pack(side=LEFT, fill=X, expand=True)
        search_entry.bind('<KeyRelease>', self.filter_members)

        # Member selection frame
        select_frame = ttk.Frame(modify_frame)
        select_frame.pack(fill=BOTH, expand=True)

        # Canvas for scrolling
        canvas = tk.Canvas(select_frame, height=300)
        scrollbar = ttk.Scrollbar(select_frame, orient="vertical", command=canvas.yview)
        self.member_frame = ttk.Frame(canvas)

        self.member_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.member_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Create member checkboxes
        self.member_vars = {}
        self.create_member_checkboxes()

        # Quick actions
        action_frame = ttk.Frame(modify_frame)
        action_frame.pack(fill=X, pady=10)

        ttk.Button(
            action_frame,
            text="Select All",
            command=self.select_all_members
        ).pack(side=LEFT, padx=5)

        ttk.Button(
            action_frame,
            text="Clear All",
            command=self.clear_all_members
        ).pack(side=LEFT)

    def create_member_checkboxes(self):
        """Create checkboxes for team members"""
        # Clear existing
        for widget in self.member_frame.winfo_children():
            widget.destroy()

        search_term = self.member_search_var.get().lower()

        # Group by department
        departments = {}
        for member in self.team_members:
            if search_term and search_term not in member.name.lower():
                continue

            dept = member.department
            if dept not in departments:
                departments[dept] = []
            departments[dept].append(member)

        # Display members
        for dept, members in sorted(departments.items()):
            if members:
                # Department header
                dept_label = ttk.Label(self.member_frame, text=dept,
                                       font=('Arial', 10, 'bold'))
                dept_label.pack(anchor=W, pady=(10, 5))

                # Member checkboxes
                for member in members:
                    var = tk.BooleanVar()
                    # Check if currently assigned
                    var.set(member in self.selected_members)
                    self.member_vars[member.email] = (var, member)

                    frame = ttk.Frame(self.member_frame)
                    frame.pack(fill=X, padx=(20, 0))

                    check = ttk.Checkbutton(
                        frame,
                        text=f"{member.name} ({member.role})",
                        variable=var
                    )
                    check.pack(side=LEFT)

                    # Show if being added/removed
                    if member in self.selected_members and not var.get():
                        ttk.Label(frame, text="(will be removed)",
                                  foreground='red').pack(side=LEFT, padx=10)
                    elif member not in self.selected_members and var.get():
                        ttk.Label(frame, text="(will be added)",
                                  foreground='green').pack(side=LEFT, padx=10)

    def filter_members(self, event=None):
        """Filter members based on search"""
        self.create_member_checkboxes()

    def select_all_members(self):
        """Select all visible members"""
        for var, member in self.member_vars.values():
            var.set(True)

    def clear_all_members(self):
        """Clear all member selections"""
        for var, member in self.member_vars.values():
            var.set(False)

    def create_files_tab(self, parent):
        """Create file attachments tab"""
        # Current files
        current_frame = ttk.LabelFrame(parent, text="Current Attachments", padding=10)
        current_frame.pack(fill=X, pady=(0, 10))

        if hasattr(self.task, 'file_attachments') and self.task.file_attachments:
            for file_path in self.task.file_attachments:
                file_frame = ttk.Frame(current_frame)
                file_frame.pack(fill=X, pady=2)

                ttk.Label(file_frame, text=os.path.basename(file_path)).pack(side=LEFT)

                ttk.Button(
                    file_frame,
                    text="Open",
                    command=lambda p=file_path: self.open_file(p)
                ).pack(side=RIGHT, padx=5)
        else:
            ttk.Label(current_frame, text="No attachments").pack()

        # Add new files
        new_frame = ttk.LabelFrame(parent, text="Add New Attachments", padding=10)
        new_frame.pack(fill=BOTH, expand=True)

        # File list
        self.file_listbox = tk.Listbox(new_frame, height=6)
        self.file_listbox.pack(fill=BOTH, expand=True, pady=(0, 10))

        # Buttons
        btn_frame = ttk.Frame(new_frame)
        btn_frame.pack(fill=X)

        ttk.Button(
            btn_frame,
            text="Add Files",
            command=self.add_files
        ).pack(side=LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="Remove Selected",
            command=self.remove_file
        ).pack(side=LEFT)

    def create_info_tab(self, parent):
        """Create task information tab"""
        # Scrollable frame
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        info_frame = ttk.Frame(canvas)

        info_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=info_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Task details
        details = [
            ("Task ID", self.task.key),
            ("Title", self.task.title),
            ("Compliance Area", self.task.compliance_area),
            ("Priority", self.task.priority),
            ("Created By", getattr(self.task, 'created_by', 'Unknown')),
            ("Created Date", self.task.created_date),
            ("Target Date", self.task.target_date)
        ]

        for label, value in details:
            frame = ttk.Frame(info_frame)
            frame.pack(fill=X, pady=2)

            ttk.Label(frame, text=f"{label}:", width=20).pack(side=LEFT)
            ttk.Label(frame, text=value, font=('Arial', 9, 'bold')).pack(side=LEFT)

        # Description
        desc_frame = ttk.LabelFrame(info_frame, text="Description", padding=10)
        desc_frame.pack(fill=X, pady=10)

        desc_text = tk.Text(desc_frame, height=5, wrap='word', state='disabled')
        desc_text.pack(fill=X)

        if hasattr(self.task, 'description'):
            desc_text.config(state='normal')
            desc_text.insert('1.0', self.task.description)
            desc_text.config(state='disabled')

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def open_file(self, file_path):
        """Open file in default application"""
        try:
            import subprocess
            import platform

            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.call(('open', file_path))
            else:  # linux
                subprocess.call(('xdg-open', file_path))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {str(e)}")

    def add_files(self):
        """Add new file attachments"""
        from tkinter import filedialog

        files = filedialog.askopenfilenames(
            parent=self,
            title="Select files to attach"
        )

        for file in files:
            if file not in self.new_files:
                self.new_files.append(file)
                self.file_listbox.insert(tk.END, os.path.basename(file))

    def remove_file(self):
        """Remove selected file from new files"""
        selection = self.file_listbox.curselection()
        if selection:
            index = selection[0]
            self.file_listbox.delete(index)
            del self.new_files[index]

    def validate_input(self) -> Tuple[bool, str]:
        """Validate update input"""
        # Check if any changes made
        actions = self.actions_text.get('1.0', 'end-1c').strip()

        if not actions and self.status_var.get() == self.task.status:
            # Check if team changes
            new_members = []
            for var, member in self.member_vars.values():
                if var.get():
                    new_members.append(member)

            if set(new_members) == set(self.selected_members) and not self.new_files:
                return False, "No changes have been made to the task"

        return True, ""

    def ok(self):
        """Handle OK button - save updates"""
        valid, message = self.validate_input()
        if not valid:
            messagebox.showwarning("No Changes", message)
            return

        # Prepare update data
        self.result = {
            'status': self.status_var.get(),
            'progress': self.progress_var.get(),
            'actions_taken': self.actions_text.get('1.0', 'end-1c').strip()
        }

        # Get updated team members
        new_members = []
        for var, member in self.member_vars.values():
            if var.get():
                new_members.append(member)

        # Determine team changes
        added_members = [m for m in new_members if m not in self.selected_members]
        removed_members = [m for m in self.selected_members if m not in new_members]

        if added_members or removed_members:
            self.result['allocated_to'] = [m.name for m in new_members]
            self.result['allocated_emails'] = [m.email for m in new_members]
            self.result['team_changes'] = {
                'added': [(m.name, m.email) for m in added_members],
                'removed': [(m.name, m.email) for m in removed_members]
            }

        # Add new files if any
        if self.new_files:
            self.result['new_files'] = self.new_files

        self.destroy()


# Add __all__ at the end of the file for explicit exports
__all__ = [
    'BaseDialog',
    'TaskDialog',
    'TeamMemberDialog',
    'ConfirmDialog',
    'ProgressDialog',
    'FilePickerDialog',
    'DateRangeDialog',
    'SearchDialog',
    'ExportDialog',
    'CustomReportDialog',
    'LoginDialog',
    'SettingsDialog',
    'HelpDialog'
]