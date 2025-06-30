# data/cache.py
"""
Caching functionality for improved performance
Implements LRU cache with TTL support
"""

import time
import pickle
import json
from pathlib import Path
from typing import Any, Optional, Dict, List, Tuple
from collections import OrderedDict
from datetime import datetime, timedelta
import threading

from config import get_config
from utils.logger import get_logger

logger = get_logger(__name__)


class DataCache:
    """LRU cache with TTL support"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize cache

        Args:
            max_size: Maximum number of items in cache
            default_ttl: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache = OrderedDict()
        self._timestamps = {}
        self._hits = 0
        self._misses = 0
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            # Check if expired
            if self._is_expired(key):
                self._remove(key)
                self._misses += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]

    def put(self, key: str, value: Any, ttl: Optional[int] = None):
        """Put item in cache"""
        with self._lock:
            # Remove if already exists
            if key in self._cache:
                del self._cache[key]

            # Add to cache
            self._cache[key] = value
            self._timestamps[key] = time.time() + (ttl or self.default_ttl)

            # Evict oldest if over size limit
            while len(self._cache) > self.max_size:
                oldest_key = next(iter(self._cache))
                self._remove(oldest_key)

    def remove(self, key: str) -> bool:
        """Remove item from cache"""
        with self._lock:
            return self._remove(key)

    def clear(self):
        """Clear all items from cache"""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
            self._hits = 0
            self._misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0

            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': hit_rate,
                'total_requests': total_requests
            }

    def _is_expired(self, key: str) -> bool:
        """Check if item is expired"""
        return time.time() > self._timestamps.get(key, 0)

    def _remove(self, key: str) -> bool:
        """Remove item from cache (internal)"""
        if key in self._cache:
            del self._cache[key]
            del self._timestamps[key]
            return True
        return False

    def cleanup_expired(self):
        """Remove all expired items"""
        with self._lock:
            expired_keys = [
                key for key in self._cache
                if self._is_expired(key)
            ]
            for key in expired_keys:
                self._remove(key)

            return len(expired_keys)


class CacheManager:
    """Manages multiple caches for different data types"""

    def __init__(self):
        self.config = get_config()

        # Initialize caches
        self.caches = {
            'tasks': DataCache(max_size=2000, default_ttl=300),
            'team': DataCache(max_size=500, default_ttl=600),
            'legislation': DataCache(max_size=300, default_ttl=3600),
            'search': DataCache(max_size=1000, default_ttl=180),
            'file_status': DataCache(max_size=100, default_ttl=60)
        }

        # Persistent cache directory
        self.cache_dir = self.config.base_path / '.cache'
        self.cache_dir.mkdir(exist_ok=True)

        # Start cleanup thread
        self._start_cleanup_thread()

    def get(self, cache_name: str, key: str) -> Optional[Any]:
        """Get item from named cache"""
        if cache_name not in self.caches:
            logger.warning(f"Unknown cache: {cache_name}")
            return None

        return self.caches[cache_name].get(key)

    def put(self, cache_name: str, key: str, value: Any, ttl: Optional[int] = None):
        """Put item in named cache"""
        if cache_name not in self.caches:
            logger.warning(f"Unknown cache: {cache_name}")
            return

        self.caches[cache_name].put(key, value, ttl)

    def remove(self, cache_name: str, key: str) -> bool:
        """Remove item from named cache"""
        if cache_name not in self.caches:
            logger.warning(f"Unknown cache: {cache_name}")
            return False

        return self.caches[cache_name].remove(key)

    def clear(self, cache_name: Optional[str] = None):
        """Clear named cache or all caches"""
        if cache_name:
            if cache_name in self.caches:
                self.caches[cache_name].clear()
        else:
            for cache in self.caches.values():
                cache.clear()

    def get_multi(self, cache_name: str, keys: List[str]) -> Dict[str, Any]:
        """Get multiple items from cache"""
        if cache_name not in self.caches:
            return {}

        cache = self.caches[cache_name]
        results = {}

        for key in keys:
            value = cache.get(key)
            if value is not None:
                results[key] = value

        return results

    def put_multi(self, cache_name: str, items: Dict[str, Any], ttl: Optional[int] = None):
        """Put multiple items in cache"""
        if cache_name not in self.caches:
            return

        cache = self.caches[cache_name]

        for key, value in items.items():
            cache.put(key, value, ttl)

    def save_to_disk(self, cache_name: str, filename: Optional[str] = None):
        """Save cache to disk for persistence"""
        if cache_name not in self.caches:
            logger.warning(f"Unknown cache: {cache_name}")
            return

        if not filename:
            filename = f"{cache_name}_cache.pkl"

        cache_file = self.cache_dir / filename

        try:
            cache_data = {
                'cache': dict(self.caches[cache_name]._cache),
                'timestamps': self.caches[cache_name]._timestamps,
                'saved_at': datetime.now().isoformat()
            }

            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)

            logger.info(f"Saved {cache_name} cache to {cache_file}")

        except Exception as e:
            logger.error(f"Error saving cache to disk: {e}")

    def load_from_disk(self, cache_name: str, filename: Optional[str] = None) -> bool:
        """Load cache from disk"""
        if cache_name not in self.caches:
            logger.warning(f"Unknown cache: {cache_name}")
            return False

        if not filename:
            filename = f"{cache_name}_cache.pkl"

        cache_file = self.cache_dir / filename

        if not cache_file.exists():
            return False

        try:
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)

            # Check age
            saved_at = datetime.fromisoformat(cache_data['saved_at'])
            age = datetime.now() - saved_at

            # Don't load if too old (> 24 hours)
            if age > timedelta(hours=24):
                logger.info(f"Cache file too old ({age}), not loading")
                return False

            # Load cache data
            cache = self.caches[cache_name]
            cache._cache = OrderedDict(cache_data['cache'])
            cache._timestamps = cache_data['timestamps']

            # Clean expired items
            cache.cleanup_expired()

            logger.info(f"Loaded {cache_name} cache from {cache_file}")
            return True

        except Exception as e:
            logger.error(f"Error loading cache from disk: {e}")
            return False

    def save_persistent(self, cache_name: str, key: str, value: Any):
        """Save item to persistent cache (survives restarts)"""
        filename = f"{cache_name}_{key}.pkl"
        cache_file = self.cache_dir / filename

        try:
            data = {
                'value': value,
                'timestamp': time.time(),
                'key': key,
                'cache_name': cache_name
            }

            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)

        except Exception as e:
            logger.error(f"Error saving persistent cache: {e}")

    def load_persistent(self, cache_name: str, key: str, max_age: Optional[int] = None) -> Optional[Any]:
        """Load item from persistent cache"""
        filename = f"{cache_name}_{key}.pkl"
        cache_file = self.cache_dir / filename

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)

            # Check age
            if max_age:
                age = time.time() - data['timestamp']
                if age > max_age:
                    cache_file.unlink()  # Remove expired file
                    return None

            return data['value']

        except Exception as e:
            logger.error(f"Error loading persistent cache: {e}")
            return None

    def clear_persistent_cache(self, cache_name: Optional[str] = None):
        """Clear persistent cache files"""
        pattern = f"{cache_name}_*.pkl" if cache_name else "*.pkl"

        for cache_file in self.cache_dir.glob(pattern):
            try:
                cache_file.unlink()
            except Exception as e:
                logger.error(f"Error clearing cache file {cache_file}: {e}")

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all caches"""
        stats = {}
        for name, cache in self.caches.items():
            stats[name] = cache.get_stats()

        # Add persistent cache stats
        cache_files = list(self.cache_dir.glob("*.pkl"))
        total_size = sum(f.stat().st_size for f in cache_files)

        stats['persistent'] = {
            'files': len(cache_files),
            'size_bytes': total_size,
            'size_mb': total_size / (1024 * 1024)
        }

        return stats

    def warmup_cache(self, data_manager):
        """Pre-populate caches with common data"""
        logger.info("Warming up caches...")

        try:
            # Cache all team members
            members = data_manager.load_team_members()
            for member in members:
                self.put('team', f'member:{member.name}', member)
                self.put('team', f'email:{member.email}', member)

            # Cache recent tasks
            tasks = data_manager.load_tasks()

            # Sort by modification date if available
            recent_tasks = sorted(
                tasks,
                key=lambda t: t.modified_date or t.created_date or '',
                reverse=True
            )[:100]

            for task in recent_tasks:
                self.put('tasks', f'task:{task.key}', task)

            # Cache legislation
            legislation = data_manager.load_legislation()
            for leg in legislation:
                self.put('legislation', f'leg:{leg.code}', leg)

            logger.info(f"Cache warmup complete: {len(members)} team members, "
                        f"{len(recent_tasks)} tasks, {len(legislation)} legislation refs")

        except Exception as e:
            logger.error(f"Error during cache warmup: {e}")

    def _start_cleanup_thread(self):
        """Start background thread for cache cleanup"""

        def cleanup_worker():
            while True:
                try:
                    time.sleep(300)  # Run every 5 minutes

                    total_cleaned = 0
                    for cache_name, cache in self.caches.items():
                        cleaned = cache.cleanup_expired()
                        if cleaned > 0:
                            logger.debug(f"Cleaned {cleaned} expired items from {cache_name} cache")
                        total_cleaned += cleaned

                    if total_cleaned > 0:
                        logger.info(f"Total expired items cleaned: {total_cleaned}")

                except Exception as e:
                    logger.error(f"Error in cache cleanup thread: {e}")

        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        logger.debug("Cache cleanup thread started")