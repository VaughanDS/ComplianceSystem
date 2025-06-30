# main.py
"""
Main entry point for Compliance Management System
Handles application initialization and error recovery
"""

import sys
import os
import pandas as pd
import logging
import traceback
from pathlib import Path
import tkinter as tk
from tkinter import messagebox


# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging early
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('compliance_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def check_requirements():
    """Check if all required packages are installed"""
    required_packages = {
        'pandas': 'pandas',
        'openpyxl': 'openpyxl',
        'ttkbootstrap': 'ttkbootstrap',
        'Pillow': 'PIL',
        'python-dateutil': 'dateutil'
    }

    missing_packages = []

    for package, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        error_msg = (
                "Missing required packages:\n\n" +
                "\n".join(f"  • {pkg}" for pkg in missing_packages) +
                "\n\nPlease install them using:\n" +
                f"pip install {' '.join(missing_packages)}"
        )

        # Try to show error in GUI
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Missing Dependencies", error_msg)
        except:
            print(error_msg)

        return False

    return True


def check_data_directory():
    """Ensure data directory structure exists"""
    from config import get_config

    try:
        config = get_config()
        base_path = config.base_path

        # Create required directories
        directories = [
            base_path,
            base_path / "Documents",
            base_path / "Backups",
            base_path / "Archives",
            base_path / "Indices",
            base_path / "Templates",
            base_path / "Exports"
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        # Create subdirectories for documents by compliance area
        doc_path = base_path / "Documents"
        for area in config.compliance_areas:
            area_path = doc_path / area
            area_path.mkdir(exist_ok=True)

        # Check for Excel files
        excel_files = {
            'tasks': base_path / config.excel_files['tasks'],
            'team': base_path / config.excel_files['team']
        }

        # Create empty Excel files if they don't exist
        import pandas as pd

        if not excel_files['tasks'].exists():
            logger.info("Creating new task log file")
            # Create empty task DataFrame with required columns
            task_columns = [
                'Task ID', 'Key', 'Title', 'Date Logged', 'Compliance Area',
                'Subcategory', 'Task Setter', 'Task Setter Email',
                'Allocated To', 'Allocated Emails', 'Manager', 'Manager Email',
                'Priority', 'Status', 'Description', 'Target Date',
                'File Paths', 'Actions Taken', 'Created By', 'Created Date',
                'Last Updated By', 'Last Updated Date'
            ]
            df_tasks = pd.DataFrame(columns=task_columns)
            df_tasks.to_excel(excel_files['tasks'], index=False)

        if not excel_files['team'].exists():
            logger.info("Creating new team data file")
            # Create empty team DataFrame with required columns
            team_columns = [
                'Name', 'Email', 'Department', 'Role', 'Manager',
                'Active', 'Permissions', 'Created Date', 'Created By',
                'Last Updated Date', 'Last Updated By'
            ]
            df_team = pd.DataFrame(columns=team_columns)

            # Add default admin user
            admin_user = {
                'Name': 'System Administrator',
                'Email': 'admin@company.com',
                'Department': 'IT',
                'Role': 'System Administrator',
                'Manager': '',
                'Active': True,
                'Permissions': ['admin', 'create_tasks', 'update_tasks',
                                'delete_tasks', 'manage_team', 'view_reports',
                                'export_data', 'approve_tasks', 'manage_compliance'],
                'Created Date': pd.Timestamp.now().strftime("%Y-%m-%d"),
                'Created By': 'System',
                'Last Updated Date': '',
                'Last Updated By': ''
            }
            df_team = pd.concat([df_team, pd.DataFrame([admin_user])], ignore_index=True)
            df_team.to_excel(excel_files['team'], index=False)

        return True

    except Exception as e:
        logger.error(f"Error setting up data directory: {e}")
        return False


def check_network_access():
    """Check if shared drive is accessible"""
    from config import get_config

    config = get_config()

    # Check if using shared drive
    if str(config.base_path).startswith(('H:', 'Z:', '\\\\')):
        if not config.base_path.exists():
            logger.warning(f"Shared drive not accessible: {config.base_path}")

            # Try to use local fallback
            if config.local_fallback:
                local_path = Path(config.local_fallback)
                if local_path.exists():
                    logger.info(f"Using local fallback: {local_path}")
                    config.base_path = local_path
                    return True

            # Show warning
            try:
                root = tk.Tk()
                root.withdraw()
                result = messagebox.askyesno(
                    "Network Drive Not Accessible",
                    f"Cannot access shared drive:\n{config.base_path}\n\n"
                    "Do you want to continue with local storage?\n"
                    "(Data will not be shared with other users)"
                )

                if result:
                    # Use local storage
                    local_path = Path.home() / "ComplianceSystem"
                    local_path.mkdir(exist_ok=True)
                    config.base_path = local_path
                    config.local_fallback = str(local_path)
                    logger.info(f"Using local storage: {local_path}")
                    return True
                else:
                    return False

            except:
                return False

    return True


def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # Log the exception
    logger.error(
        "Uncaught exception",
        exc_info=(exc_type, exc_value, exc_traceback)
    )

    # Format error message
    error_msg = f"{exc_type.__name__}: {exc_value}"

    # Show error dialog
    try:
        root = tk.Tk()
        root.withdraw()

        # Detailed error for log
        detailed_error = ''.join(traceback.format_exception(
            exc_type, exc_value, exc_traceback
        ))

        # Show user-friendly error
        messagebox.showerror(
            "Application Error",
            f"An unexpected error occurred:\n\n{error_msg}\n\n"
            "Please check the log file for details."
        )

        # Save crash report
        crash_file = Path(f"crash_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.txt")
        with open(crash_file, 'w') as f:
            f.write(f"Compliance Manager Crash Report\n")
            f.write(f"{'=' * 50}\n\n")
            f.write(f"Time: {pd.Timestamp.now()}\n")
            f.write(f"Error: {error_msg}\n\n")
            f.write(f"Traceback:\n{detailed_error}\n")

        logger.info(f"Crash report saved to: {crash_file}")

    except:
        # Fallback to console
        print(f"\nFATAL ERROR: {error_msg}")
        traceback.print_exception(exc_type, exc_value, exc_traceback)


def run_application():
    """Run the main application"""
    try:
        # Import and run the app
        from ui.app import ComplianceApp

        logger.info("Starting Compliance Management System")

        # Create and run application
        app = ComplianceApp()
        app.run()

        logger.info("Application closed normally")

    except Exception as e:
        logger.error(f"Failed to run application: {e}")
        raise


def main():
    """Main entry point"""
    # Set up exception handler
    sys.excepthook = handle_exception

    try:
        # Check requirements
        logger.info("Checking requirements...")
        if not check_requirements():
            logger.error("Missing required packages")
            sys.exit(1)

        # Import pandas after checking requirements
        import pandas as pd

        # Check network access
        logger.info("Checking network access...")
        if not check_network_access():
            logger.error("Network access check failed")
            sys.exit(1)

        # Set up data directory
        logger.info("Setting up data directory...")
        if not check_data_directory():
            logger.error("Failed to set up data directory")
            sys.exit(1)

        # Run the application
        logger.info("Starting application...")
        run_application()

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Startup error: {e}")

        # Show error to user
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Startup Error",
                f"Failed to start Compliance Manager:\n\n{str(e)}\n\n"
                "Please check the log file for details."
            )
        except:
            print(f"STARTUP ERROR: {e}")

        sys.exit(1)


if __name__ == "__main__":
    main()