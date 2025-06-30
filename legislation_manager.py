# business/legislation_manager.py
"""
Legislative reference management system
Provides access to legislation based on compliance areas and user roles
"""

import json
from typing import List, Dict, Optional, Tuple, Set, Any
from datetime import datetime, timedelta
from pathlib import Path

from config import get_config
from core.models import LegislationReference, Task
from core.constants import Department
from core.exceptions import ValidationError, DataIntegrityError
from data.data_manager import DataManager
from data.indexing import IndexManager
from utils.logger import get_logger

logger = get_logger(__name__)


class LegislationIndex:
    """Index for quick legislation lookups"""

    def __init__(self):
        self.by_code: Dict[str, LegislationReference] = {}
        self.by_category: Dict[str, List[LegislationReference]] = {}
        self.by_area: Dict[str, List[LegislationReference]] = {}
        self.by_jurisdiction: Dict[str, List[LegislationReference]] = {}

    def add(self, legislation: LegislationReference):
        """Add legislation to index"""
        self.by_code[legislation.code] = legislation

        # Index by category
        if legislation.category not in self.by_category:
            self.by_category[legislation.category] = []
        self.by_category[legislation.category].append(legislation)

        # Index by applicable areas
        for area in legislation.applicable_areas:
            if area not in self.by_area:
                self.by_area[area] = []
            self.by_area[area].append(legislation)

        # Index by jurisdiction
        if legislation.jurisdiction not in self.by_jurisdiction:
            self.by_jurisdiction[legislation.jurisdiction] = []
        self.by_jurisdiction[legislation.jurisdiction].append(legislation)

    def remove(self, code: str):
        """Remove legislation from index"""
        if code in self.by_code:
            legislation = self.by_code[code]
            del self.by_code[code]

            # Remove from category index
            if legislation.category in self.by_category:
                self.by_category[legislation.category] = [
                    l for l in self.by_category[legislation.category]
                    if l.code != code
                ]

            # Remove from area index
            for area in legislation.applicable_areas:
                if area in self.by_area:
                    self.by_area[area] = [
                        l for l in self.by_area[area]
                        if l.code != code
                    ]

            # Remove from jurisdiction index
            if legislation.jurisdiction in self.by_jurisdiction:
                self.by_jurisdiction[legislation.jurisdiction] = [
                    l for l in self.by_jurisdiction[legislation.jurisdiction]
                    if l.code != code
                ]


class LegislationManager:
    """Manages legislative references and compliance requirements"""

    def __init__(self, data_manager: DataManager, index_manager: IndexManager):
        self.config = get_config()
        self.data_manager = data_manager
        self.index_manager = index_manager
        self.legislation_index = LegislationIndex()

        # Load legislation references
        self._load_legislation_references()

        # Define department-legislation mappings
        self._define_department_mappings()

    def _load_legislation_references(self):
        """Load legislation from JSON file and Excel"""
        # Load from JSON configuration
        json_path = Path(__file__).parent.parent / 'config' / 'legislation_refs.json'
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._process_json_legislation(data)

        # Load from Excel if exists
        try:
            excel_legislation = self.data_manager.load_legislation_references()
            for leg in excel_legislation:
                self.legislation_index.add(leg)
                self.index_manager.index_legislation(leg)
        except Exception as e:
            logger.warning(f"Could not load legislation from Excel: {e}")

    def _process_json_legislation(self, data: Dict):
        """Process legislation from JSON file"""
        legislation_data = data.get('legislation_references', {})

        for code, details in legislation_data.items():
            # Create LegislationReference object
            legislation = LegislationReference(
                code=code,
                title=details.get('full_name', ''),  # Add this line
                full_name=details.get('full_name', ''),
                category=details.get('category', ''),
                subcategory=details.get('subcategory', ''),
                applicable_areas=details.get('applicable_to', []),
                jurisdiction='UK/EU',  # Default for now
                effective_date='',
                last_updated=datetime.now().strftime("%Y-%m-%d"),
                summary='',
                key_requirements=details.get('key_requirements', []),
                reference_links=details.get('reference_links', []),
                internal_guidance=details.get('internal_guidance', '')
            )

            # Add to index
            self.legislation_index.add(legislation)

    def _define_department_mappings(self):
        """Define which legislation is relevant to each department"""
        self.department_legislation = {
            'Legal': [
                'UK_GDPR', 'Data_Protection_Act_2018', 'Bribery_Act_2010',
                'Companies_Act_2006', 'Modern_Slavery_Act_2015'
            ],
            'Compliance': [
                'UK_GDPR', 'Data_Protection_Act_2018', 'Bribery_Act_2010',
                'CSDDD', 'Companies_Act_2006'
            ],
            'Procurement': [
                'Modern_Slavery_Act_2015', 'Bribery_Act_2010',
                'EU_Regulation_1223_2009', 'REACH_Regulation'
            ],
            'Operations': [
                'REACH_Regulation', 'Environmental_Standards',
                'Product_Safety', 'CSDDD'
            ],
            'Logistics': [
                'UK_Export_Control', 'Customs_Regulations',
                'Trade_Sanctions', 'Import_Export_Procedures'
            ],
            'IT': [
                'UK_GDPR', 'Data_Protection_Act_2018',
                'Cyber_Security_Regulations'
            ],
            'Quality': [
                'EU_Regulation_1223_2009', 'Product_Safety',
                'Quality_Standards', 'ISO_Standards'
            ],
            'Sales': [
                'Consumer_Rights_Act_2015', 'UK_GDPR',
                'Product_Liability'
            ],
            'Finance': [
                'Companies_Act_2006', 'Bribery_Act_2010',
                'Financial_Regulations'
            ]
        }

    def get_all_legislation(self) -> List[LegislationReference]:
        """Get all legislation references"""
        return list(self.legislation_index.by_code.values())

    def get_legislation_for_department(self, department: str) -> List[LegislationReference]:
        """Get relevant legislation for a department"""
        relevant_codes = self.department_legislation.get(department, [])
        legislation_list = []

        for code in relevant_codes:
            if code in self.legislation_index.by_code:
                legislation_list.append(self.legislation_index.by_code[code])

        return legislation_list

    def get_legislation_for_compliance_area(self,
                                            compliance_area: str) -> List[LegislationReference]:
        """Get legislation relevant to a compliance area"""
        return self.legislation_index.by_area.get(compliance_area, [])

    def get_legislation_for_task(self, task: Task) -> List[LegislationReference]:
        """Get legislation relevant to a specific task"""
        relevant_legislation = set()

        # Get by compliance area
        area_legislation = self.get_legislation_for_compliance_area(task.compliance_area)
        relevant_legislation.update(area_legislation)

        # Get by task setter's department
        if task.task_setter:
            members = self.data_manager.load_team_members()
            setter = next((m for m in members if m.name == task.task_setter), None)
            if setter:
                dept_legislation = self.get_legislation_for_department(setter.department)
                relevant_legislation.update(dept_legislation)

        # Filter by keywords in task
        keywords = self._extract_keywords(task)
        for keyword in keywords:
            for code, legislation in self.legislation_index.by_code.items():
                if (keyword.lower() in legislation.full_name.lower() or
                        keyword.lower() in legislation.summary.lower()):
                    relevant_legislation.add(legislation)

        return list(relevant_legislation)

    def search_legislation(self, query: str,
                           filters: Optional[Dict] = None) -> List[LegislationReference]:
        """Search legislation with optional filters"""
        results = []
        query_lower = query.lower()

        for code, legislation in self.legislation_index.by_code.items():
            # Check if query matches
            if (query_lower in code.lower() or
                    query_lower in legislation.full_name.lower() or
                    query_lower in legislation.summary.lower() or
                    any(query_lower in req.lower() for req in legislation.key_requirements)):

                # Apply filters if provided
                if filters:
                    if 'category' in filters and legislation.category != filters['category']:
                        continue
                    if 'jurisdiction' in filters and legislation.jurisdiction != filters['jurisdiction']:
                        continue
                    if 'compliance_area' in filters:
                        if filters['compliance_area'] not in legislation.applicable_areas:
                            continue

                results.append(legislation)

        return results

    def get_compliance_checklist(self, legislation_code: str) -> List[Dict[str, Any]]:
        """Get compliance checklist for specific legislation"""
        if legislation_code not in self.legislation_index.by_code:
            return []

        legislation = self.legislation_index.by_code[legislation_code]
        checklist = []

        # Load checklist from JSON if available
        json_path = Path(__file__).parent.parent / 'config' / 'legislation_refs.json'
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                leg_data = data.get('legislation_references', {}).get(legislation_code, {})
                checklist_items = leg_data.get('compliance_checklist', [])

                for i, item in enumerate(checklist_items):
                    checklist.append({
                        'id': f"{legislation_code}_{i + 1}",
                        'requirement': item,
                        'completed': False,
                        'notes': '',
                        'last_checked': None
                    })

        # Add key requirements as checklist items if no specific checklist
        if not checklist:
            for i, requirement in enumerate(legislation.key_requirements):
                checklist.append({
                    'id': f"{legislation_code}_REQ_{i + 1}",
                    'requirement': requirement,
                    'completed': False,
                    'notes': '',
                    'last_checked': None
                })

        return checklist

    def check_compliance_status(self, compliance_area: str,
                                organisation_data: Dict) -> Dict[str, Any]:
        """Check compliance status for an area"""
        relevant_legislation = self.get_legislation_for_compliance_area(compliance_area)

        compliance_status = {
            'area': compliance_area,
            'overall_status': 'compliant',
            'legislation_status': {},
            'missing_requirements': [],
            'recommendations': []
        }

        for legislation in relevant_legislation:
            status = self._check_legislation_compliance(legislation, organisation_data)
            compliance_status['legislation_status'][legislation.code] = status

            if status['status'] != 'compliant':
                compliance_status['overall_status'] = 'non_compliant'
                compliance_status['missing_requirements'].extend(status['missing'])

        # Generate recommendations
        if compliance_status['overall_status'] == 'non_compliant':
            compliance_status['recommendations'] = self._generate_recommendations(
                compliance_status['missing_requirements']
            )

        return compliance_status

    def get_legislative_updates(self, since_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent legislative updates"""
        updates = []

        # This would connect to external legislative tracking services
        # For now, return mock data
        if not since_date:
            since_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        # Check for updates in legislation
        for code, legislation in self.legislation_index.by_code.items():
            if legislation.last_updated >= since_date:
                updates.append({
                    'code': code,
                    'name': legislation.full_name,
                    'type': 'update',
                    'date': legislation.last_updated,
                    'summary': f"Updated: {legislation.full_name}",
                    'impact': 'review_required'
                })

        return updates

    def add_legislation(self, legislation_data: Dict,
                        added_by: str) -> Tuple[bool, str, Optional[LegislationReference]]:
        """Add new legislation reference"""
        try:
            # Validate data
            self._validate_legislation_data(legislation_data)

            # Check for duplicates
            if legislation_data['code'] in self.legislation_index.by_code:
                return False, "Legislation code already exists", None

            # Create legislation object
            legislation = LegislationReference(
                code=legislation_data['code'],
                title=legislation_data.get('full_name', legislation_data['code']),  # Add this line
                full_name=legislation_data['full_name'],
                category=legislation_data['category'],
                subcategory=legislation_data.get('subcategory', ''),
                applicable_areas=legislation_data.get('applicable_areas', []),
                jurisdiction=legislation_data.get('jurisdiction', 'UK'),
                effective_date=legislation_data.get('effective_date', ''),
                last_updated=datetime.now().strftime("%Y-%m-%d"),
                summary=legislation_data.get('summary', ''),
                key_requirements=legislation_data.get('key_requirements', []),
                reference_links=legislation_data.get('reference_links', []),
                internal_guidance=legislation_data.get('internal_guidance', '')
            )

            # Save to data store
            success = self.data_manager.create_legislation_reference(legislation)

            if success:
                # Add to indices
                self.legislation_index.add(legislation)
                self.index_manager.index_legislation(legislation)

                logger.info(f"Legislation added: {legislation.code} by {added_by}")
                return True, "Legislation reference added successfully", legislation
            else:
                return False, "Failed to save legislation reference", None

        except ValidationError as e:
            return False, str(e), None
        except Exception as e:
            logger.error(f"Error adding legislation: {e}")
            return False, f"Unexpected error: {str(e)}", None

    def update_legislation(self, code: str, updates: Dict,
                           updated_by: str) -> Tuple[bool, str]:
        """Update existing legislation reference"""
        try:
            if code not in self.legislation_index.by_code:
                return False, "Legislation not found"

            legislation = self.legislation_index.by_code[code]

            # Remove from indices
            self.legislation_index.remove(code)

            # Apply updates
            for field, value in updates.items():
                if hasattr(legislation, field):
                    setattr(legislation, field, value)

            # Update timestamp
            legislation.last_updated = datetime.now().strftime("%Y-%m-%d")

            # Save
            success = self.data_manager.update_legislation_reference(legislation)

            if success:
                # Re-add to indices
                self.legislation_index.add(legislation)
                self.index_manager.index_legislation(legislation)

                logger.info(f"Legislation updated: {code} by {updated_by}")
                return True, "Legislation reference updated successfully"
            else:
                return False, "Failed to save updates"

        except Exception as e:
            logger.error(f"Error updating legislation: {e}")
            return False, f"Unexpected error: {str(e)}"

    def _extract_keywords(self, task: Task) -> List[str]:
        """Extract keywords from task for legislation matching"""
        keywords = []

        # Common compliance keywords
        keyword_map = {
            'data': ['GDPR', 'data protection', 'privacy'],
            'export': ['export control', 'trade', 'customs'],
            'import': ['import', 'customs', 'trade'],
            'product': ['product safety', 'consumer', 'liability'],
            'environment': ['environmental', 'waste', 'EPR', 'packaging'],
            'bribery': ['bribery', 'corruption', 'ethics'],
            'safety': ['safety', 'hazmat', 'chemical']
        }

        # Check task content
        task_text = f"{task.title} {task.description}".lower()

        for key, related_terms in keyword_map.items():
            if key in task_text:
                keywords.extend(related_terms)

        return list(set(keywords))

    def _check_legislation_compliance(self, legislation: LegislationReference,
                                      organisation_data: Dict) -> Dict[str, Any]:
        """Check compliance with specific legislation"""
        # This would implement actual compliance checking logic
        # For now, return mock status
        return {
            'status': 'compliant',
            'missing': [],
            'last_reviewed': datetime.now().strftime("%Y-%m-%d")
        }

    def _generate_recommendations(self, missing_requirements: List[str]) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []

        for requirement in missing_requirements:
            if 'policy' in requirement.lower():
                recommendations.append("Develop or update relevant policies")
            elif 'training' in requirement.lower():
                recommendations.append("Implement staff training programme")
            elif 'documentation' in requirement.lower():
                recommendations.append("Improve documentation and record-keeping")
            elif 'process' in requirement.lower():
                recommendations.append("Review and update business processes")

        return list(set(recommendations))

    def _validate_legislation_data(self, data: Dict):
        """Validate legislation data"""
        required_fields = ['code', 'full_name', 'category']

        missing = []
        for field in required_fields:
            if field not in data or not data[field]:
                missing.append(field)

        if missing:
            raise ValidationError(
                f"Missing required fields: {', '.join(missing)}",
                validation_errors=missing
            )

        # Validate code format (alphanumeric and underscores only)
        import re
        if not re.match(r'^[A-Za-z0-9_]+$', data['code']):
            raise ValidationError(
                "Code must contain only letters, numbers, and underscores",
                field='code'
            )