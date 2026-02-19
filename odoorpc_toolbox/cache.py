"""Thread-safe TTL cache for static Odoo lookups.

Provides a TTLCache class with configurable maxsize and time-to-live eviction,
plus a @cached_lookup decorator for caching EqOdooConnection helper methods.
"""

from __future__ import annotations

import functools
import threading
import time
from typing import Any


class TTLCache:
    """Thread-safe cache with time-to-live eviction and max size limit.

    Entries expire after ``ttl`` seconds and are lazily evicted on access.
    When ``maxsize`` is reached, the oldest entry is removed.

    Args:
        maxsize: Maximum number of entries (default: 256).
        ttl: Time-to-live in seconds (default: 3600).

    Example:
        >>> cache = TTLCache(maxsize=100, ttl=600)
        >>> cache.set("key", "value")
        >>> cache.get("key")
        'value'
    """

    def __init__(self, maxsize: int = 256, ttl: float = 3600) -> None:
        self._maxsize = maxsize
        self._ttl = ttl
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock = threading.Lock()

    @property
    def maxsize(self) -> int:
        """Maximum number of cache entries."""
        return self._maxsize

    @property
    def ttl(self) -> float:
        """Time-to-live in seconds."""
        return self._ttl

    def get(self, key: str) -> Any | None:
        """Retrieve a value by key, returning None if missing or expired.

        Args:
            key: The cache key.

        Returns:
            The cached value or None if not found/expired.
        """
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, timestamp = entry
            if time.monotonic() - timestamp > self._ttl:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any) -> None:
        """Store a value with the current timestamp.

        If maxsize is exceeded, the oldest entry is evicted.

        Args:
            key: The cache key.
            value: The value to cache.
        """
        with self._lock:
            self._store[key] = (value, time.monotonic())
            if len(self._store) > self._maxsize:
                self._evict_oldest()

    def _evict_oldest(self) -> None:
        """Remove the oldest entry (by timestamp). Must be called under lock."""
        if not self._store:
            return
        oldest_key = min(self._store, key=lambda k: self._store[k][1])
        del self._store[oldest_key]

    def clear(self) -> None:
        """Remove all entries from the cache."""
        with self._lock:
            self._store.clear()

    def __len__(self) -> int:
        """Return number of entries (including potentially expired ones)."""
        return len(self._store)

    def __contains__(self, key: str) -> bool:
        """Check if a non-expired entry exists for key."""
        return self.get(key) is not None


def cached_lookup(cache_attr: str = "_lookup_cache"):
    """Decorator that caches lookup method results on an EqOdooConnection instance.

    The decorated method's arguments are used to build a cache key.
    The cache is stored on the instance as the attribute named by ``cache_attr``.

    Args:
        cache_attr: Name of the TTLCache attribute on the instance (default: '_lookup_cache').

    Returns:
        Decorator function.

    Example:
        >>> class MyConnection:
        ...     _lookup_cache = TTLCache()
        ...
        ...     @cached_lookup()
        ...     def get_country_id(self, code):
        ...         return expensive_rpc_call(code)
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            cache = getattr(self, cache_attr, None)
            if cache is None:
                return func(self, *args, **kwargs)

            # Build cache key from method name + arguments
            key_parts = [func.__name__]
            key_parts.extend(str(a) for a in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)

            result = cache.get(cache_key)
            if result is not None:
                return result

            result = func(self, *args, **kwargs)
            if result is not None:
                cache.set(cache_key, result)
            return result

        return wrapper

    return decorator
