# config/settings.py
"""
Central configuration management for Compliance System
All settings are centralised here for easy management
"""

import os
import json  # Added missing import
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class AppConfig:
    """Application configuration with all settings"""
    # Application Info
    app_name: str = "Compliance Manager"
    version: str = "4.0"
    author: str = "Vaughan De Sousa"
    company: str = "Sysco Guest Supply"

    # Paths
    shared_drive: str = "H:/Compliance/ComplianceSystem"
    local_fallback: Optional[str] = None
    base_path: Optional[Path] = None

    # UI Settings
    theme: str = "superhero"
    window_size: str = "1400x900"
    min_window_size: str = "1200x800"
    font_family: str = "Segoe UI"
    font_size: int = 10

    # Auto-refresh
    auto_refresh_interval: int = 15  # seconds
    manual_refresh_enabled: bool = True
    refresh_interval_seconds: int = 300  # 5 minutes

    # File Settings
    allowed_extensions: List[str] = field(default_factory=lambda: [
        '.pdf', '.docx', '.xlsx', '.doc', '.xls', '.png', '.jpg', '.jpeg',
        '.msg', '.eml', '.txt', '.csv', '.pptx', '.ppt'
    ])
    max_file_size_mb: int = 50

    # Email Configuration
    smtp_server: str = "smtp.office365.com"
    smtp_port: int = 587
    smtp_use_tls: bool = True
    email_from: str = "compliance@guestsupply.co.uk"
    email_reply_to: str = "compliance@guestsupply.co.uk"
    compliance_email: str = "compliance@guestsupply.co.uk"  # Added missing field
    email_templates_path: str = "resources/templates"

    # Data Management
    data_folder: str = "Data"
    archive_folder: str = "Archives"
    attachment_folder: str = "Attachments"
    export_folder: str = "Exports"
    log_folder: str = "Logs"

    excel_files: Dict[str, str] = field(default_factory=lambda: {
        'tasks': 'Task_Log.xlsx',
        'team': 'Team_Data.xlsx',  # Fixed truncated value
        'legislation': 'Legislation_References.xlsx',
        'archives': 'Archive_Index.xlsx',  # Added missing key
        'indices': 'Search_Index.xlsx'  # Added missing key
    })

    # Compliance Categories
    compliance_areas: Dict[str, List[str]] = field(default_factory=lambda: {
        "IT Security & Data Protection": [
            "Data Protection", "Cybersecurity", "Access Control",
            "Data Retention", "Incident Response", "Other"
        ],
        "Product Liability & Traceability": [
            "Product Safety", "Labelling", "Recalls", "Traceability",
            "Quality Control", "Other"
        ],
        "Restricted Practices & Trade": [
            "Export Controls", "Sanctions", "Anti-Competition",
            "Trade Agreements", "Other"
        ],
        "Legal & Contractual": [
            "Contract Management", "Intellectual Property", "Disputes",
            "Corporate Governance", "Other"
        ],
        "Environmental & Sustainability": [
            "Waste Management", "Emissions", "Energy Efficiency",
            "Sustainable Sourcing", "Other"
        ],
        "Health & Safety": [
            "Workplace Safety", "Risk Assessments", "Safety Training", "Incident Reports",
            "Equipment Checks", "Emergency Procedures", "Other"
        ],
        "Data Protection": [
            "GDPR Compliance", "Data Requests", "Privacy Policies",
            "Data Breaches", "Training", "Other"
        ],
        "Financial": [
            "Tax Compliance", "Financial Reporting", "Audits",
            "Regulatory Returns", "Other"
        ],
        "Operational": [
            "General Compliance", "Process Updates", "System Changes",
            "Documentation", "Other"
        ]
    })

    # Priority Options
    priority_options: List[str] = field(default_factory=lambda: [
        "Critical", "High", "Medium", "Low"
    ])

    status_options: List[str] = field(default_factory=lambda: [
        "Open", "In Progress", "Pending Approval", "Sent For Approval",
        "Approved", "Resolved", "Closed", "On Hold"
    ])

    # Manager Approval Settings
    approval_required_statuses: List[str] = field(default_factory=lambda: [
        "Pending Approval", "Sent For Approval"
    ])
    approval_levels: int = 2

    # Business rules
    task_reminder_days: List[int] = field(default_factory=lambda: [7, 3, 1])
    session_timeout_minutes: int = 30
    archive_after_days: int = 90  # Added missing field

    # Performance settings
    max_search_results: int = 100
    cache_size_mb: int = 50

    # Feature flags
    enable_notifications: bool = True
    enable_auto_save: bool = True
    enable_audit_trail: bool = True
    enable_file_locking: bool = True

    # Legislative References
    legislation_categories: Dict[str, List[str]] = field(default_factory=lambda: {
        "UK Regulations": [
            "UK GDPR", "Data Protection Act 2018", "Bribery Act 2010",
            "Modern Slavery Act 2015", "Companies Act 2006", "Consumer Rights Act 2015"
        ],
        "EU Regulations": [
            "EU GDPR", "REACH Regulation", "Packaging Waste Directive",
            "Product Liability Directive", "CSDDD", "Cosmetics Regulation"
        ],
        "Trade & Customs": [
            "UK Customs Act", "Export Control Order", "Trade Sanctions",
            "Dual-Use Regulation", "Rules of Origin"
        ],
        "Industry Specific": [
            "FCA Handbook", "PRA Rulebook", "ISO Standards",
            "GMP Guidelines", "HACCP Requirements"
        ]
    })

    # Search Settings
    search_index_fields: List[str] = field(default_factory=lambda: [
        'Task Key', 'Title', 'Description', 'Task Setter', 'Allocated To',
        'Compliance Area', 'Subcategory', 'Status', 'Priority'
    ])

    # Email settings from constants
    EMAIL_MAX_RECIPIENTS: int = 50
    EMAIL_SUBJECT_PREFIX: str = "[Compliance System]"
    EMAIL_RETRY_ATTEMPTS: int = 3
    EMAIL_RETRY_DELAY_SECONDS: int = 60

    # UI constants from constants
    WINDOW_MIN_WIDTH: int = 1200
    WINDOW_MIN_HEIGHT: int = 800
    TABLE_ROW_HEIGHT: int = 25
    DIALOG_WIDTH: int = 600
    DIALOG_HEIGHT: int = 400

    # Logging
    log_level: str = "INFO"
    log_file: str = "compliance_system.log"
    log_max_size_mb: int = 10
    log_backup_count: int = 5

    def __post_init__(self):
        """Initialize paths after creation"""
        if self.local_fallback is None:
            self.local_fallback = str(Path.home() / "ComplianceSystem")

        # Try to determine base path
        try:
            if Path(self.shared_drive).exists():
                self.base_path = Path(self.shared_drive)
            else:
                self.base_path = Path(self.local_fallback)
        except Exception as e:  # More specific exception handling
            print(f"Warning: Could not access shared drive: {e}")
            self.base_path = Path(self.local_fallback)

    def get_excel_path(self, file_type: str) -> Path:
        """Get full path for an Excel file"""
        if file_type in self.excel_files:
            return self.base_path / self.data_folder / self.excel_files[file_type]  # Fixed truncated reference
        raise ValueError(f"Unknown file type: {file_type}")

    def get_archive_path(self, year: int, month: int) -> Path:
        """Get archive path for a specific period"""
        archive_base = self.base_path / self.archive_folder
        return archive_base / str(year) / f"{month:02d}"

    def get_attachment_path(self, task_key: str) -> Path:
        """Get attachment path for a task"""
        return self.base_path / self.attachment_folder / task_key

    def get_export_path(self, export_type: str) -> Path:
        """Get export path with timestamp"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{export_type}_{timestamp}.xlsx"
        return self.base_path / self.export_folder / filename

    def get_log_path(self) -> Path:
        """Get log file path"""
        from datetime import datetime
        date_str = datetime.now().strftime("%Y%m%d")
        return self.base_path / self.log_folder / f"compliance_{date_str}.log"

    def to_dict(self) -> dict:
        """Convert config to dictionary"""
        return {
            k: str(v) if isinstance(v, Path) else v
            for k, v in self.__dict__.items()
            if not k.startswith('_')
        }

    def save_to_file(self, config_file: str = "config.json"):
        """Save configuration to file"""
        with open(config_file, 'w') as f:
            json.dump(self.to_dict(), f, indent=4)


# Singleton instance
_config_instance = None


def get_config() -> AppConfig:
    """Get the singleton configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = AppConfig()
    return _config_instance


def reset_config():
    """Reset configuration (mainly for testing)"""
    global _config_instance
    _config_instance = None