# ui/components/base_components.py
"""
Base UI components for the Compliance Management System
Fixed version with proper placeholder handling
"""

import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from datetime import datetime, date
from typing import Optional, Callable, Any, List, Tuple

from ui.styles import UIStyles

# Constants
LEFT = tk.LEFT
RIGHT = tk.RIGHT
TOP = tk.TOP
BOTTOM = tk.BOTTOM
BOTH = tk.BOTH
X = tk.X
Y = tk.Y
W = tk.W
E = tk.E
N = tk.N
S = tk.S
EW = tk.EW
NS = tk.NS
NSEW = tk.NSEW
CENTER = tk.CENTER
TRUE = True
FALSE = False


class ModernFrame(ttk.Frame):
    """Enhanced frame with optional border and padding"""

    def __init__(self, parent, padding: int = 0, border: bool = False, **kwargs):
        # Apply styling
        if border:
            kwargs['relief'] = 'solid'
            kwargs['borderwidth'] = 1

        super().__init__(parent, padding=padding, **kwargs)


class ModernButton(ttk.Button):
    """Enhanced button with icon support"""

    def __init__(self, parent, text: str = "", icon: str = "",
                 style_type: str = "primary", **kwargs):
        # Map style types to button styles
        style_map = {
            'primary': 'primary.TButton',
            'secondary': 'secondary.TButton',
            'success': 'success.TButton',
            'danger': 'danger.TButton',
            'warning': 'warning.TButton',
            'info': 'info.TButton',
            'outline': 'outline.TButton',
            'link': 'link.TButton'
        }

        # Set style
        if 'style' not in kwargs:
            kwargs['style'] = style_map.get(style_type, 'primary.TButton')

        # Add icon to text if provided
        if icon:
            icon_char = UIStyles.ICONS.get(icon, icon)
            display_text = f"{icon_char} {text}" if text else icon_char
        else:
            display_text = text

        super().__init__(parent, text=display_text, **kwargs)


class ModernEntry(ttk.Entry):
    """Enhanced entry with placeholder support - FIXED"""

    def __init__(self, parent, placeholder: str = "", **kwargs):
        # Extract show parameter if provided (for password fields)
        self.show_char = kwargs.pop('show', '')

        super().__init__(parent, **kwargs)

        self.placeholder = placeholder
        self.placeholder_color = '#999999'
        self.default_fg_color = self['foreground'] if 'foreground' in kwargs else '#000000'
        self.placeholder_active = False

        if self.placeholder:
            self._setup_placeholder()

    def _setup_placeholder(self):
        """Setup placeholder functionality"""
        # Bind events
        self.bind('<FocusIn>', self._on_focus_in)
        self.bind('<FocusOut>', self._on_focus_out)

        # Show placeholder initially
        if not self.get():
            self._show_placeholder()

    def _show_placeholder(self):
        """Show placeholder text"""
        if not self.get():
            self.placeholder_active = True
            self['foreground'] = self.placeholder_color
            if self.show_char:
                self.configure(show='')  # Show placeholder text normally
            self.insert(0, self.placeholder)

    def _hide_placeholder(self):
        """Hide placeholder text"""
        if self.placeholder_active:
            self.delete(0, 'end')
            self['foreground'] = self.default_fg_color
            if self.show_char:
                self.configure(show=self.show_char)  # Restore password masking
            self.placeholder_active = False

    def _on_focus_in(self, event):
        """Handle focus in event"""
        self._hide_placeholder()

    def _on_focus_out(self, event):
        """Handle focus out event"""
        if not self.get():
            self._show_placeholder()

    def get_value(self):
        """Get the real value (excluding placeholder)"""
        if self.placeholder_active:
            return ""
        return self.get()

    def set_value(self, value: str):
        """Set the entry value"""
        self._hide_placeholder()
        self.delete(0, 'end')
        if value:
            self.insert(0, value)
        else:
            self._show_placeholder()


class ModernLabel(ttk.Label):
    """Enhanced label with styling options"""

    def __init__(self, parent, text: str = "", style_type: str = 'default', **kwargs):
        # Get style configuration
        style_config = UIStyles.LABEL_STYLES.get(style_type, {})

        # Merge configurations
        for key, value in style_config.items():
            if key not in kwargs:
                kwargs[key] = value

        super().__init__(parent, text=text, **kwargs)


class SearchBar(ttk.Frame):
    """Search bar component - FIXED"""

    def __init__(self, parent, callback: Optional[Callable[[str], None]] = None,
                 placeholder: str = "Search...", **kwargs):
        super().__init__(parent, **kwargs)

        self.callback = callback
        self.search_var = tk.StringVar()

        # Search icon
        icon_label = ttk.Label(self, text=UIStyles.ICONS.get('search', '🔍'))
        icon_label.pack(side=LEFT, padx=(5, 0))

        # Search entry with proper placeholder
        self.search_entry = ModernEntry(
            self,
            placeholder=placeholder,
            textvariable=self.search_var
        )
        self.search_entry.pack(side=LEFT, fill=X, expand=True, padx=5)

        # Bind events for live search
        self.search_var.trace('w', self._on_search_change)
        self.search_entry.bind('<Return>', self._on_search_enter)

        # Clear button (initially hidden)
        self.clear_btn = ttk.Button(
            self,
            text=UIStyles.ICONS.get('close', '✕'),
            width=3,
            command=self.clear_search
        )

    def _on_search_change(self, *args):
        """Handle search text change"""
        query = self.search_var.get()

        # Show/hide clear button
        if query and not self.search_entry.placeholder_active:
            if not self.clear_btn.winfo_ismapped():
                self.clear_btn.pack(side=RIGHT, padx=(0, 5))
        else:
            self.clear_btn.pack_forget()

        # Trigger callback
        if self.callback:
            self.callback(self.search_entry.get_value())

    def _on_search_enter(self, event):
        """Handle enter key in search"""
        if self.callback:
            self.callback(self.search_entry.get_value())

    def clear_search(self):
        """Clear search text"""
        self.search_var.set('')
        self.search_entry.set_value('')

    def get_search_text(self) -> str:
        """Get current search text"""
        return self.search_entry.get_value()


class StatusBadge(ttk.Label):
    """Status indicator badge"""

    def __init__(self, parent, status: str, **kwargs):
        # Get status styling
        bg_color = UIStyles.get_status_colour(status)
        icon = UIStyles.get_status_icon(status)

        # Create label with icon and text
        text = f"{icon} {status}" if icon else status

        super().__init__(parent, text=text, **kwargs)

        # Apply styling
        self.configure(
            background=bg_color,
            foreground='white',
            padding=(10, 5)
        )


class PriorityBadge(ttk.Label):
    """Priority indicator badge"""

    def __init__(self, parent, priority: str, **kwargs):
        # Get priority styling
        icon = UIStyles.ICONS.get(f'priority_{priority.lower()}', '')

        # Create label with icon and text
        text = f"{icon} {priority}" if icon else priority

        super().__init__(parent, text=text, **kwargs)

        # Apply styling based on priority
        fg_color = UIStyles.get_priority_colour(priority)
        self.configure(foreground=fg_color)


class DatePicker(ttk.Frame):
    """Date picker component"""

    def __init__(self, parent, callback: Optional[Callable[[date], None]] = None, **kwargs):
        super().__init__(parent, **kwargs)

        self.callback = callback
        self.selected_date = date.today()

        # Create date entry
        self.create_widgets()

    def create_widgets(self):
        """Create date picker widgets"""
        # Date display button
        self.date_button = ttk.Button(
            self,
            text=self.selected_date.strftime('%Y-%m-%d'),
            command=self.show_calendar
        )
        self.date_button.pack(side=LEFT, fill=X, expand=True)

        # Calendar icon
        cal_icon = ttk.Label(self, text=UIStyles.ICONS.get('calendar', '📅'))
        cal_icon.pack(side=RIGHT, padx=(5, 0))

    def show_calendar(self):
        """Show calendar popup"""
        # For now, just show date entry dialog
        # In a full implementation, this would show a calendar widget
        from ui.components.dialogs import DateRangeDialog

        dialog = DateRangeDialog(self)
        self.wait_window(dialog)

        if dialog.result:
            self.set_date(dialog.result['start_date'])

    def set_date(self, new_date: date):
        """Set the selected date"""
        self.selected_date = new_date
        self.date_button.configure(text=new_date.strftime('%Y-%m-%d'))

        if self.callback:
            self.callback(new_date)

    def get_date(self) -> date:
        """Get the selected date"""
        return self.selected_date


class IconButton(ttk.Button):
    """Icon-only button"""

    def __init__(self, parent, icon: str, tooltip: str = "", **kwargs):
        # Get icon character
        icon_char = UIStyles.ICONS.get(icon, icon)

        # Set minimal width
        kwargs['width'] = kwargs.get('width', 3)

        super().__init__(parent, text=icon_char, **kwargs)

        # Add tooltip if provided
        if tooltip:
            ToolTip(self, tooltip)


class ProgressIndicator(ttk.Progressbar):
    """Progress indicator for long operations"""

    def __init__(self, parent, **kwargs):
        kwargs['mode'] = kwargs.get('mode', 'indeterminate')
        super().__init__(parent, **kwargs)
        self.running = False

    def start_progress(self):
        """Start progress animation"""
        if not self.running:
            self.start(10)
            self.running = True

    def stop_progress(self):
        """Stop progress animation"""
        if self.running:
            self.stop()
            self.running = False


class Card(ttk.LabelFrame):
    """Card component for grouping related content"""

    def __init__(self, parent, title: str = "", **kwargs):
        super().__init__(parent, text=title, **kwargs)

        # Add padding by default
        self.configure(padding=kwargs.get('padding', 15))


class MetricCard(ttk.Frame):
    """Metric display card"""

    def __init__(self, parent, title: str, value: str,
                 subtitle: str = "", trend: str = "", **kwargs):
        super().__init__(parent, **kwargs)

        # Add border and padding
        self.configure(relief='solid', borderwidth=1, padding=15)

        # Title
        title_label = ttk.Label(self, text=title, font=('Arial', 9))
        title_label.pack(anchor=W)

        # Value
        value_label = ttk.Label(self, text=value, font=('Arial', 20, 'bold'))
        value_label.pack(anchor=W)

        # Subtitle
        if subtitle:
            sub_label = ttk.Label(self, text=subtitle, font=('Arial', 8))
            sub_label.pack(anchor=W)

        # Trend indicator
        if trend:
            trend_label = ttk.Label(self, text=trend, font=('Arial', 8))
            trend_label.pack(anchor=W)


class Separator(ttk.Separator):
    """Separator line"""

    def __init__(self, parent, orient: str = 'horizontal', **kwargs):
        super().__init__(parent, orient=orient, **kwargs)


class ScrollableFrame(ttk.Frame):
    """Scrollable frame container"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # Create canvas
        self.canvas = tk.Canvas(self, bg='white')
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")


class ToolTip:
    """Tooltip for widgets"""

    def __init__(self, widget, text: str, delay: int = 500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window = None
        self.show_timer = None

        # Bind events
        self.widget.bind('<Enter>', self.on_enter)
        self.widget.bind('<Leave>', self.on_leave)
        self.widget.bind('<ButtonPress>', self.on_leave)

    def on_enter(self, event):
        """Show tooltip after delay"""
        self.show_timer = self.widget.after(self.delay, self.show_tooltip)

    def on_leave(self, event):
        """Hide tooltip"""
        if self.show_timer:
            self.widget.after_cancel(self.show_timer)
            self.show_timer = None
        self.hide_tooltip()

    def show_tooltip(self):
        """Display tooltip"""
        if self.tooltip_window or not self.text:
            return

        x, y, _, _ = self.widget.bbox("insert") if hasattr(self.widget, 'bbox') else (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = ttk.Label(
            tw,
            text=self.text,
            background="#333333",
            foreground="white",
            relief='solid',
            borderwidth=1,
            font=('Arial', 9)
        )
        label.pack()

    def hide_tooltip(self):
        """Hide tooltip"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None