"""
MCP Response Caching System
Reduces API costs and improves response times
"""

import json
import hashlib
import pickle
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
from pathlib import Path
import redis
from functools import wraps

class MCPCache:
    """Advanced caching system for MCP responses"""

    def __init__(self, cache_dir: str = "cache", use_redis: bool = False):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.use_redis = use_redis
        self.redis_client = None

        # Default TTL values (in seconds)
        self.ttl_config = {
            'westlaw': 86400,      # 24 hours - case law changes rarely
            'lexisnexis': 86400,   # 24 hours - statutory research
            'gmail': 3600,         # 1 hour - emails change frequently
            'slack': 1800,         # 30 minutes - active communications
            'supabase': 300,       # 5 minutes - database queries
            'github': 600,         # 10 minutes - repository data
        }

        if use_redis:
            self._init_redis()

    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
        except Exception as e:
            print(f"Redis connection failed, falling back to file cache: {e}")
            self.use_redis = False

    def _generate_cache_key(self, service: str, query: str, params: Dict = None) -> str:
        """Generate unique cache key"""
        key_parts = [service, query]
        if params:
            key_parts.append(json.dumps(params, sort_keys=True))
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get file path for cache entry"""
        return self.cache_dir / f"{cache_key}.pkl"

    def get(self, service: str, query: str, params: Dict = None) -> Optional[Any]:
        """Retrieve cached response"""
        cache_key = self._generate_cache_key(service, query, params)

        if self.use_redis and self.redis_client:
            return self._get_from_redis(cache_key)
        else:
            return self._get_from_file(cache_key)

    def _get_from_redis(self, cache_key: str) -> Optional[Any]:
        """Get from Redis cache"""
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            print(f"Redis get error: {e}")
        return None

    def _get_from_file(self, cache_key: str) -> Optional[Any]:
        """Get from file cache"""
        cache_path = self._get_cache_path(cache_key)
        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'rb') as f:
                cache_entry = pickle.load(f)

            # Check if expired
            if cache_entry['expires_at'] < datetime.now():
                cache_path.unlink()
                return None

            return cache_entry['data']
        except Exception as e:
            print(f"Cache read error: {e}")
            return None

    def set(self, service: str, query: str, data: Any, params: Dict = None, ttl: int = None):
        """Store response in cache"""
        cache_key = self._generate_cache_key(service, query, params)
        ttl = ttl or self.ttl_config.get(service, 3600)

        if self.use_redis and self.redis_client:
            self._set_in_redis(cache_key, data, ttl)
        else:
            self._set_in_file(cache_key, data, ttl)

    def _set_in_redis(self, cache_key: str, data: Any, ttl: int):
        """Set in Redis cache"""
        try:
            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(data, default=str)
            )
        except Exception as e:
            print(f"Redis set error: {e}")

    def _set_in_file(self, cache_key: str, data: Any, ttl: int):
        """Set in file cache"""
        cache_path = self._get_cache_path(cache_key)
        cache_entry = {
            'data': data,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(seconds=ttl)
        }

        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_entry, f)
        except Exception as e:
            print(f"Cache write error: {e}")

    def invalidate(self, service: str, query: str = None, params: Dict = None):
        """Invalidate cache entries"""
        if query:
            cache_key = self._generate_cache_key(service, query, params)
            if self.use_redis and self.redis_client:
                self.redis_client.delete(cache_key)
            else:
                cache_path = self._get_cache_path(cache_key)
                if cache_path.exists():
                    cache_path.unlink()
        else:
            # Invalidate all entries for service
            self.clear_service_cache(service)

    def clear_service_cache(self, service: str):
        """Clear all cache entries for a service"""
        if self.use_redis and self.redis_client:
            pattern = f"{service}:*"
            for key in self.redis_client.scan_iter(match=pattern):
                self.redis_client.delete(key)
        else:
            # File cache - would need metadata to track service
            pass

    def clear_all(self):
        """Clear entire cache"""
        if self.use_redis and self.redis_client:
            self.redis_client.flushdb()
        else:
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if self.use_redis and self.redis_client:
            return {
                'type': 'redis',
                'keys': self.redis_client.dbsize(),
                'memory': self.redis_client.info('memory')['used_memory_human']
            }
        else:
            cache_files = list(self.cache_dir.glob("*.pkl"))
            total_size = sum(f.stat().st_size for f in cache_files)
            return {
                'type': 'file',
                'entries': len(cache_files),
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }


def cached_mcp_call(service: str, ttl: int = None):
    """Decorator for caching MCP calls"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache()

            # Extract query from args/kwargs
            query = kwargs.get('query') or (args[0] if args else None)
            params = kwargs.get('params')

            # Try to get from cache
            cached_result = cache.get(service, query, params)
            if cached_result is not None:
                return {
                    'data': cached_result,
                    'source': 'cache',
                    'cached_at': datetime.now().isoformat()
                }

            # Call actual function
            result = func(*args, **kwargs)

            # Cache the result
            if result and not result.get('error'):
                cache.set(service, query, result, params, ttl)

            return result

        return wrapper
    return decorator


# Singleton instance
_cache = None

def get_cache() -> MCPCache:
    """Get singleton cache instance"""
    global _cache
    if _cache is None:
        _cache = MCPCache()
    return _cache
