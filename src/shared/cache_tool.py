"""Small in-memory TTL cache shared by ported fetchers."""

import threading
import time

import settings


_cache = {}
_cache_lock = threading.Lock()
_inflight = {}
_INFLIGHT_WAIT_SECONDS = 180


def _entry_ttl(hit):
    return hit[2] if len(hit) > 2 else settings.CACHE_TTL


def cached(key, force, fetch_fn, ttl=None):
    wait_event = None
    with _cache_lock:
        read_at = time.time()
        hit = _cache.get(key)
        if hit and not force and read_at - hit[0] < _entry_ttl(hit):
            return hit[1], hit[0]
        if not force:
            wait_event = _inflight.get(key)
        if wait_event is None:
            own_event = threading.Event()
            _inflight[key] = own_event

    if wait_event is not None:
        wait_event.wait(timeout=_INFLIGHT_WAIT_SECONDS)
        with _cache_lock:
            current = _cache.get(key)
            if current is not None and current is not hit:
                return current[1], current[0]
            own_event = threading.Event()
            _inflight[key] = own_event

    try:
        result = fetch_fn()
        effective_ttl = ttl(result) if callable(ttl) else ttl
        if effective_ttl is None:
            effective_ttl = settings.CACHE_TTL
        with _cache_lock:
            fetched_at = time.time()
            current = _cache.get(key)
            if current is not None and current is not hit:
                return result, fetched_at
            if current and fetched_at <= current[0]:
                fetched_at = current[0] + 0.000001
            _cache[key] = (fetched_at, result, effective_ttl)
        return result, fetched_at
    finally:
        with _cache_lock:
            if _inflight.get(key) is own_event:
                del _inflight[key]
        own_event.set()


def ttl_for(key):
    with _cache_lock:
        hit = _cache.get(key)
        return _entry_ttl(hit) if hit else settings.CACHE_TTL
