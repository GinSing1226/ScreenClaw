"""
Cache utilities for performance optimization
"""
from threading import Lock
from time import time
from typing import Dict, Any, Optional, Callable
from functools import wraps


class TTLCache:
    """Simple thread-safe TTL (Time-To-Live) cache.

    Provides a thread-safe in-memory cache with automatic entry expiration.
    Each cached value is associated with a timestamp and expires after the
    configured TTL period.
    """

    def __init__(self, ttl_seconds: float = 60.0):
        """Initialize a new TTLCache.

        Args:
            ttl_seconds: Time-to-live in seconds for cached entries.
                        Entries older than this will be automatically expired.
                        Defaults to 60.0 seconds.
        """
        self._cache: Dict[str, tuple[float, Any]] = {}
        self._lock = Lock()
        self._ttl = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired.

        Args:
            key: The cache key to retrieve.

        Returns:
            The cached value if found and not expired, None otherwise.
        """
        with self._lock:
            if key in self._cache:
                timestamp, value = self._cache[key]
                if time() - timestamp < self._ttl:
                    return value
                # Expired, remove it
                del self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Set value in cache with current timestamp.

        Args:
            key: The cache key to store.
            value: The value to cache.
        """
        with self._lock:
            self._cache[key] = (time(), value)

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()

    def invalidate(self, key: str) -> None:
        """Invalidate specific cache entry.

        Args:
            key: The cache key to invalidate.
        """
        with self._lock:
            self._cache.pop(key, None)


def cached_class_property(ttl_seconds: float = 60.0):
    """Decorator for class-level cached properties with TTL.

    WARNING: This decorator creates a SINGLE shared cache instance at function
    definition time that is used across ALL instances of the class. This is
    designed for class-level caching where you want to share computed values
    across all instances.

    Behavior:
    - The cache is shared globally across all class instances
    - Uses instance id (id(self)) + function name as cache key to distinguish
      between different instances in the shared cache
    - Cached values expire after ttl_seconds
    - Thread-safe through TTLCache's internal locking

    Use cases:
    - Expensive computations that are identical across instances
    - Class-level resources or configuration
    - When you want instance A to benefit from instance B's computation

    For per-instance caching, use a different approach (e.g., store cache
    in self._cache in __init__).

    Args:
        ttl_seconds: Time-to-live in seconds for cached values. Defaults to 60.0.

    Returns:
        A decorator function that can be applied to class methods.
    """
    cache = TTLCache(ttl_seconds)

    def decorator(func: Callable) -> property:
        """Decorator that wraps the function with caching logic.

        Args:
            func: The function to decorate. Should be a method that takes self.

        Returns:
            A property object that caches the function's return value.
        """
        @wraps(func)
        def wrapper(self):
            """Wrapper that implements the caching logic.

            Args:
                self: The class instance.

            Returns:
                The cached or freshly computed value.
            """
            # Use instance id + function name as cache key
            # Note: This allows the same shared cache to distinguish between
            # different instances, but the cache itself is shared globally
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
