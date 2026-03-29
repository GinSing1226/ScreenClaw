# tests/test_cache_utils.py
import time
import pytest
from app.utils.cache import TTLCache, cached_property


def test_ttl_cache_get_set():
    cache = TTLCache(ttl_seconds=1.0)

    assert cache.get("key1") is None
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"


def test_ttl_cache_expiration():
    cache = TTLCache(ttl_seconds=0.1)

    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"

    time.sleep(0.15)
    assert cache.get("key1") is None


def test_ttl_cache_clear():
    cache = TTLCache(ttl_seconds=1.0)

    cache.set("key1", "value1")
    cache.set("key2", "value2")

    cache.clear()
    assert cache.get("key1") is None
    assert cache.get("key2") is None


def test_ttl_cache_invalidate():
    cache = TTLCache(ttl_seconds=1.0)

    cache.set("key1", "value1")
    cache.invalidate("key1")
    assert cache.get("key1") is None


def test_cached_property_decorator():
    class TestClass:
        def __init__(self):
            self.call_count = 0

        @cached_property(ttl_seconds=1.0)
        def expensive_property(self):
            self.call_count += 1
            return "computed"

    obj = TestClass()
    assert obj.call_count == 0

    # First access computes
    assert obj.expensive_property == "computed"
    assert obj.call_count == 1

    # Second access uses cache
    assert obj.expensive_property == "computed"
    assert obj.call_count == 1

    # Wait for expiration
    time.sleep(1.1)
    assert obj.expensive_property == "computed"
    assert obj.call_count == 2
