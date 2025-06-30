# services/search_service.py
"""
Advanced search functionality for Compliance Management System
Provides unified search across tasks, team members, and legislation
"""

from typing import List, Dict, Optional, Tuple, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import re

from config.settings import get_config
from core.models import Task, TeamMember, LegislationReference
from core.constants import TaskStatus, Priority, Department
from data.indexing import SearchResult, IndexManager
from data.data_manager import DataManager
from utils.logger import get_logger

logger = get_logger(__name__)


class SearchScope(Enum):
    """Search scope options"""
    ALL = "all"
    TASKS = "tasks"
    TEAM = "team"
    LEGISLATION = "legislation"
    DOCUMENTS = "documents"


class SearchOperator(Enum):
    """Search operators"""
    AND = "and"
    OR = "or"
    NOT = "not"
    EXACT = "exact"


@dataclass
class SearchFilter:
    """Search filter definition"""
    field: str
    operator: str  # =, !=, <, >, <=, >=, contains, starts_with, ends_with
    value: Any

    def matches(self, field_value: Any) -> bool:
        """Check if field value matches filter"""
        if field_value is None:
            return False

        # Convert to string for comparison
        field_str = str(field_value).lower()
        value_str = str(self.value).lower()

        if self.operator == '=':
            return field_str == value_str
        elif self.operator == '!=':
            return field_str != value_str
        elif self.operator == 'contains':
            return value_str in field_str
        elif self.operator == 'starts_with':
            return field_str.startswith(value_str)
        elif self.operator == 'ends_with':
            return field_str.endswith(value_str)
        elif self.operator in ['<', '>', '<=', '>=']:
            try:
                # Try numeric comparison
                field_num = float(field_value)
                value_num = float(self.value)

                if self.operator == '<':
                    return field_num < value_num
                elif self.operator == '>':
                    return field_num > value_num
                elif self.operator == '<=':
                    return field_num <= value_num
                elif self.operator == '>=':
                    return field_num >= value_num
            except:
                # Try date comparison
                try:
                    if isinstance(field_value, str):
                        field_date = datetime.strptime(field_value, "%Y-%m-%d")
                    else:
                        field_date = field_value

                    if isinstance(self.value, str):
                        value_date = datetime.strptime(self.value, "%Y-%m-%d")
                    else:
                        value_date = self.value

                    if self.operator == '<':
                        return field_date < value_date
                    elif self.operator == '>':
                        return field_date > value_date
                    elif self.operator == '<=':
                        return field_date <= value_date
                    elif self.operator == '>=':
                        return field_date >= value_date
                except:
                    pass

        return False


@dataclass
class SearchQuery:
    """Search query definition"""
    text: str
    scope: SearchScope = SearchScope.ALL
    filters: List[SearchFilter] = None
    operator: SearchOperator = SearchOperator.AND
    sort_by: str = 'relevance'
    sort_order: str = 'desc'
    limit: int = 50
    offset: int = 0

    def __post_init__(self):
        if self.filters is None:
            self.filters = []


class SearchService:
    """Advanced search service"""

    def __init__(self, data_manager: DataManager, index_manager: IndexManager):
        self.config = get_config()
        self.data_manager = data_manager
        self.index_manager = index_manager

        # Search configuration
        self._search_history = []
        self._synonyms = self._load_synonyms()
        self._stop_words = self._load_stop_words()

    def search(self, query: SearchQuery) -> Tuple[List[SearchResult], int]:
        """Execute search query"""
        try:
            # Preprocess query
            processed_query = self._preprocess_query(query.text)

            # Execute search based on scope
            if query.scope == SearchScope.ALL:
                results = self._search_all(query)
            elif query.scope == SearchScope.TASKS:
                results = self._search_tasks(query)
            elif query.scope == SearchScope.TEAM:
                results = self._search_team(query)
            elif query.scope == SearchScope.LEGISLATION:
                results = self._search_legislation(query)
            else:
                results = []

            # Apply filters
            if query.filters:
                results = self._apply_filters(results, query.filters)

            # Sort results
            results = self._sort_results(results, query.sort_by, query.sort_order)

            # Apply pagination
            total_count = len(results)
            paginated_results = results[query.offset:query.offset + query.limit]

            # Log search
            self._log_search(query, total_count)

            return paginated_results, total_count

        except Exception as e:
            logger.error(f"Error executing search: {e}")
            return [], 0

    def advanced_search(self, text: str,
                        status: Optional[List[str]] = None,
                        priority: Optional[List[str]] = None,
                        assigned_to: Optional[List[str]] = None,
                        date_from: Optional[str] = None,
                        date_to: Optional[str] = None,
                        compliance_area: Optional[str] = None) -> List[Task]:
        """Execute advanced task search with multiple criteria"""
        try:
            # Build filters
            filters = []

            if status:
                filters.append(SearchFilter('status', 'in', status))

            if priority:
                filters.append(SearchFilter('priority', 'in', priority))

            if assigned_to:
                filters.append(SearchFilter('allocated_to', 'contains_any', assigned_to))

            if date_from:
                filters.append(SearchFilter('created_date', '>=', date_from))

            if date_to:
                filters.append(SearchFilter('created_date', '<=', date_to))

            if compliance_area:
                filters.append(SearchFilter('compliance_area', '=', compliance_area))

            # Create query
            query = SearchQuery(
                text=text,
                scope=SearchScope.TASKS,
                filters=filters
            )

            # Execute search
            results, _ = self.search(query)

            # Convert results to tasks
            tasks = []
            for result in results:
                task = self._load_task_from_result(result)
                if task:
                    tasks.append(task)

            return tasks

        except Exception as e:
            logger.error(f"Error in advanced search: {e}")
            return []

    def suggest_search(self, partial_text: str, scope: SearchScope = SearchScope.ALL) -> List[str]:
        """Get search suggestions based on partial text"""
        try:
            suggestions = []
            partial_lower = partial_text.lower()

            # Get recent searches
            recent_searches = [s['query'] for s in self._search_history[-20:]]
            suggestions.extend([s for s in recent_searches if partial_lower in s.lower()])

            # Get field suggestions based on scope
            if scope == SearchScope.TASKS:
                # Suggest task titles
                tasks = self.data_manager.load_tasks()
                titles = [t.title for t in tasks if partial_lower in t.title.lower()]
                suggestions.extend(titles[:5])

            elif scope == SearchScope.TEAM:
                # Suggest team member names
                members = self.data_manager.load_team_members()
                names = [m.name for m in members if partial_lower in m.name.lower()]
                suggestions.extend(names[:5])

            elif scope == SearchScope.LEGISLATION:
                # Suggest legislation codes and names
                legislation = self.data_manager.load_legislation_references()
                for leg in legislation:
                    if partial_lower in leg.code.lower():
                        suggestions.append(leg.code)
                    if partial_lower in leg.full_name.lower():
                        suggestions.append(leg.full_name)

            # Remove duplicates and limit
            suggestions = list(dict.fromkeys(suggestions))[:10]

            return suggestions

        except Exception as e:
            logger.error(f"Error getting search suggestions: {e}")
            return []

    def export_search_results(self, query: SearchQuery, format: str = 'csv') -> str:
        """Export search results to file"""
        try:
            from services.export_service import ExportService

            # Get all results (no pagination for export)
            query_copy = SearchQuery(
                text=query.text,
                scope=query.scope,
                filters=query.filters,
                sort_by=query.sort_by,
                sort_order=query.sort_order,
                limit=10000,  # Large limit for export
                offset=0
            )

            results, _ = self.search(query_copy)

            # Convert results to appropriate format
            if query.scope == SearchScope.TASKS:
                # Convert to tasks
                tasks = []
                for result in results:
                    task = self._load_task_from_result(result)
                    if task:
                        tasks.append(task)

                export_service = ExportService()
                if format == 'csv':
                    return export_service.export_tasks_to_csv(tasks)
                elif format == 'excel':
                    return export_service.export_tasks_to_excel(tasks)
                elif format == 'pdf':
                    return export_service.export_tasks_to_pdf(tasks)

            # For other types, export as generic CSV
            return self._export_generic_results(results, format)

        except Exception as e:
            logger.error(f"Error exporting search results: {e}")
            raise

    def _search_all(self, query: SearchQuery) -> List[SearchResult]:
        """Search across all data types"""
        all_results = []

        # Search each type
        task_results = self._search_tasks(query)
        team_results = self._search_team(query)
        legislation_results = self._search_legislation(query)

        # Combine results
        all_results.extend(task_results)
        all_results.extend(team_results)
        all_results.extend(legislation_results)

        # Sort by relevance
        all_results.sort(key=lambda x: x.relevance_score, reverse=True)

        return all_results

    def _search_tasks(self, query: SearchQuery) -> List[SearchResult]:
        """Search tasks"""
        # Use full-text search for better results
        if ' ' in query.text:
            results = self.index_manager.search_phrase(query.text, record_types=['task'])
        else:
            results = self.index_manager.search(
                query.text,
                record_types=['task'],
                limit=query.limit * 2
            )

        # Filter to tasks only
        task_results = [r for r in results if r.record_type == 'task']

        # Enhance relevance scoring for tasks
        for result in task_results:
            self._enhance_task_relevance(result, query)

        return task_results

    def _search_team(self, query: SearchQuery) -> List[SearchResult]:
        """Search team members"""
        if ' ' in query.text:
            results = self.index_manager.search_phrase(query.text, record_types=['team'])
        else:
            results = self.index_manager.search(
                query.text,
                record_types=['team'],
                limit=query.limit * 2
            )

        # Filter to team only
        team_results = [r for r in results if r.record_type == 'team']

        return team_results

    def _search_legislation(self, query: SearchQuery) -> List[SearchResult]:
        """Search legislation references"""
        if ' ' in query.text:
            results = self.index_manager.search_phrase(query.text, record_types=['legislation'])
        else:
            results = self.index_manager.search(
                query.text,
                record_types=['legislation'],
                limit=query.limit * 2
            )

        # Filter to legislation only
        legislation_results = [r for r in results if r.record_type == 'legislation']

        return legislation_results

    def _preprocess_query(self, query_text: str) -> str:
        """Preprocess query text"""
        # Convert to lowercase
        processed = query_text.lower()

        # Remove extra whitespace
        processed = ' '.join(processed.split())

        # Expand synonyms
        words = processed.split()
        expanded_words = []

        for word in words:
            if word in self._synonyms:
                # Add original and synonyms
                expanded_words.append(f"({word} OR {' OR '.join(self._synonyms[word])})")
            else:
                expanded_words.append(word)

        # Remove stop words unless in quotes
        if '"' not in processed:
            filtered_words = [w for w in expanded_words if w not in self._stop_words]
            processed = ' '.join(filtered_words)
        else:
            processed = ' '.join(expanded_words)

        return processed

    def _apply_filters(self, results: List[SearchResult],
                       filters: List[SearchFilter]) -> List[SearchResult]:
        """Apply filters to search results"""
        filtered_results = []

        for result in results:
            match = True

            for filter in filters:
                # Get field value from result data
                field_value = result.data.get(filter.field)

                # Special handling for certain operators
                if filter.operator == 'in':
                    if field_value not in filter.value:
                        match = False
                        break
                elif filter.operator == 'contains_any':
                    if isinstance(field_value, list):
                        if not any(v in field_value for v in filter.value):
                            match = False
                            break
                    else:
                        match = False
                        break
                else:
                    # Use standard filter matching
                    if not filter.matches(field_value):
                        match = False
                        break

            if match:
                filtered_results.append(result)

        return filtered_results

    def _sort_results(self, results: List[SearchResult],
                      sort_by: str, sort_order: str) -> List[SearchResult]:
        """Sort search results"""
        reverse = (sort_order == 'desc')

        if sort_by == 'relevance':
            results.sort(key=lambda x: x.relevance_score, reverse=reverse)
        elif sort_by == 'date':
            results.sort(
                key=lambda x: x.data.get('created_date', ''),
                reverse=reverse
            )
        elif sort_by == 'title':
            results.sort(
                key=lambda x: x.title.lower(),
                reverse=reverse
            )
        elif sort_by == 'priority':
            # Custom priority order
            priority_order = {
                'Critical': 0,
                'High': 1,
                'Medium': 2,
                'Low': 3
            }
            results.sort(
                key=lambda x: priority_order.get(x.data.get('priority', 'Low'), 4),
                reverse=not reverse  # Invert for priority
            )

        return results

    def _enhance_task_relevance(self, result: SearchResult, query: SearchQuery):
        """Enhance relevance scoring for task results"""
        # Boost score based on task properties
        task_data = result.data

        # Boost for priority
        priority = task_data.get('priority', '')
        if priority == 'Critical':
            result.relevance_score *= 1.5
        elif priority == 'High':
            result.relevance_score *= 1.2

        # Boost for overdue tasks
        if task_data.get('is_overdue', False):
            result.relevance_score *= 1.3

        # Boost for exact title match
        if query.text.lower() in task_data.get('title', '').lower():
            result.relevance_score *= 2.0

        # Boost for recent tasks
        created_date = task_data.get('created_date', '')
        if created_date:
            try:
                task_date = datetime.strptime(created_date, "%Y-%m-%d %H:%M:%S")
                days_old = (datetime.now() - task_date).days
                if days_old < 7:
                    result.relevance_score *= 1.2
                elif days_old < 30:
                    result.relevance_score *= 1.1
            except:
                pass

    def _log_search(self, query: SearchQuery, result_count: int):
        """Log search for history and analytics"""
        log_entry = {
            'timestamp': datetime.now(),
            'query': query.text,
            'scope': query.scope.value,
            'filters': [
                {'field': f.field, 'operator': f.operator, 'value': str(f.value)}
                for f in query.filters
            ],
            'result_count': result_count,
            'user': None  # Would be set from session/context
        }

        self._search_history.append(log_entry)

        # Keep only recent history
        if len(self._search_history) > 1000:
            self._search_history = self._search_history[-1000:]

    def _load_synonyms(self) -> Dict[str, List[str]]:
        """Load search synonyms"""
        # Common compliance-related synonyms
        return {
            'gdpr': ['data protection', 'privacy', 'general data protection regulation'],
            'compliance': ['conformity', 'adherence', 'conformance'],
            'task': ['action', 'activity', 'assignment', 'to-do'],
            'overdue': ['late', 'delayed', 'past due', 'behind schedule'],
            'urgent': ['critical', 'high priority', 'important', 'pressing'],
            'complete': ['done', 'finished', 'resolved', 'completed'],
            'approve': ['authorise', 'authorize', 'sign off', 'endorse', 'ratify'],
            'review': ['check', 'examine', 'assess', 'evaluate', 'inspect'],
            'assign': ['allocate', 'delegate', 'designate', 'appoint'],
            'deadline': ['due date', 'target date', 'completion date']
        }

    def _load_stop_words(self) -> Set[str]:
        """Load stop words to exclude from search"""
        return {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for',
            'from', 'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on',
            'that', 'the', 'to', 'was', 'will', 'with', 'have', 'has',
            'had', 'do', 'does', 'did', 'can', 'could', 'should', 'would',
            'may', 'might', 'must', 'shall', 'will', 'would'
        }

    def _load_task_from_result(self, result: SearchResult) -> Optional[Task]:
        """Load full task data from search result"""
        if result.record_type != 'task':
            return None

        try:
            # Get task by key
            task_key = result.record_key
            return self.data_manager.get_task(task_key)
        except:
            # Try to reconstruct from result data
            try:
                return Task.from_dict(result.data)
            except:
                return None

    def _export_generic_results(self, results: List[SearchResult],
                                format: str) -> str:
        """Export generic search results"""
        import pandas as pd

        # Convert results to DataFrame
        data = []
        for result in results:
            data.append({
                'Type': result.record_type,
                'Title': result.title,
                'Summary': result.summary,
                'Relevance': f"{result.relevance_score:.2f}",
                'Key': result.record_key
            })

        df = pd.DataFrame(data)

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Search_Results_{timestamp}.{format}"
        filepath = self.config.base_path / "Exports" / filename

        # Ensure export directory exists
        filepath.parent.mkdir(exist_ok=True)

        if format == 'csv':
            df.to_csv(filepath, index=False)
        elif format == 'json':
            df.to_json(filepath, orient='records', indent=2)
        elif format == 'excel':
            df.to_excel(filepath, index=False)

        return str(filepath)

    def get_search_statistics(self) -> Dict[str, Any]:
        """Get search usage statistics"""
        try:
            if not self._search_history:
                return {
                    'total_searches': 0,
                    'popular_queries': [],
                    'search_by_scope': {},
                    'average_results': 0
                }

            # Calculate statistics
            total = len(self._search_history)

            # Popular queries
            query_counts = {}
            for entry in self._search_history:
                query = entry['query']
                query_counts[query] = query_counts.get(query, 0) + 1

            popular_queries = sorted(
                query_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]

            # Searches by scope
            scope_counts = {}
            for entry in self._search_history:
                scope = entry['scope']
                scope_counts[scope] = scope_counts.get(scope, 0) + 1

            # Average results
            result_counts = [entry['result_count'] for entry in self._search_history]
            avg_results = sum(result_counts) / len(result_counts) if result_counts else 0

            return {
                'total_searches': total,
                'popular_queries': [
                    {'query': q, 'count': c} for q, c in popular_queries
                ],
                'search_by_scope': scope_counts,
                'average_results': round(avg_results, 1),
                'recent_searches': [
                    {
                        'query': entry['query'],
                        'timestamp': entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                        'results': entry['result_count']
                    }
                    for entry in self._search_history[-10:]
                ]
            }

        except Exception as e:
            logger.error(f"Error getting search statistics: {e}")
            return {}

    def clear_search_history(self):
        """Clear search history"""
        self._search_history = []
        logger.info("Search history cleared")