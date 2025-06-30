# business/compliance_manager.py
"""
Core compliance management business logic
Orchestrates compliance operations across the system
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
import json

from config.settings import get_config
from core.models import Task, TeamMember
from core.constants import TaskStatus, Priority, Department
from core.exceptions import ValidationError, DataIntegrityError
from data.data_manager import DataManager
from data.indexing import IndexManager
from data.archiving import ArchiveManager
from business.task_manager import TaskManager
from business.team_manager import TeamManager
from business.legislation_manager import LegislationManager
from utils.logger import get_logger

logger = get_logger(__name__)


class ComplianceManager:
    """Central compliance management orchestrator"""

    def __init__(self, data_manager: DataManager):
        self.config = get_config()
        self.data_manager = data_manager
        self.index_manager = IndexManager(data_manager)
        self.archive_manager = ArchiveManager(data_manager)
        self.task_manager = TaskManager(data_manager, self.index_manager)
        self.team_manager = TeamManager(data_manager, self.index_manager)
        self.legislation_manager = LegislationManager(data_manager, self.index_manager)

        # Initialize search index if needed
        self._initialize_system()

    def _initialize_system(self):
        """Initialize system components"""
        try:
            # Check if index needs rebuilding
            stats = self.index_manager.get_index_stats()
            if stats['total_fields'] == 0:
                logger.info("Building initial search index...")
                self.index_manager.rebuild_index()
        except Exception as e:
            logger.error(f"Error initializing system: {e}")

    def refresh_data(self) -> Tuple[bool, bool]:
        """Check for and load changed data"""
        tasks_changed = self.data_manager.has_file_changed(
            self.config.excel_files['tasks']
        )
        team_changed = self.data_manager.has_file_changed(
            self.config.excel_files['team']
        )

        if tasks_changed:
            # Update task index
            self.index_manager.rebuild_index('task')

        if team_changed:
            # Update team index
            self.index_manager.rebuild_index('team')

        return tasks_changed, team_changed

    def get_dashboard_data(self, user: str) -> Dict[str, Any]:
        """Get comprehensive dashboard data for user"""
        dashboard_data = {
            'tasks': {
                'total': 0,
                'by_status': {},
                'by_priority': {},
                'overdue': 0,
                'due_soon': 0,
                'my_tasks': 0
            },
            'team': {
                'total': 0,
                'active': 0,
                'by_department': {}
            },
            'compliance': {
                'by_area': {},
                'recent_updates': [],
                'upcoming_deadlines': []
            },
            'metrics': {
                'completion_rate': 0,
                'average_resolution_time': 0,
                'tasks_this_month': 0
            }
        }

        try:
            # Get task statistics
            tasks = self.data_manager.load_tasks()
            dashboard_data['tasks']['total'] = len(tasks)

            # Get team statistics
            team_members = self.data_manager.load_team_members()
            dashboard_data['team']['total'] = len(team_members)
            dashboard_data['team']['active'] = sum(1 for m in team_members if m.active)

            # Calculate other metrics...

        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")

        return dashboard_data