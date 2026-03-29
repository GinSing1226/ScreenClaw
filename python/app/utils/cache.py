"""
Cache utilities for performance optimization
"""
from threading import Lock
from time import time
from typing import Dict, Any, Optional, Callable
from functools import wraps


class TTLCache:
    """Simple thread-safe TTL cache"""

    def __init__(self, ttl_seconds: float = 60.0):
        self._cache: Dict[str, tuple[float, Any]] = {}
        self._lock = Lock()
        self._ttl = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        """Get value if not expired"""
        with self._lock:
            if key in self._cache:
                timestamp, value = self._cache[key]
                if time() - timestamp < self._ttl:
                    return value
                # Expired, remove it
                del self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Set value with current timestamp"""
        with self._lock:
            self._cache[key] = (time(), value)

    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()

    def invalidate(self, key: str) -> None:
        """Invalidate specific key"""
        with self._lock:
            self._cache.pop(key, None)


def cached_property(ttl_seconds: float = 60.0):
    """Decorator for cached properties with TTL"""
    cache = TTLCache(ttl_seconds)

    def decorator(func: Callable) -> property:
        @wraps(func)
        def wrapper(self):
            # Use instance id + function name as cache key
            cache_key = f"{id(self)}_{func.__name__}"
            value = cache.get(cache_key)
            if value is not None:
                return value

            # Compute and cache
            value = func(self)
            cache.set(cache_key, value)
            return value

        return property(wrapper)

    return decorator
