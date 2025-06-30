# views/team_view.py
"""
Team management view for Compliance Management System
"""

import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from datetime import datetime
from typing import Dict, Any, List, Optional

from views import BaseView
from ui.components import (
    ModernFrame, ModernButton, ModernLabel, Card,
    TeamTable, SearchBar, FilterPanel
)
from ui.components.dialogs import TeamMemberDialog, ConfirmDialog
from ui.styles import UIStyles


class TeamView(BaseView):
    """Team management view"""

    def __init__(self, parent_frame: ttk.Frame, app: Any):
        super().__init__(parent_frame, app)
        self.selected_member = None

    def show(self):
        """Display team management view"""
        super().show()

        # Check permissions
        can_manage = 'manage_team' in self.app.user_permissions

        # Main container
        main_container = ttk.Frame(self.parent_frame)
        main_container.pack(fill='both', expand=True, padx=20, pady=20)

        # Title and actions
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill='x', pady=(0, 20))

        title_label = ModernLabel(
            header_frame,
            text="Team Management",
            style_type='heading1'
        )
        title_label.pack(side='left')

        # Action buttons
        if can_manage:
            action_frame = ttk.Frame(header_frame)
            action_frame.pack(side='right')

            add_btn = ModernButton(
                action_frame,
                text="Add Member",
                icon='plus',
                command=self.add_member,
                style_type='primary'
            )
            add_btn.pack(side='left', padx=(0, 5))

            import_btn = ModernButton(
                action_frame,
                text="Import",
                icon='upload',
                command=self.import_members,
                style_type='secondary'
            )
            import_btn.pack(side='left', padx=(0, 5))

            export_btn = ModernButton(
                action_frame,
                text="Export",
                icon='download',
                command=self.export_members,
                style_type='secondary'
            )
            export_btn.pack(side='left')

        # Search bar
        search_frame = ttk.Frame(main_container)
        search_frame.pack(fill='x', pady=(0, 10))

        self.search_bar = SearchBar(
            search_frame,
            callback=self.on_search,
            placeholder="Search team members..."
        )
        self.search_bar.pack(fill='x')

        # Content area
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill='both', expand=True)

        # Left: Team statistics
        stats_frame = ttk.Frame(content_frame)
        stats_frame.pack(side='left', fill='y', padx=(0, 10))

        self.create_team_stats(stats_frame)

        # Right: Team table
        table_frame = ttk.Frame(content_frame)
        table_frame.pack(side='left', fill='both', expand=True)

        # Team table
        table_card = Card(table_frame, "Team Members")
        table_card.pack(fill='both', expand=True)

        self.team_table = TeamTable(
            table_card.get_content_frame(),
            on_select=self.on_member_select,
            on_double_click=self.on_member_double_click if can_manage else None
        )
        self.team_table.pack(fill='both', expand=True)

        # Load team members
        self.load_members()

        # Member details panel (if selected)
        if can_manage:
            self.create_details_panel(table_frame)

    def create_team_stats(self, parent: ttk.Frame):
        """Create team statistics panel"""
        stats_card = Card(parent, "Team Statistics")
        stats_card.pack(fill='x')

        content = stats_card.get_content_frame()

        # Get statistics
        stats = self.app.compliance_manager.team_manager.get_department_statistics()

        # Total members
        self.create_stat_item(content, "Total Members", str(stats['total_members']))

        # Active members
        self.create_stat_item(content, "Active Members", str(stats['active_members']))

        # Managers
        self.create_stat_item(content, "Managers", str(stats['managers_count']))

        # By department
        dept_frame = ttk.LabelFrame(content, text="By Department", padding=10)
        dept_frame.pack(fill='x', pady=(10, 0))

        for dept, data in stats['by_department'].items():
            dept_text = f"{dept}: {data['count']}"
            if data['managers'] > 0:
                dept_text += f" ({data['managers']} managers)"

            ttk.Label(
                dept_frame,
                text=dept_text,
                font=UIStyles.FONTS.get_font('small')
            ).pack(anchor='w', pady=2)

    def create_stat_item(self, parent: ttk.Frame, label: str, value: str):
        """Create statistic item"""
        stat_frame = ttk.Frame(parent)
        stat_frame.pack(fill='x', pady=5)

        ttk.Label(
            stat_frame,
            text=f"{label}:",
            font=UIStyles.FONTS.get_font('normal')
        ).pack(side='left')

        ttk.Label(
            stat_frame,
            text=value,
            font=UIStyles.FONTS.get_font('normal', 'bold')
        ).pack(side='right')

    def create_details_panel(self, parent: ttk.Frame):
        """Create member details panel"""
        self.details_card = Card(parent, "Member Details")
        # Initially hidden

        self.details_content = self.details_card.get_content_frame()

    def load_members(self):
        """Load team members"""
        try:
            members = self.app.compliance_manager.team_manager.get_active_team_members()
            self.team_table.load_members(members)
        except Exception as e:
            self.show_error("Load Error", f"Failed to load team members: {str(e)}")

    def on_search(self, query: str):
        """Handle search"""
        # Filter members
        all_members = self.app.compliance_manager.data_manager.load_team_members()

        if query:
            query_lower = query.lower()
            filtered = [m for m in all_members if
                        query_lower in m.name.lower() or
                        query_lower in m.email.lower() or
                        query_lower in m.department.lower() or
                        query_lower in m.role.lower()]
        else:
            filtered = all_members

        self.team_table.load_members(filtered)

    def on_member_select(self, member: Any):
        """Handle member selection"""
        self.selected_member = member

        # Show details if panel exists
        if hasattr(self, 'details_card'):
            self.show_member_details(member)

    def on_member_double_click(self, member: Any):
        """Handle member double-click"""
        self.edit_member(member)

    def show_member_details(self, member: Any):
        """Show member details in panel"""
        # Clear existing
        for widget in self.details_content.winfo_children():
            widget.destroy()

        # Show card
        self.details_card.pack(fill='x', pady=(10, 0))

        # Member info
        info_frame = ttk.Frame(self.details_content)
        info_frame.pack(fill='x', pady=(0, 10))

        self.create_detail_item(info_frame, "Name", member.name)
        self.create_detail_item(info_frame, "Email", member.email)
        self.create_detail_item(info_frame, "Department", member.department)
        self.create_detail_item(info_frame, "Role", member.role)
        self.create_detail_item(info_frame, "Reports To", member.manager or "None")
        self.create_detail_item(info_frame, "Status", "Active" if member.active else "Inactive")

        # Permissions
        if member.permissions:
            perm_frame = ttk.LabelFrame(self.details_content, text="Permissions", padding=5)
            perm_frame.pack(fill='x', pady=(0, 10))

            perm_text = "\n".join(f"• {p.replace('_', ' ').title()}" for p in member.permissions)
            ttk.Label(
                perm_frame,
                text=perm_text,
                font=UIStyles.FONTS.get_font('small')
            ).pack(anchor='w')

        # Task workload
        workload_frame = ttk.LabelFrame(self.details_content, text="Task Workload", padding=5)
        workload_frame.pack(fill='x', pady=(0, 10))

        # Get member's tasks
        tasks = self.app.compliance_manager.task_manager.get_tasks_for_user(member.name)

        open_tasks = sum(1 for t in tasks if t.status == 'Open')
        in_progress = sum(1 for t in tasks if t.status == 'In Progress')
        pending = sum(1 for t in tasks if t.status == 'Pending Approval')

        ttk.Label(
            workload_frame,
            text=f"Open: {open_tasks}\nIn Progress: {in_progress}\nPending Approval: {pending}",
            font=UIStyles.FONTS.get_font('small')
        ).pack(anchor='w')

        # Action buttons
        btn_frame = ttk.Frame(self.details_content)
        btn_frame.pack(fill='x')

        edit_btn = ModernButton(
            btn_frame,
            text="Edit",
            icon='edit',
            command=lambda: self.edit_member(member),
            style_type='primary'
        )
        edit_btn.pack(side='left', padx=(0, 5))

        if member.active:
            deactivate_btn = ModernButton(
                btn_frame,
                text="Deactivate",
                icon='block',
                command=lambda: self.deactivate_member(member),
                style_type='warning'
            )
            deactivate_btn.pack(side='left')
        else:
            activate_btn = ModernButton(
                btn_frame,
                text="Activate",
                icon='check',
                command=lambda: self.activate_member(member),
                style_type='success'
            )
            activate_btn.pack(side='left')

    def create_detail_item(self, parent: ttk.Frame, label: str, value: str):
        """Create detail item"""
        item_frame = ttk.Frame(parent)
        item_frame.pack(fill='x', pady=2)

        ttk.Label(
            item_frame,
            text=f"{label}:",
            font=UIStyles.FONTS.get_font('small'),
            foreground=UIStyles.COLOURS['text_secondary']
        ).pack(side='left')

        ttk.Label(
            item_frame,
            text=value,
            font=UIStyles.FONTS.get_font('small', 'bold')
        ).pack(side='left', padx=(5, 0))

    def add_member(self):
        """Add new team member"""
        departments = [d.value for d in self.app.config.departments]

        dialog = TeamMemberDialog(
            self.parent_frame,
            departments=departments
        )

        self.parent_frame.wait_window(dialog)

        if dialog.result:
            member_data = dialog.result

            success, message, member = self.app.compliance_manager.team_manager.create_team_member(
                member_data,
                self.app.current_user
            )

            if success:
                self.show_info("Success", "Team member added successfully")
                self.refresh()
            else:
                self.show_error("Error", message)

    def edit_member(self, member: Any):
        """Edit team member"""
        departments = [d.value for d in self.app.config.departments]

        # Convert member to dict
        member_data = {
            'name': member.name,
            'email': member.email,
            'department': member.department,
            'role': member.role,
            'manager': member.manager,
            'active': member.active,
            'permissions': member.permissions
        }

        dialog = TeamMemberDialog(
            self.parent_frame,
            member_data=member_data,
            departments=departments
        )

        self.parent_frame.wait_window(dialog)

        if dialog.result:
            updates = dialog.result

            success, message = self.app.compliance_manager.team_manager.update_team_member(
                member.email,
                updates,
                self.app.current_user
            )

            if success:
                self.show_info("Success", "Team member updated successfully")
                self.refresh()

                # Update details panel if visible
                if hasattr(self, 'details_card'):
                    # Reload member
                    updated_member = self.app.compliance_manager.team_manager.get_member_by_email(
                        member.email
                    )
                    if updated_member:
                        self.show_member_details(updated_member)
            else:
                self.show_error("Error", message)

    def deactivate_member(self, member: Any):
        """Deactivate team member"""
        # Check for task dependencies
        tasks = self.app.compliance_manager.task_manager.get_tasks_for_user(member.name)
        active_tasks = [t for t in tasks if t.status not in ['Resolved', 'Closed']]

        warning_msg = f"Are you sure you want to deactivate {member.name}?"
        if active_tasks:
            warning_msg += f"\n\nThis member has {len(active_tasks)} active tasks."
            warning_msg += "\nConsider reassigning these tasks first."

        if self.ask_yes_no("Deactivate Member", warning_msg):
            success, message = self.app.compliance_manager.team_manager.deactivate_team_member(
                member.email,
                self.app.current_user
            )

            if success:
                self.show_info("Success", "Team member deactivated")
                self.refresh()
            else:
                self.show_error("Error", message)

    def activate_member(self, member: Any):
        """Activate team member"""
        if self.ask_yes_no("Activate Member", f"Activate {member.name}?"):
            success, message = self.app.compliance_manager.team_manager.activate_team_member(
                member.email,
                self.app.current_user
            )

            if success:
                self.show_info("Success", "Team member activated")
                self.refresh()
            else:
                self.show_error("Error", message)

    def import_members(self):
        """Import team members from file"""
        from tkinter import filedialog
        import pandas as pd

        filename = filedialog.askopenfilename(
            title="Select file to import",
            filetypes=[
                ("Excel files", "*.xlsx;*.xls"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )

        if filename:
            try:
                # Read file
                if filename.endswith('.csv'):
                    df = pd.read_csv(filename)
                else:
                    df = pd.read_excel(filename)

                # Validate columns
                required_columns = ['Name', 'Email', 'Department', 'Role']
                missing = [col for col in required_columns if col not in df.columns]

                if missing:
                    self.show_error("Import Error",
                                    f"Missing required columns: {', '.join(missing)}")
                    return

                # Process members
                members_data = []
                for _, row in df.iterrows():
                    member_data = {
                        'name': row['Name'],
                        'email': row['Email'],
                        'department': row['Department'],
                        'role': row['Role'],
                        'manager': row.get('Manager', ''),
                        'active': row.get('Active', True),
                        'permissions': []  # Default permissions
                    }

                    # Add default permissions based on role
                    if 'manager' in member_data['role'].lower():
                        member_data['permissions'] = [
                            'create_tasks', 'update_tasks', 'view_reports',
                            'approve_tasks'
                        ]
                    else:
                        member_data['permissions'] = [
                            'create_tasks', 'update_tasks', 'view_reports'
                        ]

                    members_data.append(member_data)

                # Import members
                successful, errors = self.app.compliance_manager.team_manager.bulk_import_members(
                    members_data,
                    self.app.current_user
                )

                # Show results
                message = f"Imported {successful} members successfully."
                if errors:
                    message += f"\n\nErrors:\n" + "\n".join(errors[:5])
                    if len(errors) > 5:
                        message += f"\n... and {len(errors) - 5} more"

                self.show_info("Import Complete", message)
                self.refresh()

            except Exception as e:
                self.show_error("Import Error", f"Failed to import: {str(e)}")

    def export_members(self):
        """Export team members"""
        from tkinter import filedialog

        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[
                ("Excel files", "*.xlsx"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )

        if filename:
            success, filepath = self.app.compliance_manager.team_manager.export_team_data(
                'csv' if filename.endswith('.csv') else 'excel'
            )

            if success:
                # Copy to user's chosen location
                import shutil
                shutil.copy2(filepath, filename)
                self.show_info("Export Complete", f"Team data exported to:\n{filename}")
            else:
                self.show_error("Export Error", filepath)