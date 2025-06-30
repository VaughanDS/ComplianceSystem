# views/legislation_view.py
"""
Legislation reference view for Compliance Management System
"""

import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from typing import Dict, Any, List, Optional

from views import BaseView
from ui.components import (
    ModernFrame, ModernButton, ModernLabel, Card,
    LegislationBrowser, SearchBar
)
from ui.styles import UIStyles


class LegislationView(BaseView):
    """Legislation reference browser view"""

    def show(self):
        """Display legislation view"""
        super().show()

        # Main container
        main_container = ttk.Frame(self.parent_frame)
        main_container.pack(fill='both', expand=True, padx=20, pady=20)

        # Title
        title_label = ModernLabel(
            main_container,
            text="Legislation Reference",
            style_type='heading1'
        )
        title_label.pack(pady=(0, 20))

        # Content area
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill='both', expand=True)

        # Left: Legislation browser
        browser_frame = ttk.Frame(content_frame)
        browser_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))

        self.legislation_browser = LegislationBrowser(
            browser_frame,
            on_select=self.on_legislation_select
        )
        self.legislation_browser.pack(fill='both', expand=True)

        # Right: Quick reference and tools
        right_frame = ttk.Frame(content_frame)
        right_frame.pack(side='right', fill='y', padx=(10, 0))

        # Quick links
        self.create_quick_links(right_frame)

        # Compliance tools
        self.create_compliance_tools(right_frame)

        # Load legislation data
        self.load_legislation()

    def create_quick_links(self, parent: ttk.Frame):
        """Create quick links section"""
        links_card = Card(parent, "Quick Links")
        links_card.pack(fill='x', pady=(0, 10))

        content = links_card.get_content_frame()

        # Common legislation links
        links = [
            {
                'text': 'UK GDPR',
                'code': 'UK-GDPR',
                'url': 'https://ico.org.uk/for-organisations/guide-to-data-protection/guide-to-the-general-data-protection-regulation-gdpr/'
            },
            {
                'text': 'EU REACH',
                'code': 'EU-REACH',
                'url': 'https://echa.europa.eu/regulations/reach/understanding-reach'
            },
            {
                'text': 'Modern Slavery Act',
                'code': 'UK-MSA-2015',
                'url': 'https://www.gov.uk/government/collections/modern-slavery-bill'
            },
            {
                'text': 'Bribery Act',
                'code': 'UK-BA-2010',
                'url': 'https://www.gov.uk/anti-bribery-policy'
            }
        ]

        for link in links:
            link_btn = ModernButton(
                content,
                text=link['text'],
                icon='external_link',
                command=lambda l=link: self.open_legislation_link(l),
                style_type='link'
            )
            link_btn.pack(fill='x', pady=2)

    def create_compliance_tools(self, parent: ttk.Frame):
        """Create compliance tools section"""
        tools_card = Card(parent, "Compliance Tools")
        tools_card.pack(fill='x')

        content = tools_card.get_content_frame()

        # Check compliance button
        check_btn = ModernButton(
            content,
            text="Check Task Compliance",
            icon='check_circle',
            command=self.check_task_compliance,
            style_type='primary'
        )
        check_btn.pack(fill='x', pady=(0, 5))

        # Generate checklist
        checklist_btn = ModernButton(
            content,
            text="Generate Checklist",
            icon='list',
            command=self.generate_checklist,
            style_type='secondary'
        )
        checklist_btn.pack(fill='x', pady=(0, 5))

        # Export references
        export_btn = ModernButton(
            content,
            text="Export References",
            icon='download',
            command=self.export_references,
            style_type='secondary'
        )
        export_btn.pack(fill='x')

    def load_legislation(self):
        """Load legislation data"""
        try:
            # Load from legislation manager
            legislation_list = self.app.compliance_manager.legislation_manager.get_all_legislation()

            # Load into browser
            self.legislation_browser.load_legislation(legislation_list)

        except Exception as e:
            self.show_error("Load Error", f"Failed to load legislation: {str(e)}")

    def on_legislation_select(self, legislation: Any):
        """Handle legislation selection"""
        # Could show more detailed view or related tasks
        pass

    def open_legislation_link(self, link: Dict[str, str]):
        """Open external legislation link"""
        import webbrowser

        if self.ask_yes_no("Open External Link",
                           f"Open {link['text']} in your web browser?"):
            webbrowser.open(link['url'])

    def check_task_compliance(self):
        """Check compliance for current tasks"""
        # Get user's tasks
        tasks = self.app.compliance_manager.task_manager.get_tasks_for_user(
            self.app.current_user
        )

        open_tasks = [t for t in tasks if t.status in ['Open', 'In Progress']]

        if not open_tasks:
            self.show_info("No Tasks", "You have no open tasks to check")
            return

        # Create task selection dialog
        from ui.components.dialogs import BaseDialog

        class TaskSelectionDialog(BaseDialog):
            def __init__(self, parent, tasks):
                self.tasks = tasks
                self.selected_task = None
                super().__init__(parent, "Select Task", 400, 300)

            def create_content(self):
                ttk.Label(
                    self.main_frame,
                    text="Select a task to check compliance:",
                    font=UIStyles.FONTS.get_font('normal')
                ).pack(pady=(0, 10))

                # Task listbox
                self.task_listbox = tk.Listbox(self.main_frame, height=10)
                self.task_listbox.pack(fill='both', expand=True)

                for task in self.tasks:
                    display_text = f"{task.key} - {task.title}"
                    self.task_listbox.insert(tk.END, display_text)

                # Select first item
                if self.tasks:
                    self.task_listbox.selection_set(0)

            def get_result(self):
                selection = self.task_listbox.curselection()
                if selection:
                    return self.tasks[selection[0]]
                return None

        dialog = TaskSelectionDialog(self.parent_frame, open_tasks)
        self.parent_frame.wait_window(dialog)

        if dialog.result:
            self.show_task_compliance(dialog.result)

    def show_task_compliance(self, task: Any):
        """Show compliance requirements for a task"""
        # Get relevant legislation
        relevant = self.app.compliance_manager.legislation_manager.get_legislation_for_task(task)

        if not relevant:
            self.show_info("No Requirements",
                           "No specific legislation requirements found for this task")
            return

        # Create compliance dialog
        from ui.components.dialogs import BaseDialog

        class ComplianceDialog(BaseDialog):
            def __init__(self, parent, task, legislation_list):
                self.task = task
                self.legislation_list = legislation_list
                super().__init__(parent, "Compliance Requirements", 600, 500)

            def create_content(self):
                # Task info
                task_frame = ttk.LabelFrame(self.main_frame, text="Task", padding=10)
                task_frame.pack(fill='x', pady=(0, 10))

                ttk.Label(
                    task_frame,
                    text=f"{self.task.key} - {self.task.title}",
                    font=UIStyles.FONTS.get_font('normal', 'bold')
                ).pack(anchor='w')

                ttk.Label(
                    task_frame,
                    text=f"Compliance Area: {self.task.compliance_area}",
                    font=UIStyles.FONTS.get_font('small')
                ).pack(anchor='w')

                # Relevant legislation
                leg_frame = ttk.LabelFrame(self.main_frame, text="Relevant Legislation", padding=10)
                leg_frame.pack(fill='both', expand=True)

                # Create scrollable text
                text_frame = ttk.Frame(leg_frame)
                text_frame.pack(fill='both', expand=True)

                scrollbar = ttk.Scrollbar(text_frame)
                scrollbar.pack(side='right', fill='y')

                self.text_widget = tk.Text(
                    text_frame,
                    wrap='word',
                    yscrollcommand=scrollbar.set,
                    font=UIStyles.FONTS.get_font('normal')
                )
                self.text_widget.pack(side='left', fill='both', expand=True)
                scrollbar.configure(command=self.text_widget.yview)

                # Add legislation requirements
                for legislation in self.legislation_list:
                    self.text_widget.insert('end', f"{legislation.code} - {legislation.full_name}\n", 'title')
                    self.text_widget.insert('end', f"\nSummary: {legislation.summary}\n\n", 'normal')

                    if legislation.key_requirements:
                        self.text_widget.insert('end', "Key Requirements:\n", 'heading')
                        for req in legislation.key_requirements:
                            self.text_widget.insert('end', f"  • {req}\n", 'normal')

                    self.text_widget.insert('end', "\n" + "=" * 60 + "\n\n", 'separator')

                # Configure tags
                self.text_widget.tag_configure('title', font=UIStyles.FONTS.get_font('normal', 'bold'))
                self.text_widget.tag_configure('heading', font=UIStyles.FONTS.get_font('normal', 'bold'))
                self.text_widget.tag_configure('normal', font=UIStyles.FONTS.get_font('small'))
                self.text_widget.tag_configure('separator', foreground=UIStyles.COLOURS['text_secondary'])

                self.text_widget.configure(state='disabled')

            def create_buttons(self):
                button_frame = ttk.Frame(self.main_frame)
                button_frame.pack(side='bottom', fill='x', pady=(20, 0))

                # Export button
                export_btn = ModernButton(
                    button_frame,
                    text="Export Requirements",
                    icon='download',
                    command=self.export_requirements,
                    style_type='primary'
                )
                export_btn.pack(side='left')

                # Close button
                close_btn = ModernButton(
                    button_frame,
                    text="Close",
                    command=self.cancel,
                    style_type='secondary'
                )
                close_btn.pack(side='right')

            def export_requirements(self):
                from tkinter import filedialog

                filename = filedialog.asksaveasfilename(
                    defaultextension=".txt",
                    filetypes=[
                        ("Text files", "*.txt"),
                        ("PDF files", "*.pdf"),
                        ("All files", "*.*")
                    ]
                )

                if filename:
                    try:
                        content = self.text_widget.get('1.0', 'end-1c')
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(f"Compliance Requirements for Task: {self.task.key}\n")
                            f.write("=" * 60 + "\n\n")
                            f.write(content)

                        messagebox.showinfo("Success", f"Requirements exported to:\n{filename}")
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to export: {str(e)}")

        dialog = ComplianceDialog(self.parent_frame, task, relevant)

    def generate_checklist(self):
        """Generate compliance checklist"""
        # Ask for legislation selection
        legislation_list = self.app.compliance_manager.legislation_manager.get_all_legislation()

        if not legislation_list:
            self.show_warning("No Legislation", "No legislation data available")
            return

        # Create selection dialog
        from ui.components.dialogs import BaseDialog

        class ChecklistDialog(BaseDialog):
            def __init__(self, parent, legislation_list):
                self.legislation_list = legislation_list
                self.selected_items = []
                super().__init__(parent, "Generate Compliance Checklist", 500, 400)

            def create_content(self):
                ttk.Label(
                    self.main_frame,
                    text="Select legislation to include in checklist:",
                    font=UIStyles.FONTS.get_font('normal')
                ).pack(pady=(0, 10))

                # Legislation checkboxes
                canvas = tk.Canvas(self.main_frame)
                scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=canvas.yview)
                scrollable_frame = ttk.Frame(canvas)

                scrollable_frame.bind(
                    "<Configure>",
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
                )

                canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
                canvas.configure(yscrollcommand=scrollbar.set)

                self.check_vars = {}
                for legislation in self.legislation_list:
                    var = tk.BooleanVar(value=False)
                    self.check_vars[legislation.code] = var

                    cb = ttk.Checkbutton(
                        scrollable_frame,
                        text=f"{legislation.code} - {legislation.full_name}",
                        variable=var
                    )
                    cb.pack(anchor='w', pady=2)

                canvas.pack(side="left", fill="both", expand=True)
                scrollbar.pack(side="right", fill="y")

            def get_result(self):
                selected = []
                for code, var in self.check_vars.items():
                    if var.get():
                        leg = next((l for l in self.legislation_list if l.code == code), None)
                        if leg:
                            selected.append(leg)
                return selected

        dialog = ChecklistDialog(self.parent_frame, legislation_list)
        self.parent_frame.wait_window(dialog)

        if dialog.result:
            self.export_checklist(dialog.result)

    def export_checklist(self, legislation_list: List[Any]):
        """Export compliance checklist"""
        from tkinter import filedialog

        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[
                ("Excel files", "*.xlsx"),
                ("PDF files", "*.pdf"),
                ("All files", "*.*")
            ]
        )

        if filename:
            try:
                import pandas as pd

                # Create checklist data
                checklist_data = []

                for legislation in legislation_list:
                    # Get checklist items
                    checklist = self.app.compliance_manager.legislation_manager.get_compliance_checklist(
                        legislation.code
                    )

                    for item in checklist:
                        checklist_data.append({
                            'Legislation': f"{legislation.code} - {legislation.full_name}",
                            'Requirement': item['requirement'],
                            'Category': item.get('category', ''),
                            'Completed': '',
                            'Date': '',
                            'Notes': ''
                        })

                # Create dataframe
                df = pd.DataFrame(checklist_data)

                if filename.endswith('.xlsx'):
                    # Excel with formatting
                    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='Compliance Checklist')

                        # Get worksheet
                        worksheet = writer.sheets['Compliance Checklist']

                        # Set column widths
                        worksheet.column_dimensions['A'].width = 40
                        worksheet.column_dimensions['B'].width = 60
                        worksheet.column_dimensions['C'].width = 20
                        worksheet.column_dimensions['D'].width = 15
                        worksheet.column_dimensions['E'].width = 15
                        worksheet.column_dimensions['F'].width = 40

                else:
                    # PDF would require additional library
                    self.show_error("Export Error", "PDF export not yet implemented")
                    return

                self.show_info("Success", f"Checklist exported to:\n{filename}")

            except Exception as e:
                self.show_error("Export Error", f"Failed to export checklist: {str(e)}")

    def export_references(self):
        """Export all legislation references"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[
                ("Excel files", "*.xlsx"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )

        if filename:
            try:
                # Get all legislation
                legislation_list = self.app.compliance_manager.legislation_manager.get_all_legislation()

                # Convert to dataframe
                import pandas as pd

                data = []
                for leg in legislation_list:
                    data.append({
                        'Code': leg.code,
                        'Full Name': leg.full_name,
                        'Category': leg.category,
                        'Jurisdiction': leg.jurisdiction,
                        'Effective Date': leg.effective_date,
                        'Summary': leg.summary,
                        'Applicable Areas': ', '.join(leg.applicable_areas),
                        'Key Requirements': '\n'.join(leg.key_requirements) if leg.key_requirements else ''
                    })

                df = pd.DataFrame(data)

                if filename.endswith('.csv'):
                    df.to_csv(filename, index=False)
                else:
                    df.to_excel(filename, index=False)

                self.show_info("Success", f"References exported to:\n{filename}")

            except Exception as e:
                self.show_error("Export Error", f"Failed to export: {str(e)}")