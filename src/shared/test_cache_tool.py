import threading
import unittest
from unittest import mock

from shared import cache_tool


class CacheToolTest(unittest.TestCase):
    def setUp(self):
        cache_tool._cache.clear()

    def tearDown(self):
        cache_tool._cache.clear()

    def test_cached_hit(self):
        calls = []
        with mock.patch("time.time", side_effect=[100.0, 101.0, 102.0]):
            result, fetched_at = cache_tool.cached("k", False, lambda: calls.append(1) or "v1")
            result2, fetched_at2 = cache_tool.cached("k", False, lambda: calls.append(2) or "v2")

        self.assertEqual(result, "v1")
        self.assertEqual(result2, "v1")
        self.assertEqual(fetched_at, 101.0)
        self.assertEqual(fetched_at2, 101.0)
        self.assertEqual(calls, [1])

    def test_cached_hit_preserves_seeded_fetched_at(self):
        cache_tool._cache["k"] = (123.0, "old")
        with mock.patch("shared.cache_tool.settings.CACHE_TTL", 10), mock.patch("time.time", return_value=125.0):
            result, fetched_at = cache_tool.cached("k", False, lambda: self.fail("cache hit should not fetch"))

        self.assertEqual(result, "old")
        self.assertEqual(fetched_at, 123.0)

    def test_cached_ttl_expiry(self):
        calls = []
        cache_tool._cache["k"] = (10.0, "old")
        with mock.patch("shared.cache_tool.settings.CACHE_TTL", 5), mock.patch(
            "time.time", side_effect=[20.0, 21.0]
        ):
            result, fetched_at = cache_tool.cached("k", False, lambda: calls.append(1) or "new")

        self.assertEqual(result, "new")
        self.assertEqual(fetched_at, 21.0)
        self.assertEqual(calls, [1])

    def test_cached_per_entry_ttl(self):
        calls = []
        cache_tool._cache["k"] = (10.0, "old", 120)
        with mock.patch("shared.cache_tool.settings.CACHE_TTL", 3600), mock.patch(
            "time.time", side_effect=[200.0, 201.0]
        ):
            result, fetched_at = cache_tool.cached("k", False, lambda: calls.append(1) or "new")

        self.assertEqual(result, "new")
        self.assertEqual(fetched_at, 201.0)
        self.assertEqual(calls, [1])

    def test_cached_ttl_selector_stores_effective_ttl(self):
        with mock.patch("time.time", side_effect=[100.0, 101.0]):
            result, fetched_at = cache_tool.cached(
                "k",
                False,
                lambda: ([], [{"account": "x"}]),
                ttl=lambda outcome: 120 if not outcome[0] and outcome[1] else None,
            )

        self.assertEqual(result, ([], [{"account": "x"}]))
        self.assertEqual(fetched_at, 101.0)
        self.assertEqual(cache_tool.ttl_for("k"), 120)

    def test_cached_force(self):
        cache_tool._cache["k"] = (10.0, "old")
        with mock.patch("time.time", side_effect=[11.0, 12.0]):
            result, fetched_at = cache_tool.cached("k", True, lambda: "forced")

        self.assertEqual(result, "forced")
        self.assertEqual(fetched_at, 12.0)

    def test_cached_concurrent_same_key_miss_coalesces_fetch(self):
        fetch_started = threading.Event()
        second_call_started = threading.Event()
        release_fetch = threading.Event()
        counter_lock = threading.Lock()
        fetch_count = [0]
        outcomes = []
        errors = []

        def fetch():
            with counter_lock:
                fetch_count[0] += 1
            fetch_started.set()
            if not release_fetch.wait(timeout=0.5):
                raise AssertionError("timed out waiting to release the shared fetch")
            return "shared-value"

        def worker(started=None):
            if started is not None:
                started.set()
            try:
                outcomes.append(cache_tool.cached("shared", False, fetch))
            except BaseException as error:
                errors.append(error)

        threads = [
            threading.Thread(target=worker, name="cache-shared-first"),
            threading.Thread(
                target=worker,
                args=(second_call_started,),
                name="cache-shared-second",
            ),
        ]
        threads[0].start()
        try:
            self.assertTrue(fetch_started.wait(timeout=0.5))
            threads[1].start()
            self.assertTrue(second_call_started.wait(timeout=0.5))
        finally:
            release_fetch.set()
            for thread in threads:
                if thread.ident is not None:
                    thread.join(timeout=0.5)

        self.assertTrue(all(not thread.is_alive() for thread in threads))
        if errors:
            raise errors[0]
        self.assertEqual(fetch_count[0], 1)
        self.assertEqual([outcome[0] for outcome in outcomes], ["shared-value"] * 2)

    def test_cached_concurrent_different_keys_do_not_coalesce(self):
        fetch_started = {"first": threading.Event(), "second": threading.Event()}
        release_fetches = threading.Event()
        counter_lock = threading.Lock()
        fetch_counts = {"first": 0, "second": 0}
        outcomes = {}
        errors = []

        def fetch(key):
            with counter_lock:
                fetch_counts[key] += 1
            fetch_started[key].set()
            if not release_fetches.wait(timeout=0.5):
                raise AssertionError("timed out waiting to release independent fetches")
            return key + "-value"

        def worker(key):
            try:
                outcomes[key] = cache_tool.cached(key, False, lambda: fetch(key))
            except BaseException as error:
                errors.append(error)

        threads = [
            threading.Thread(target=worker, args=(key,), name="cache-" + key)
            for key in ("first", "second")
        ]
        for thread in threads:
            thread.start()
        try:
            for started in fetch_started.values():
                self.assertTrue(started.wait(timeout=0.5))
        finally:
            release_fetches.set()
            for thread in threads:
                thread.join(timeout=0.5)

        self.assertTrue(all(not thread.is_alive() for thread in threads))
        if errors:
            raise errors[0]
        self.assertEqual(fetch_counts, {"first": 1, "second": 1})
        self.assertEqual(
            {key: outcome[0] for key, outcome in outcomes.items()},
            {"first": "first-value", "second": "second-value"},
        )

    def test_cached_force_bypasses_inflight_coalescing(self):
        non_force_started = threading.Event()
        force_fetch_started = threading.Event()
        release_non_force = threading.Event()
        counter_lock = threading.Lock()
        fetch_count = [0]
        outcomes = {}
        errors = []

        def non_force_fetch():
            with counter_lock:
                fetch_count[0] += 1
            non_force_started.set()
            if not release_non_force.wait(timeout=0.5):
                raise AssertionError("timed out waiting to release non-force fetch")
            return "non-force"

        def force_fetch():
            with counter_lock:
                fetch_count[0] += 1
            force_fetch_started.set()
            return "forced"

        def worker(name, force, fetch):
            try:
                outcomes[name] = cache_tool.cached("shared", force, fetch)
            except BaseException as error:
                errors.append(error)

        non_force_thread = threading.Thread(
            target=worker,
            args=("non-force", False, non_force_fetch),
            name="cache-non-force",
        )
        force_thread = threading.Thread(
            target=worker,
            args=("force", True, force_fetch),
            name="cache-force",
        )
        threads = [non_force_thread, force_thread]
        non_force_thread.start()
        try:
            self.assertTrue(non_force_started.wait(timeout=0.5))
            force_thread.start()
            self.assertTrue(force_fetch_started.wait(timeout=0.5))
        finally:
            release_non_force.set()
            for thread in threads:
                if thread.ident is not None:
                    thread.join(timeout=0.5)

        self.assertTrue(all(not thread.is_alive() for thread in threads))
        if errors:
            raise errors[0]
        self.assertEqual(fetch_count[0], 2)
        self.assertEqual(outcomes["force"][0], "forced")
        self.assertEqual(outcomes["non-force"][0], "non-force")

    def test_cached_rejects_superseded_commit(self):
        fetch_started = threading.Event()
        release_fetch = threading.Event()
        first_outcome = []
        first_errors = []
        main_times = iter([200.0, 250.0])

        def current_time():
            if threading.current_thread().name == "first-cache-fetch":
                return 300.0 if release_fetch.is_set() else 100.0
            return next(main_times)

        def fetch_first():
            fetch_started.set()
            if not release_fetch.wait(timeout=2):
                raise AssertionError("timed out waiting to finish the first fetch")
            return "first"

        def run_first():
            try:
                first_outcome.append(cache_tool.cached("k", False, fetch_first))
            except BaseException as error:
                first_errors.append(error)

        first_thread = threading.Thread(target=run_first, name="first-cache-fetch")
        with mock.patch("shared.cache_tool.time.time", side_effect=current_time):
            first_thread.start()
            self.assertTrue(fetch_started.wait(timeout=2))

            second_result, second_fetched_at = cache_tool.cached("k", True, lambda: "second")
            release_fetch.set()
            first_thread.join(timeout=2)

        self.assertFalse(first_thread.is_alive())
        if first_errors:
            raise first_errors[0]
        self.assertEqual(first_outcome, [("first", 300.0)])
        self.assertEqual(second_result, "second")
        self.assertEqual(second_fetched_at, 250.0)
        self.assertEqual(cache_tool._cache["k"], (250.0, "second", cache_tool.settings.CACHE_TTL))

    def test_cached_sequential_force_refresh_overwrites(self):
        cache_tool._cache["k"] = (99.0, "old")
        with mock.patch("shared.cache_tool.time.time", return_value=100.0):
            cache_tool.cached("k", True, lambda: "first")
            _, second_fetched_at = cache_tool.cached("k", True, lambda: "second")

        self.assertEqual(
            cache_tool._cache["k"],
            (second_fetched_at, "second", cache_tool.settings.CACHE_TTL),
        )

    def test_cached_fetched_at_is_monotonic_for_same_key(self):
        with mock.patch("shared.cache_tool.time.time", return_value=100.0):
            _, first_fetched_at = cache_tool.cached("same", False, lambda: "first")
            _, second_fetched_at = cache_tool.cached("same", True, lambda: "second")

        self.assertEqual(first_fetched_at, 100.0)
        self.assertEqual(second_fetched_at, 100.000001)

    def test_cached_fetched_at_is_independent_between_keys(self):
        with mock.patch("shared.cache_tool.time.time", return_value=100.0):
            _, first_fetched_at = cache_tool.cached("first", False, lambda: "one")
            _, second_fetched_at = cache_tool.cached("second", False, lambda: "two")

        self.assertEqual(first_fetched_at, 100.0)
        self.assertEqual(second_fetched_at, 100.0)


if __name__ == "__main__":
    unittest.main()
