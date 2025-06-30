# views/reports_view.py
"""
Reports view for Compliance Management System
Fixed import issues and proper error handling
"""

import tkinter as tk
from tkinter import ttk, filedialog
import ttkbootstrap as tb
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
import os
import tempfile

from views import BaseView
from ui.components import (
    ModernFrame, ModernButton, ModernLabel, Card,
    DatePicker, ProgressIndicator
)
# Import all dialogs properly
from ui.components.dialogs import (
    DateRangeDialog, ExportDialog, CustomReportDialog, ProgressDialog
)
from ui.styles import UIStyles


class ReportsView(BaseView):
    """Reports generation and viewing with comprehensive analytics"""

    def __init__(self, parent_frame: ttk.Frame, app: Any):
        super().__init__(parent_frame, app)
        self.recent_reports = []

    def show(self):
        """Display reports view"""
        super().show()

        # Main container
        main_container = ttk.Frame(self.parent_frame)
        main_container.pack(fill='both', expand=True, padx=20, pady=20)

        # Title
        title_label = ModernLabel(
            main_container,
            text="Reports & Analytics",
            style_type='heading1'
        )
        title_label.pack(pady=(0, 20))

        # Create scrollable content
        canvas, scrollable_frame = self.create_scrollable_frame(main_container)

        # Report types grid
        self.create_report_types_section(scrollable_frame)

        # Recent reports section
        self.create_recent_reports_section(scrollable_frame)

    def create_report_types_section(self, parent: ttk.Frame):
        """Create report types selection grid"""
        reports_frame = ttk.Frame(parent)
        reports_frame.pack(fill='both', expand=True, pady=(0, 20))

        # Configure grid
        for i in range(3):
            reports_frame.columnconfigure(i, weight=1)

        # Executive Summary
        self.create_report_card(
            reports_frame,
            title="Executive Summary",
            description="High-level overview of compliance status and key metrics",
            icon="📊",
            command=lambda: self.generate_report('executive_summary'),
            row=0, column=0
        )

        # Detailed Compliance Report
        self.create_report_card(
            reports_frame,
            title="Detailed Compliance Report",
            description="Comprehensive compliance analysis by area and status",
            icon="📋",
            command=lambda: self.generate_report('detailed_compliance'),
            row=0, column=1
        )

        # Task Status Report
        self.create_report_card(
            reports_frame,
            title="Task Status Report",
            description="Detailed breakdown of all tasks by status and priority",
            icon="📈",
            command=lambda: self.generate_report('task_status'),
            row=0, column=2
        )

        # Team Performance
        self.create_report_card(
            reports_frame,
            title="Team Performance",
            description="Individual and team productivity metrics",
            icon="👥",
            command=lambda: self.generate_report('team_performance'),
            row=1, column=0
        )

        # Overdue Analysis
        self.create_report_card(
            reports_frame,
            title="Overdue Analysis",
            description="Analysis of overdue tasks and bottlenecks",
            icon="⚠️",
            command=lambda: self.generate_report('overdue_analysis'),
            row=1, column=1
        )

        # Custom Report
        self.create_report_card(
            reports_frame,
            title="Custom Report",
            description="Create a report with custom filters and parameters",
            icon="🔧",
            command=self.create_custom_report,
            row=1, column=2
        )

    def create_report_card(self, parent: ttk.Frame, title: str, description: str,
                           icon: str, command: callable, row: int, column: int):
        """Create a single report type card"""
        card = Card(parent, title)
        card.grid(row=row, column=column, padx=10, pady=10, sticky='nsew')

        content = card.content_frame if hasattr(card, 'content_frame') else card

        # Icon
        icon_label = ttk.Label(
            content,
            text=icon,
            font=('', 32)
        )
        icon_label.pack(pady=(10, 10))

        # Description
        desc_label = ttk.Label(
            content,
            text=description,
            wraplength=200,
            justify='center'
        )
        desc_label.pack(pady=(0, 15))

        # Generate button
        generate_btn = ModernButton(
            content,
            text="Generate",
            command=command,
            style_type='primary'
        )
        generate_btn.pack()

    def create_recent_reports_section(self, parent: ttk.Frame):
        """Create recent reports section"""
        recent_card = Card(parent, "Recent Reports")
        recent_card.pack(fill='x', pady=(0, 20))

        content = recent_card.content_frame if hasattr(recent_card, 'content_frame') else recent_card

        # Get recent reports
        self.recent_reports = self.get_recent_reports()

        if self.recent_reports:
            for report in self.recent_reports[:5]:  # Show last 5 reports
                self.create_report_item(content, report)
        else:
            ttk.Label(
                content,
                text="No recent reports available",
                font=UIStyles.FONTS.get_font('normal', 'italic')
            ).pack(pady=20)

    def create_report_item(self, parent: ttk.Frame, report: Dict[str, Any]):
        """Create a single recent report item"""
        item_frame = ttk.Frame(parent)
        item_frame.pack(fill='x', pady=5, padx=10)

        # Report info
        info_frame = ttk.Frame(item_frame)
        info_frame.pack(side='left', fill='x', expand=True)

        # Title
        title_label = ttk.Label(
            info_frame,
            text=report.get('title', 'Unknown Report'),
            font=UIStyles.FONTS.get_font('normal', 'bold')
        )
        title_label.pack(anchor='w')

        # Date and user
        meta_label = ttk.Label(
            info_frame,
            text=f"{report.get('date', 'Unknown')} - Generated by {report.get('user', 'Unknown')}",
            font=UIStyles.FONTS.get_font('small'),
            foreground=UIStyles.COLOURS.get('text_secondary', '#666666')
        )
        meta_label.pack(anchor='w')

        # Actions
        action_frame = ttk.Frame(item_frame)
        action_frame.pack(side='right')

        # View button
        if 'filepath' in report and os.path.exists(report['filepath']):
            view_btn = ModernButton(
                action_frame,
                text="View",
                icon='eye',
                command=lambda: self.view_report(report['filepath']),
                style_type='secondary'
            )
            view_btn.pack(side='left', padx=(0, 5))

            download_btn = ModernButton(
                action_frame,
                text="Download",
                icon='download',
                command=lambda: self.download_report(report['filepath']),
                style_type='secondary'
            )
            download_btn.pack(side='left')

    def get_recent_reports(self) -> List[Dict[str, Any]]:
        """Get list of recent reports from the system"""
        reports = []

        # Check for reports directory
        if hasattr(self.app, 'config'):
            reports_dir = getattr(self.app.config, 'reports_directory', None)
            if reports_dir and os.path.exists(reports_dir):
                try:
                    # List recent report files
                    for filename in os.listdir(reports_dir)[:5]:
                        filepath = os.path.join(reports_dir, filename)
                        if os.path.isfile(filepath):
                            # Extract metadata from filename or file
                            reports.append({
                                'title': filename.rsplit('.', 1)[0],
                                'date': datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d'),
                                'user': 'System',
                                'filepath': filepath
                            })
                except Exception as e:
                    self.logger.error(f"Error loading recent reports: {e}")

        return reports

    def generate_report(self, report_type: str):
        """Generate a standard report"""
        try:
            # Ask for date range
            date_dialog = DateRangeDialog(
                self.parent_frame,
                title="Select Date Range",
                start_date=date.today() - timedelta(days=30),
                end_date=date.today()
            )
            self.track_dialog(date_dialog)
            self.parent_frame.wait_window(date_dialog)

            if not date_dialog.result:
                return

            date_range = date_dialog.result

            # Ask for export options
            export_dialog = ExportDialog(
                self.parent_frame,
                export_types=['PDF', 'Excel', 'CSV']
            )
            self.track_dialog(export_dialog)
            self.parent_frame.wait_window(export_dialog)

            if not export_dialog.result:
                return

            export_options = export_dialog.result

            # Generate report with progress
            self.generate_report_with_progress(
                report_type,
                date_range,
                export_options
            )

        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            self.show_error("Report Error", f"Failed to generate report: {str(e)}")

    def generate_report_with_progress(self, report_type: str,
                                      date_range: Dict[str, Any],
                                      export_options: Dict[str, Any]):
        """Generate report with progress indicator"""
        # Show progress dialog
        progress = ProgressDialog(
            self.parent_frame,
            title="Generating Report",
            message="Please wait while the report is being generated...",
            cancellable=True
        )
        self.track_dialog(progress)

        def generate():
            try:
                # Simulate report generation steps
                progress.set_progress(20, "Loading data...")

                # Get report data
                if hasattr(self.app, 'compliance_manager'):
                    report_data = self.app.compliance_manager.generate_compliance_report(
                        report_type,
                        {
                            'start_date': date_range['start_date'].strftime('%Y-%m-%d'),
                            'end_date': date_range['end_date'].strftime('%Y-%m-%d'),
                            'user': getattr(self.app, 'current_user', 'Unknown')
                        }
                    )
                else:
                    # Mock data for testing
                    report_data = {
                        'type': report_type,
                        'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'data': {}
                    }

                if progress.cancelled:
                    return

                progress.set_progress(60, "Formatting report...")

                # Create temporary file
                temp_file = self.create_temp_report_file(
                    report_type,
                    report_data,
                    export_options['format']
                )

                if progress.cancelled:
                    return

                progress.set_progress(100, "Complete!")

                # Close progress dialog
                progress.destroy()

                # Save report
                self.save_report(temp_file, report_type, export_options['format'])

            except Exception as e:
                progress.destroy()
                self.show_error("Generation Error", f"Failed to generate report: {str(e)}")

        # Run generation in background
        self.run_in_background(generate)

    def create_temp_report_file(self, report_type: str,
                                report_data: Dict[str, Any],
                                format: str) -> str:
        """Create temporary report file"""
        # Create temp file
        suffix = '.pdf' if format == 'PDF' else '.xlsx' if format == 'Excel' else '.csv'
        temp_fd, temp_path = tempfile.mkstemp(suffix=suffix)
        os.close(temp_fd)

        # In real implementation, generate actual report content
        # For now, create a placeholder file
        with open(temp_path, 'w') as f:
            f.write(f"Report Type: {report_type}\n")
            f.write(f"Generated: {report_data.get('generated_date', 'Unknown')}\n")
            f.write("Report content would go here...")

        return temp_path

    def save_report(self, temp_filepath: str, report_type: str, format: str):
        """Save report to user-selected location"""
        filename = filedialog.asksaveasfilename(
            parent=self.parent_frame,
            title="Save Report",
            defaultextension=f".{format.lower()}",
            initialfile=f"{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            filetypes=[
                (f"{format} files", f"*.{format.lower()}"),
                ("All files", "*.*")
            ]
        )

        if filename:
            try:
                import shutil
                shutil.copy2(temp_filepath, filename)

                # Clean up temp file
                try:
                    os.remove(temp_filepath)
                except:
                    pass

                # Show success with option to open
                if self.ask_yes_no(
                        "Report Generated",
                        f"Report saved to:\n{filename}\n\nOpen now?"
                ):
                    self.view_report(filename)

            except Exception as e:
                self.show_error("Save Error", f"Failed to save report: {str(e)}")

    def create_custom_report(self):
        """Create custom report with user-defined parameters"""
        try:
            # Get available fields for custom report
            available_fields = self.get_available_report_fields()

            # Show custom report dialog
            dialog = CustomReportDialog(
                self.parent_frame,
                available_fields=available_fields
            )
            self.track_dialog(dialog)
            self.parent_frame.wait_window(dialog)

            if dialog.result:
                self.generate_custom_report_from_config(dialog.result)

        except Exception as e:
            self.logger.error(f"Error creating custom report: {e}")
            self.show_error("Custom Report Error", f"Failed to create custom report: {str(e)}")

    def get_available_report_fields(self) -> Dict[str, List[str]]:
        """Get available fields for custom reports"""
        fields = {
            'Task': [
                'Key', 'Title', 'Status', 'Priority', 'Compliance Area',
                'Task Setter', 'Assigned To', 'Target Date', 'Created Date'
            ],
            'Team': [
                'Name', 'Email', 'Department', 'Role', 'Active'
            ],
            'Compliance': [
                'Area', 'Status', 'Score', 'Last Review Date'
            ]
        }

        return fields

    def generate_custom_report_from_config(self, config: Dict[str, Any]):
        """Generate custom report based on configuration"""
        # Show progress
        progress = ProgressDialog(
            self.parent_frame,
            title="Generating Custom Report",
            message="Creating your custom report...",
            cancellable=True
        )
        self.track_dialog(progress)

        def generate():
            try:
                progress.set_progress(30, "Gathering data...")

                # In real implementation, gather data based on config
                report_data = {
                    'name': config.get('name', 'Custom Report'),
                    'source': config.get('source', 'Task'),
                    'fields': config.get('fields', []),
                    'filters': config.get('filters', {}),
                    'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

                if progress.cancelled:
                    return

                progress.set_progress(70, "Formatting report...")

                # Create report file
                temp_file = self.create_temp_report_file(
                    'custom_report',
                    report_data,
                    'Excel'  # Default to Excel for custom reports
                )

                progress.set_progress(100, "Complete!")
                progress.destroy()

                # Save report
                self.save_report(temp_file, config.get('name', 'custom_report'), 'Excel')

            except Exception as e:
                progress.destroy()
                self.show_error("Generation Error", f"Failed to generate custom report: {str(e)}")

        self.run_in_background(generate)

    def view_report(self, filepath: str):
        """Open report file"""
        try:
            os.startfile(filepath)  # Windows
        except AttributeError:
            try:
                import subprocess
                subprocess.call(['open', filepath])  # macOS
            except:
                subprocess.call(['xdg-open', filepath])  # Linux
        except Exception as e:
            self.show_error("View Error", f"Failed to open report: {str(e)}")

    def download_report(self, filepath: str):
        """Download/copy report to new location"""
        new_location = filedialog.asksaveasfilename(
            parent=self.parent_frame,
            title="Save Report As",
            initialfile=os.path.basename(filepath),
            defaultextension=os.path.splitext(filepath)[1]
        )

        if new_location:
            try:
                import shutil
                shutil.copy2(filepath, new_location)
                self.show_info("Success", f"Report saved to:\n{new_location}")
            except Exception as e:
                self.show_error("Download Error", f"Failed to save report: {str(e)}")