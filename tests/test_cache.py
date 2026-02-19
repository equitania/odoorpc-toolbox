"""Tests for TTLCache and @cached_lookup decorator."""

import threading
import time

from odoorpc_toolbox.cache import TTLCache, cached_lookup


class TestTTLCache:
    """Tests for the TTLCache class."""

    def test_set_and_get(self):
        """Test basic set and get operations."""
        cache = TTLCache(maxsize=10, ttl=60)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_missing_key(self):
        """Test getting a non-existent key returns None."""
        cache = TTLCache(maxsize=10, ttl=60)
        assert cache.get("missing") is None

    def test_expiry(self):
        """Test that entries expire after TTL."""
        cache = TTLCache(maxsize=10, ttl=0.1)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        time.sleep(0.15)
        assert cache.get("key1") is None

    def test_eviction_on_maxsize(self):
        """Test that oldest entry is evicted when maxsize is exceeded."""
        cache = TTLCache(maxsize=3, ttl=60)
        cache.set("key1", "value1")
        time.sleep(0.01)
        cache.set("key2", "value2")
        time.sleep(0.01)
        cache.set("key3", "value3")
        time.sleep(0.01)
        cache.set("key4", "value4")

        # key1 should have been evicted (oldest)
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"
        assert cache.get("key4") == "value4"

    def test_clear(self):
        """Test clearing the cache."""
        cache = TTLCache(maxsize=10, ttl=60)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        assert len(cache) == 2
        cache.clear()
        assert len(cache) == 0
        assert cache.get("key1") is None

    def test_contains(self):
        """Test __contains__ for non-expired entries."""
        cache = TTLCache(maxsize=10, ttl=60)
        cache.set("key1", "value1")
        assert "key1" in cache
        assert "missing" not in cache

    def test_contains_expired(self):
        """Test __contains__ returns False for expired entries."""
        cache = TTLCache(maxsize=10, ttl=0.1)
        cache.set("key1", "value1")
        time.sleep(0.15)
        assert "key1" not in cache

    def test_len(self):
        """Test __len__ returns number of entries."""
        cache = TTLCache(maxsize=10, ttl=60)
        assert len(cache) == 0
        cache.set("key1", "value1")
        assert len(cache) == 1
        cache.set("key2", "value2")
        assert len(cache) == 2

    def test_overwrite_key(self):
        """Test overwriting an existing key."""
        cache = TTLCache(maxsize=10, ttl=60)
        cache.set("key1", "value1")
        cache.set("key1", "value2")
        assert cache.get("key1") == "value2"
        assert len(cache) == 1

    def test_properties(self):
        """Test maxsize and ttl properties."""
        cache = TTLCache(maxsize=100, ttl=300)
        assert cache.maxsize == 100
        assert cache.ttl == 300

    def test_thread_safety(self):
        """Test concurrent access from multiple threads."""
        cache = TTLCache(maxsize=1000, ttl=60)
        errors = []

        def writer(start, count):
            try:
                for i in range(start, start + count):
                    cache.set(f"key_{i}", f"value_{i}")
            except Exception as e:
                errors.append(e)

        def reader(start, count):
            try:
                for i in range(start, start + count):
                    cache.get(f"key_{i}")
            except Exception as e:
                errors.append(e)

        threads = []
        for i in range(5):
            t = threading.Thread(target=writer, args=(i * 100, 100))
            threads.append(t)
            t = threading.Thread(target=reader, args=(i * 100, 100))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestCachedLookupDecorator:
    """Tests for the @cached_lookup decorator."""

    def test_caching_return_value(self):
        """Test that the decorator caches the return value."""
        call_count = 0

        class FakeConnection:
            _lookup_cache = TTLCache(maxsize=10, ttl=60)

            @cached_lookup()
            def get_something(self, name):
                nonlocal call_count
                call_count += 1
                return 42

        conn = FakeConnection()
        result1 = conn.get_something("test")
        result2 = conn.get_something("test")

        assert result1 == 42
        assert result2 == 42
        assert call_count == 1  # Only called once, second was from cache

    def test_different_args_different_cache(self):
        """Test that different arguments produce different cache entries."""
        call_count = 0

        class FakeConnection:
            _lookup_cache = TTLCache(maxsize=10, ttl=60)

            @cached_lookup()
            def get_something(self, name):
                nonlocal call_count
                call_count += 1
                return hash(name)

        conn = FakeConnection()
        conn.get_something("foo")
        conn.get_something("bar")

        assert call_count == 2

    def test_none_result_not_cached(self):
        """Test that None results are not cached."""
        call_count = 0

        class FakeConnection:
            _lookup_cache = TTLCache(maxsize=10, ttl=60)

            @cached_lookup()
            def get_something(self, name):
                nonlocal call_count
                call_count += 1
                return None

        conn = FakeConnection()
        conn.get_something("test")
        conn.get_something("test")

        assert call_count == 2  # Called twice since None is not cached

    def test_no_cache_attribute(self):
        """Test that the decorator works even without cache attribute (no caching)."""
        call_count = 0

        class FakeConnection:
            @cached_lookup()
            def get_something(self, name):
                nonlocal call_count
                call_count += 1
                return 42

        conn = FakeConnection()
        conn.get_something("test")
        conn.get_something("test")

        assert call_count == 2  # Called twice, no cache

    def test_kwargs_in_cache_key(self):
        """Test that keyword arguments are included in the cache key."""
        call_count = 0

        class FakeConnection:
            _lookup_cache = TTLCache(maxsize=10, ttl=60)

            @cached_lookup()
            def get_something(self, name, active=True):
                nonlocal call_count
                call_count += 1
                return 42 if active else 0

        conn = FakeConnection()
        conn.get_something("test", active=True)
        conn.get_something("test", active=False)

        assert call_count == 2  # Different kwargs = different cache entries

    def test_custom_cache_attr(self):
        """Test using a custom cache attribute name."""
        call_count = 0

        class FakeConnection:
            my_cache = TTLCache(maxsize=10, ttl=60)

            @cached_lookup(cache_attr="my_cache")
            def get_something(self, name):
                nonlocal call_count
                call_count += 1
                return 42

        conn = FakeConnection()
        conn.get_something("test")
        conn.get_something("test")

        assert call_count == 1
