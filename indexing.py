# data/indexing.py
"""
Search indexing functionality for fast text search
Creates and maintains search indices for all data
"""

import pandas as pd
from typing import List, Dict, Set, Optional, Any
from datetime import datetime
import re
from pathlib import Path
from dataclasses import dataclass
import json

from config.settings import get_config
from config.database import get_db_config
from core.models import Task, TeamMember, LegislationReference
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SearchResult:
    """Search result with relevance scoring"""
    record_type: str  # 'task', 'team', 'legislation'
    record_key: str
    title: str
    summary: str
    relevance_score: float
    matched_fields: List[str]
    data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'record_type': self.record_type,
            'record_key': self.record_key,
            'title': self.title,
            'summary': self.summary,
            'relevance_score': self.relevance_score,
            'matched_fields': self.matched_fields,
            'data': self.data
        }


class IndexManager:
    """Manages search indices for fast text search"""

    def __init__(self, data_manager):
        self.config = get_config()
        self.db_config = get_db_config()
        self.data_manager = data_manager

        # Index structure: {table: {record_key: {field: [tokens]}}}
        self._indices = {
            'task': {},
            'team': {},
            'legislation': {}
        }

        # Inverted index: {table: {token: set(record_keys)}}
        self._inverted_indices = {
            'task': {},
            'team': {},
            'legislation': {}
        }

        # Stop words
        self._stop_words = {
            'the', 'is', 'at', 'which', 'on', 'a', 'an', 'and', 'or',
            'but', 'in', 'with', 'to', 'for', 'of', 'as', 'by', 'that',
            'this', 'it', 'from', 'be', 'are', 'been', 'being', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'shall', 'can', 'need'
        }

        # Index file path
        self.index_file = self.config.base_path / 'indices' / 'search_index.json'
        self.index_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing index
        self._load_index()

    def rebuild_index(self, table: Optional[str] = None):
        """Rebuild search index for specified table or all tables"""
        try:
            if table:
                tables = [table]
            else:
                tables = ['task', 'team', 'legislation']

            for tbl in tables:
                logger.info(f"Rebuilding index for {tbl}")

                if tbl == 'task':
                    self._index_tasks()
                elif tbl == 'team':
                    self._index_team_members()
                elif tbl == 'legislation':
                    self._index_legislation()

            # Save index to file
            self._save_index()

            logger.info("Index rebuild completed")

        except Exception as e:
            logger.error(f"Error rebuilding index: {e}")

    def search(self, query: str, record_types: Optional[List[str]] = None,
               field_names: Optional[List[str]] = None, limit: int = 100) -> List[SearchResult]:
        """Search for records matching query"""
        try:
            # Tokenize query
            tokens = self._tokenize(query)

            if not tokens:
                return []

            # Determine which tables to search
            if record_types:
                tables = [t for t in record_types if t in self._inverted_indices]
            else:
                tables = list(self._inverted_indices.keys())

            results = []

            for table in tables:
                # Find matching records
                matching_records = self._find_matching_records(table, tokens)

                # Score and create results
                for record_key, score in matching_records.items():
                    result = self._create_search_result(table, record_key, tokens, score)
                    if result:
                        results.append(result)

            # Sort by relevance score
            results.sort(key=lambda x: x.relevance_score, reverse=True)

            # Apply limit
            return results[:limit]

        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []

    def index_task(self, task: Task):
        """Index a single task"""
        try:
            # Create searchable text
            searchable_text = ' '.join([
                task.key,
                task.title,
                task.description,
                task.compliance_area,
                task.subcategory,
                task.task_setter,
                task.priority,
                task.status,
                ' '.join(task.allocated_to),
                ' '.join(task.tags)
            ])

            # Tokenize and index
            tokens = self._tokenize(searchable_text)
            self._add_to_index('task', task.key, tokens)

            # Index individual fields
            self._add_field_to_index('task', task.key, 'title', self._tokenize(task.title))
            self._add_field_to_index('task', task.key, 'description', self._tokenize(task.description))
            self._add_field_to_index('task', task.key, 'compliance_area', self._tokenize(task.compliance_area))

        except Exception as e:
            logger.error(f"Error indexing task {task.key}: {e}")

    def index_team_member(self, member: TeamMember):
        """Index a single team member"""
        try:
            # Create searchable text
            searchable_text = ' '.join([
                member.name,
                member.email,
                member.department,
                member.role,
                member.location,
                member.manager,
                member.employee_id
            ])

            # Tokenize and index
            tokens = self._tokenize(searchable_text)
            self._add_to_index('team', member.email, tokens)

            # Index individual fields
            self._add_field_to_index('team', member.email, 'name', self._tokenize(member.name))
            self._add_field_to_index('team', member.email, 'department', self._tokenize(member.department))
            self._add_field_to_index('team', member.email, 'role', self._tokenize(member.role))

        except Exception as e:
            logger.error(f"Error indexing team member {member.email}: {e}")

    def index_legislation(self, legislation: LegislationReference):
        """Index a single legislation reference"""
        try:
            # Create searchable text
            searchable_text = ' '.join([
                legislation.code,
                legislation.title,
                legislation.category,
                legislation.jurisdiction,
                legislation.description,
                ' '.join(legislation.key_requirements) if hasattr(legislation, 'key_requirements') else ''
            ])

            # Tokenize and index
            tokens = self._tokenize(searchable_text)
            self._add_to_index('legislation', legislation.code, tokens)

            # Index individual fields
            self._add_field_to_index('legislation', legislation.code, 'title', self._tokenize(legislation.title))
            self._add_field_to_index('legislation', legislation.code, 'category', self._tokenize(legislation.category))
            self._add_field_to_index('legislation', legislation.code, 'description',
                                     self._tokenize(legislation.description))

        except Exception as e:
            logger.error(f"Error indexing legislation {legislation.code}: {e}")

    def remove_from_index(self, table: str, record_key: str):
        """Remove record from index"""
        try:
            # Remove from forward index
            if table in self._indices and record_key in self._indices[table]:
                tokens = set()
                for field_tokens in self._indices[table][record_key].values():
                    tokens.update(field_tokens)

                del self._indices[table][record_key]

                # Remove from inverted index
                inverted_index = self._inverted_indices.get(table, {})
                for token in tokens:
                    if token in inverted_index:
                        inverted_index[token].discard(record_key)
                        if not inverted_index[token]:
                            del inverted_index[token]

        except Exception as e:
            logger.error(f"Error removing {record_key} from {table} index: {e}")

    def get_index_stats(self) -> Dict[str, int]:
        """Get index statistics"""
        stats = {
            'total_records': 0,
            'total_tokens': 0,
            'total_fields': 0
        }

        for table, index in self._indices.items():
            stats[f'{table}_records'] = len(index)
            stats['total_records'] += len(index)

            for record_data in index.values():
                stats['total_fields'] += len(record_data)
                for tokens in record_data.values():
                    stats['total_tokens'] += len(tokens)

        for table, inverted_index in self._inverted_indices.items():
            stats[f'{table}_unique_tokens'] = len(inverted_index)

        return stats

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for indexing"""
        if not text:
            return []

        # Convert to lowercase
        text = text.lower()

        # Remove special characters
        text = re.sub(r'[^\w\s-]', ' ', text)

        # Split into tokens
        tokens = text.split()

        # Remove stop words and short tokens
        tokens = [t for t in tokens if t not in self._stop_words and len(t) > 2]

        return tokens

    def _add_to_index(self, table: str, record_key: str, tokens: List[str]):
        """Add tokens to index"""
        # Forward index
        if table not in self._indices:
            self._indices[table] = {}

        if record_key not in self._indices[table]:
            self._indices[table][record_key] = {}

        self._indices[table][record_key]['_all'] = tokens

        # Inverted index
        if table not in self._inverted_indices:
            self._inverted_indices[table] = {}

        for token in set(tokens):
            if token not in self._inverted_indices[table]:
                self._inverted_indices[table][token] = set()
            self._inverted_indices[table][token].add(record_key)

    def _add_field_to_index(self, table: str, record_key: str, field_name: str, tokens: List[str]):
        """Add field-specific tokens to index"""
        if table not in self._indices:
            self._indices[table] = {}

        if record_key not in self._indices[table]:
            self._indices[table][record_key] = {}

        self._indices[table][record_key][field_name] = tokens

    def _find_matching_records(self, table: str, tokens: List[str]) -> Dict[str, float]:
        """Find records matching tokens with scoring"""
        inverted_index = self._inverted_indices.get(table, {})
        matching_records = {}

        for token in tokens:
            if token in inverted_index:
                for record_key in inverted_index[token]:
                    if record_key not in matching_records:
                        matching_records[record_key] = 0
                    matching_records[record_key] += 1

        # Normalize scores
        if matching_records:
            max_score = max(matching_records.values())
            for key in matching_records:
                matching_records[key] = matching_records[key] / max_score

        return matching_records

    def _create_search_result(self, table: str, record_key: str,
                              query_tokens: List[str], base_score: float) -> Optional[SearchResult]:
        """Create search result object"""
        try:
            # Get record data
            if table == 'task':
                record = self.data_manager.get_task(record_key)
                if not record:
                    return None

                return SearchResult(
                    record_type='task',
                    record_key=record_key,
                    title=record.title,
                    summary=f"{record.compliance_area} - {record.status}",
                    relevance_score=base_score,
                    matched_fields=self._get_matched_fields(table, record_key, query_tokens),
                    data=record.to_dict()
                )

            elif table == 'team':
                members = self.data_manager.load_team_members()
                record = next((m for m in members if m.email == record_key), None)
                if not record:
                    return None

                return SearchResult(
                    record_type='team',
                    record_key=record_key,
                    title=record.name,
                    summary=f"{record.role} - {record.department}",
                    relevance_score=base_score,
                    matched_fields=self._get_matched_fields(table, record_key, query_tokens),
                    data=record.to_dict()
                )

            elif table == 'legislation':
                legislations = self.data_manager.load_legislation()
                record = next((l for l in legislations if l.code == record_key), None)
                if not record:
                    return None

                return SearchResult(
                    record_type='legislation',
                    record_key=record_key,
                    title=record.title,
                    summary=f"{record.category} - {record.jurisdiction}",
                    relevance_score=base_score,
                    matched_fields=self._get_matched_fields(table, record_key, query_tokens),
                    data=record.to_dict()
                )

        except Exception as e:
            logger.error(f"Error creating search result for {table}/{record_key}: {e}")
            return None

    def _get_matched_fields(self, table: str, record_key: str, query_tokens: List[str]) -> List[str]:
        """Get list of fields that matched the query"""
        matched_fields = []

        if table in self._indices and record_key in self._indices[table]:
            record_index = self._indices[table][record_key]

            for field_name, field_tokens in record_index.items():
                if field_name != '_all' and any(token in field_tokens for token in query_tokens):
                    matched_fields.append(field_name)

        return matched_fields

    def _index_tasks(self):
        """Index all tasks"""
        try:
            tasks = self.data_manager.load_tasks()

            # Clear existing task index
            self._indices['task'] = {}
            self._inverted_indices['task'] = {}

            for task in tasks:
                self.index_task(task)

            logger.info(f"Indexed {len(tasks)} tasks")

        except Exception as e:
            logger.error(f"Error indexing tasks: {e}")

    def _index_team_members(self):
        """Index all team members"""
        try:
            members = self.data_manager.load_team_members()

            # Clear existing team index
            self._indices['team'] = {}
            self._inverted_indices['team'] = {}

            for member in members:
                self.index_team_member(member)

            logger.info(f"Indexed {len(members)} team members")

        except Exception as e:
            logger.error(f"Error indexing team members: {e}")

    def _index_legislation(self):
        """Index all legislation references"""
        try:
            legislation_refs = self.data_manager.load_legislation()

            # Clear existing legislation index
            self._indices['legislation'] = {}
            self._inverted_indices['legislation'] = {}

            for leg in legislation_refs:
                self.index_legislation(leg)

            logger.info(f"Indexed {len(legislation_refs)} legislation references")

        except Exception as e:
            logger.error(f"Error indexing legislation: {e}")

    def _save_index(self):
        """Save index to file"""
        try:
            # Convert sets to lists for JSON serialization
            index_data = {
                'indices': self._indices,
                'inverted_indices': {}
            }

            for table, inverted_index in self._inverted_indices.items():
                index_data['inverted_indices'][table] = {
                    token: list(record_keys)
                    for token, record_keys in inverted_index.items()
                }

            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2)

            logger.debug("Index saved to file")

        except Exception as e:
            logger.error(f"Error saving index: {e}")

    def _load_index(self):
        """Load index from file"""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)

                self._indices = index_data.get('indices', {})

                # Convert lists back to sets for inverted indices
                self._inverted_indices = {}
                for table, inverted_index in index_data.get('inverted_indices', {}).items():
                    self._inverted_indices[table] = {
                        token: set(record_keys)
                        for token, record_keys in inverted_index.items()
                    }

                logger.debug("Index loaded from file")

        except Exception as e:
            logger.error(f"Error loading index: {e}")
            # Initialize empty indices on error
            self._indices = {'task': {}, 'team': {}, 'legislation': {}}
            self._inverted_indices = {'task': {}, 'team': {}, 'legislation': {}}