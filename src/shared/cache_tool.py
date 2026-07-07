"""Small in-memory TTL cache shared by ported fetchers."""

import threading
import time

import settings


_cache = {}
_cache_lock = threading.Lock()


def cached(key, force, fetch_fn):
    now = time.time()
    with _cache_lock:
        hit = _cache.get(key)
        if hit and not force and now - hit[0] < settings.CACHE_TTL:
            return hit[1], hit[0]
    result = fetch_fn()
    fetched_at = time.time()
    with _cache_lock:
        _cache[key] = (fetched_at, result)
    return result, fetched_at
