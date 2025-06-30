# ui/styles.py
"""
UI styling constants and theme management
Provides consistent styling across the application
"""

from dataclasses import dataclass
from typing import Dict, Tuple, Optional, List
import json
from pathlib import Path

from config.settings import get_config


@dataclass
class ColourScheme:
    """Colour scheme definition"""
    primary: str
    secondary: str
    success: str
    danger: str
    warning: str
    info: str
    light: str
    dark: str
    background: str
    surface: str
    text_primary: str
    text_secondary: str
    border: str

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary"""
        return self.__dict__


@dataclass
class FontScheme:
    """Font scheme definition"""
    family_default: str = "Segoe UI"
    family_heading: str = "Segoe UI"
    family_mono: str = "Consolas"

    size_tiny: int = 8
    size_small: int = 9
    size_normal: int = 10
    size_medium: int = 11
    size_large: int = 14
    size_xlarge: int = 16
    size_xxlarge: int = 20
    size_title: int = 24

    weight_normal: str = "normal"
    weight_bold: str = "bold"

    def get_font(self, size: str = 'normal', weight: str = 'normal', family: str = 'default') -> Tuple[str, int, str]:
        """Get font tuple for tkinter"""
        size_map = {
            'tiny': self.size_tiny,
            'small': self.size_small,
            'normal': self.size_normal,
            'medium': self.size_medium,
            'large': self.size_large,
            'xlarge': self.size_xlarge,
            'xxlarge': self.size_xxlarge,
            'title': self.size_title,
            'heading1': self.size_xxlarge,
            'heading2': self.size_xlarge,
            'heading3': self.size_large,
            'caption': self.size_small
        }

        family_map = {
            'default': self.family_default,
            'heading': self.family_heading,
            'mono': self.family_mono
        }

        font_size = size_map.get(size, self.size_normal)
        font_family = family_map.get(family, self.family_default)

        return (font_family, font_size, weight)


@dataclass
class SpacingScheme:
    """Spacing scheme definition"""
    xs: int = 2
    sm: int = 5
    md: int = 10
    lg: int = 15
    xl: int = 20
    xxl: int = 30


class UIStyles:
    """Central UI styling configuration"""

    # Predefined colour schemes
    COLOUR_SCHEMES = {
        'default': ColourScheme(
            primary='#1976D2',
            secondary='#424242',
            success='#4CAF50',
            danger='#F44336',
            warning='#FF9800',
            info='#2196F3',
            light='#F5F5F5',
            dark='#212121',
            background='#FFFFFF',
            surface='#FAFAFA',
            text_primary='#212121',
            text_secondary='#757575',
            border='#E0E0E0'
        ),
        'dark': ColourScheme(
            primary='#2196F3',
            secondary='#616161',
            success='#66BB6A',
            danger='#EF5350',
            warning='#FFA726',
            info='#42A5F5',
            light='#424242',
            dark='#121212',
            background='#121212',
            surface='#1E1E1E',
            text_primary='#FFFFFF',
            text_secondary='#B0B0B0',
            border='#333333'
        ),
        'professional': ColourScheme(
            primary='#0D47A1',
            secondary='#37474F',
            success='#1B5E20',
            danger='#B71C1C',
            warning='#E65100',
            info='#01579B',
            light='#ECEFF1',
            dark='#263238',
            background='#FAFAFA',
            surface='#FFFFFF',
            text_primary='#263238',
            text_secondary='#546E7A',
            border='#CFD8DC'
        )
    }

    # Current active colours
    COLOURS = COLOUR_SCHEMES['default']

    # Font schemes
    FONTS = FontScheme()

    # Spacing
    SPACING = SpacingScheme()

    # Icons
    ICONS = {
        # Navigation
        'home': '🏠',
        'back': '←',
        'forward': '→',
        'up': '↑',
        'down': '↓',
        'menu': '☰',

        # Actions
        'plus': '+',
        'add': '+',
        'delete': '🗑',
        'edit': '✏',
        'save': '💾',
        'cancel': '✖',
        'close': '✖',
        'refresh': '🔄',
        'search': '🔍',
        'filter': '🔽',
        'sort': '⇅',
        'export': '📤',
        'import': '📥',
        'print': '🖨',

        # Status
        'check': '✓',
        'error': '✖',
        'warning': '⚠',
        'info': 'ℹ',
        'question': '?',
        'star': '★',
        'flag': '🚩',

        # Task status
        'status_open': '○',
        'status_progress': '◐',
        'status_resolved': '●',
        'status_closed': '✓',

        # Priority
        'priority_critical': '🔴',
        'priority_high': '🟠',
        'priority_medium': '🟡',
        'priority_low': '🟢',

        # File types
        'file': '📄',
        'folder': '📁',
        'attachment': '📎',
        'document': '📃',
        'spreadsheet': '📊',
        'pdf': '📕',

        # Other
        'user': '👤',
        'team': '👥',
        'email': '✉',
        'calendar': '📅',
        'clock': '🕐',
        'settings': '⚙',
        'lock': '🔒',
        'unlock': '🔓',
        'notification': '🔔'
    }

    # Widget styles
    BUTTON_STYLES = {
        'default': {
            'style': 'TButton',
            'cursor': 'hand2'
        },
        'primary': {
            'style': 'Primary.TButton',
            'cursor': 'hand2'
        },
        'secondary': {
            'style': 'Secondary.TButton',
            'cursor': 'hand2'
        },
        'success': {
            'style': 'Success.TButton',
            'cursor': 'hand2'
        },
        'danger': {
            'style': 'Danger.TButton',
            'cursor': 'hand2'
        },
        'warning': {
            'style': 'Warning.TButton',
            'cursor': 'hand2'
        },
        'info': {
            'style': 'Info.TButton',
            'cursor': 'hand2'
        },
        'link': {
            'style': 'Link.TButton',
            'cursor': 'hand2'
        }
    }

    ENTRY_STYLES = {
        'default': {
            'style': 'TEntry'
        },
        'search': {
            'style': 'Search.TEntry'
        },
        'error': {
            'style': 'Error.TEntry'
        }
    }

    LABEL_STYLES = {
        'default': {},
        'heading1': {
            'font': ('Segoe UI', 20, 'bold')
        },
        'heading2': {
            'font': ('Segoe UI', 16, 'bold')
        },
        'heading3': {
            'font': ('Segoe UI', 14, 'bold')
        },
        'caption': {
            'font': ('Segoe UI', 9, 'normal')
        },
        'error': {
            'foreground': '#F44336'
        },
        'success': {
            'foreground': '#4CAF50'
        }
    }

    FRAME_STYLES = {
        'default': {
            'padding': 0
        },
        'card': {
            'padding': 15,
            'relief': 'solid',
            'borderwidth': 1
        },
        'section': {
            'padding': 10
        }
    }

    TABLE_STYLES = {
        'default': {
            'show': 'tree headings',
            'selectmode': 'browse'
        },
        'multi': {
            'show': 'tree headings',
            'selectmode': 'extended'
        }
    }

    @classmethod
    def get_status_colour(cls, status: str) -> str:
        """Get colour for status"""
        status_colours = {
            'Open': cls.COLOURS.warning,
            'In Progress': cls.COLOURS.info,
            'Pending Approval': cls.COLOURS.warning,
            'Approved': cls.COLOURS.success,
            'Resolved': cls.COLOURS.success,
            'Closed': cls.COLOURS.secondary,
            'On Hold': cls.COLOURS.secondary
        }
        return status_colours.get(status, cls.COLOURS.secondary)

    @classmethod
    def get_priority_colour(cls, priority: str) -> str:
        """Get colour for priority"""
        priority_colours = {
            'Critical': cls.COLOURS.danger,
            'High': cls.COLOURS.warning,
            'Medium': cls.COLOURS.info,
            'Low': cls.COLOURS.success
        }
        return priority_colours.get(priority, cls.COLOURS.secondary)

    @classmethod
    def get_status_icon(cls, status: str) -> str:
        """Get icon for status"""
        icons = {
            'Open': cls.ICONS['status_open'],
            'In Progress': cls.ICONS['status_progress'],
            'Resolved': cls.ICONS['status_resolved'],
            'Closed': cls.ICONS['status_closed']
        }
        return icons.get(status, '')

    @classmethod
    def set_theme(cls, theme_name: str):
        """Set the current theme"""
        if theme_name in cls.COLOUR_SCHEMES:
            cls.COLOURS = cls.COLOUR_SCHEMES[theme_name]


class ThemeManager:
    """Manages application themes"""

    def __init__(self):
        try:
            self.config = get_config()
        except:
            # Fallback if config not available
            self.config = None

        self.current_theme = 'default'
        self.custom_themes = self._load_custom_themes()
        self.fonts = FontScheme()
        self.spacing = SpacingScheme()
        self.colours = UIStyles.COLOUR_SCHEMES[self.current_theme]

    def _load_custom_themes(self) -> Dict[str, ColourScheme]:
        """Load custom themes from configuration"""
        custom_themes = {}

        if not self.config:
            return custom_themes

        # Load from JSON file if exists
        theme_file = Path(self.config.base_path) / "themes.json"
        if theme_file.exists():
            try:
                with open(theme_file, 'r') as f:
                    theme_data = json.load(f)
                    for name, colours in theme_data.items():
                        custom_themes[name] = ColourScheme(**colours)
            except Exception as e:
                print(f"Error loading custom themes: {e}")

        return custom_themes

    def get_theme(self, name: str) -> Optional[ColourScheme]:
        """Get theme by name"""
        # Check built-in themes
        if name in UIStyles.COLOUR_SCHEMES:
            return UIStyles.COLOUR_SCHEMES[name]

        # Check custom themes
        if name in self.custom_themes:
            return self.custom_themes[name]

        return None

    def set_theme(self, name: str) -> bool:
        """Set current theme"""
        theme = self.get_theme(name)
        if theme:
            self.current_theme = name
            self.colours = theme
            UIStyles.set_theme(name)
            return True
        return False

    def get_available_themes(self) -> List[str]:
        """Get list of available themes"""
        built_in = list(UIStyles.COLOUR_SCHEMES.keys())
        custom = list(self.custom_themes.keys())
        return built_in + custom

    def create_custom_theme(self, name: str, colours: Dict[str, str]) -> bool:
        """Create and save custom theme"""
        if not self.config:
            return False

        try:
            # Create theme
            theme = ColourScheme(**colours)
            self.custom_themes[name] = theme

            # Save to file
            theme_file = Path(self.config.base_path) / "themes.json"
            all_custom = {
                name: theme.to_dict()
                for name, theme in self.custom_themes.items()
            }

            with open(theme_file, 'w') as f:
                json.dump(all_custom, f, indent=2)

            return True

        except Exception as e:
            print(f"Error creating custom theme: {e}")
            return False

    def get_colour(self, colour_name: str) -> str:
        """Get colour value by name"""
        return getattr(self.colours, colour_name, '#000000')

    def get_widget_style(self, widget_type: str, style_name: str = 'default') -> Dict:
        """Get style configuration for a widget type"""
        style_map = {
            'button': UIStyles.BUTTON_STYLES,
            'entry': UIStyles.ENTRY_STYLES,
            'label': UIStyles.LABEL_STYLES,
            'frame': UIStyles.FRAME_STYLES,
            'table': UIStyles.TABLE_STYLES
        }

        if widget_type in style_map:
            return style_map[widget_type].get(style_name, {})

        return {}

    def apply_theme_to_widget(self, widget, widget_type: str, style_name: str = 'default'):
        """Apply theme styling to a widget"""
        style = self.get_widget_style(widget_type, style_name)

        # Apply common styles
        for attr, value in style.items():
            if hasattr(widget, 'configure'):
                try:
                    widget.configure(**{attr: value})
                except:
                    pass


# Global theme manager instance
_theme_manager = None


def get_theme_manager() -> ThemeManager:
    """Get global theme manager instance"""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager