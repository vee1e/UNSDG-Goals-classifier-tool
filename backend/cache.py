"""
In-memory cache with TTL for SDG classification results.
Prevents redundant API calls for identical requests within a session.
"""

import hashlib
import json
import time
from typing import Any, Dict, Optional, Tuple
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class CacheEntry:
    """A single cache entry with data, timestamp, and metadata."""
    data: Any
    timestamp: float
    ttl: int  # seconds
    hits: int = 0


class InMemoryCache:
    """
    Thread-safe in-memory cache with TTL support.
    
    Features:
    - Automatic expiration of old entries
    - Cache hit/miss statistics
    - Per-endpoint cache isolation
    - Thread-safe operations
    """
    
    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache with default TTL.
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 5 minutes)
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl
        self._lock = Lock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'total_requests': 0,
            'evictions': 0
        }
    
    def _generate_key(self, endpoint: str, data: Dict) -> str:
        """
        Generate a unique cache key from endpoint and request data.
        
        Key includes:
        - Endpoint path (model type)
        - projectUrl (normalized to lowercase, stripped)
        - projectDescription (stripped whitespace)
        """
        # Normalize data for consistent hashing
        normalized = {
            'endpoint': endpoint,
            'projectUrl': str(data.get('projectUrl', '')).lower().strip().rstrip('/'),
            'projectDescription': str(data.get('projectDescription', '')).strip()
        }
        
        # Create deterministic JSON string
        key_data = json.dumps(normalized, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def get(self, endpoint: str, data: Dict) -> Tuple[Optional[Any], bool]:
        """
        Retrieve item from cache if it exists and is not expired.
        
        Args:
            endpoint: API endpoint path
            data: Request data dictionary
            
        Returns:
            Tuple of (cached_data or None, was_cache_hit)
        """
        with self._lock:
            self._stats['total_requests'] += 1
            
            key = self._generate_key(endpoint, data)
            entry = self._cache.get(key)
            
            if entry is None:
                self._stats['misses'] += 1
                return None, False
            
            # Check if expired
            current_time = time.time()
            if current_time - entry.timestamp > entry.ttl:
                # Expired - remove and return miss
                del self._cache[key]
                self._stats['evictions'] += 1
                self._stats['misses'] += 1
                return None, False
            
            # Cache hit
            entry.hits += 1
            self._stats['hits'] += 1
            
            # Add cache metadata to response
            result_with_meta = {
                **entry.data,
                '_cache_meta': {
                    'cached': True,
                    'cached_at': entry.timestamp,
                    'ttl': entry.ttl,
                    'age_seconds': int(current_time - entry.timestamp),
                    'cache_hits': entry.hits
                }
            }
            
            return result_with_meta, True
    
    def set(self, endpoint: str, data: Dict, result: Any, ttl: Optional[int] = None) -> None:
        """
        Store result in cache.
        
        Args:
            endpoint: API endpoint path
            data: Request data dictionary
            result: Data to cache
            ttl: Optional custom TTL (uses default if not specified)
        """
        with self._lock:
            key = self._generate_key(endpoint, data)
            
            # Don't cache error responses
            if isinstance(result, dict) and 'error' in result:
                return
            
            # Remove any existing cache meta before storing
            clean_result = {k: v for k, v in result.items() if not k.startswith('_')}
            
            self._cache[key] = CacheEntry(
                data=clean_result,
                timestamp=time.time(),
                ttl=ttl or self._default_ttl,
                hits=0
            )
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        with self._lock:
            total = self._stats['total_requests']
            hits = self._stats['hits']
            
            # Clean up expired entries for accurate count
            current_time = time.time()
            active_entries = sum(
                1 for entry in self._cache.values()
                if current_time - entry.timestamp <= entry.ttl
            )
            
            return {
                'hits': hits,
                'misses': self._stats['misses'],
                'total_requests': total,
                'hit_rate': round(hits / total * 100, 2) if total > 0 else 0,
                'evictions': self._stats['evictions'],
                'active_entries': active_entries,
                'default_ttl_seconds': self._default_ttl
            }
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._stats = {
                'hits': 0,
                'misses': 0,
                'total_requests': 0,
                'evictions': 0
            }
    
    def get_cache_key(self, endpoint: str, data: Dict) -> str:
        """Get the cache key that would be used for a request (for debugging)."""
        return self._generate_key(endpoint, data)


# Global cache instance
classification_cache = InMemoryCache(default_ttl=300)


def cached_classify(endpoint: str, ttl: Optional[int] = None):
    """
    Decorator to cache classification endpoint results.
    
    Usage:
        @app.route('/api/classify_aurora', methods=['POST'])
        @cached_classify('aurora')
        def classify_aurora():
            ...
    """
    def decorator(f):
        def wrapper(*args, **kwargs):
            from flask import request, jsonify, make_response
            
            data = request.json or {}
            
            # Try to get from cache
            cached_result, is_hit = classification_cache.get(endpoint, data)
            
            if is_hit:
                # Return cached result with headers
                response = make_response(jsonify(cached_result))
                response.headers['X-Cache'] = 'HIT'
                response.headers['X-Cache-Age'] = str(cached_result['_cache_meta']['age_seconds'])
                return response
            
            # Cache miss - call the actual function
            result = f(*args, **kwargs)
            
            # Handle Flask response objects
            if hasattr(result, 'get_json'):
                result_data = result.get_json()
                status_code = result.status_code
            else:
                result_data = result
                status_code = 200
            
            # Only cache successful responses
            if status_code == 200 and isinstance(result_data, dict) and 'error' not in result_data:
                classification_cache.set(endpoint, data, result_data, ttl)
                # Add cache miss header
                if hasattr(result, 'headers'):
                    result.headers['X-Cache'] = 'MISS'
            
            return result
        
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator
