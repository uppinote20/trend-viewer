import concurrent.futures
import json
import os
import tempfile
import threading
import unittest
from collections import Counter
from unittest import mock

import settings
from analysis import aggregate_tool
from shared import accounts_tool, cache_tool


class AggregateToolTests(unittest.TestCase):
    def setUp(self):
        accounts_tool._sources.clear()
        cache_tool._cache.clear()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.config_patch = mock.patch.object(settings, "CONFIG_DIR", self.tmpdir.name)
        self.config_patch.start()

        self.trends = mock.patch.object(
            aggregate_tool.trends_tool,
            "get_trends",
            return_value=([], 0, [], 3600),
        ).start()
        self.youtube = mock.patch.object(
            aggregate_tool.youtube_tool, "get_videos", return_value=([], 0)
        ).start()
        self.reels = mock.patch.object(
            aggregate_tool.reels_tool,
            "get_reels",
            return_value=([], [], 0, [], 3600),
        ).start()
        self.x_posts = mock.patch.object(
            aggregate_tool.x_twitter_tool,
            "get_x_posts",
            return_value=([], [], 0, [], 3600),
        ).start()
        self.threads = mock.patch.object(
            aggregate_tool.threads_tool,
            "get_threads_posts",
            return_value=([], [], 0, [], 3600),
        ).start()
        self.tiktok = mock.patch.object(
            aggregate_tool.tiktok_tool, "get_tiktok", return_value=([], [], 0)
        ).start()
        self.ai_news = mock.patch.object(
            aggregate_tool.ai_news_tool,
            "get_ai_data",
            return_value=({"news": [], "models": {}}, 0),
        ).start()
        self.addCleanup(mock.patch.stopall)

    def tearDown(self):
        accounts_tool._sources.clear()
        cache_tool._cache.clear()
        self.config_patch.stop()
        self.tmpdir.cleanup()

    def test_collect_snapshot_maps_every_adapter_contract(self):
        self.trends.return_value = (
            [
                {
                    "keyword": "Trend One",
                    "trafficValue": "100",
                    "ts": 11,
                    "news": [{"url": "https://news.test/one"}],
                },
                {"keyword": "No News", "trafficValue": 5, "ts": 12, "news": []},
            ],
            1,
            [],
            3600,
        )
        self.youtube.return_value = ([{"id": "yt1", "title": "YT", "views": "200"}], 2)
        self.reels.return_value = (
            [{"title": "Reel", "url": "https://reel.test/1", "views": 300, "takenAt": 13}],
            [],
            3,
            [],
            3600,
        )
        self.x_posts.return_value = (
            [
                {"text": "view metric", "url": "https://x.test/view", "views": 8, "likes": 100},
                {"text": "like fallback", "url": "https://x.test/like", "views": 0, "likes": 12},
            ],
            [],
            4,
            [],
            3600,
        )
        self.threads.return_value = (
            [
                {"text": "lower", "url": "https://threads.test/low", "likes": 2, "createdAt": 14},
                {"text": "higher", "url": "https://threads.test/high", "likes": 9, "createdAt": 15},
            ],
            [],
            5,
            [],
            3600,
        )
        self.tiktok.return_value = (
            [{"title": "Tik", "url": "https://tik.test/1", "views": 400, "createdAt": 16}],
            [],
            6,
        )
        self.ai_news.return_value = (
            {"news": [{"title": "AI News", "link": "https://ai.test/1", "ts": 17}]},
            7,
        )

        snapshot = aggregate_tool.collect_snapshot(country="KR", deadline=1)
        by_title = {item["title"]: item for item in snapshot["items"]}

        self.assertEqual(by_title["Trend One"], {
            "platform": "trends", "title": "Trend One", "url": "https://news.test/one",
            "metric": 100, "ts": 11.0,
        })
        self.assertEqual(by_title["No News"]["url"], "https://www.google.com/search?q=No+News")
        self.assertEqual(by_title["YT"]["url"], "https://www.youtube.com/watch?v=yt1")
        self.assertEqual((by_title["YT"]["metric"], by_title["YT"]["ts"]), (200, 0.0))
        self.assertEqual((by_title["Reel"]["metric"], by_title["Reel"]["ts"]), (300, 13.0))
        self.assertEqual((by_title["like fallback"]["metric"], by_title["like fallback"]["ts"]), (12, 0.0))
        self.assertEqual(by_title["view metric"]["metric"], 8)
        self.assertEqual((by_title["higher"]["metric"], by_title["higher"]["ts"]), (9, 15.0))
        self.assertEqual((by_title["Tik"]["metric"], by_title["Tik"]["ts"]), (400, 16.0))
        self.assertEqual((by_title["AI News"]["metric"], by_title["AI News"]["ts"]), (0, 17.0))
        self.assertLess(
            snapshot["items"].index(by_title["like fallback"]),
            snapshot["items"].index(by_title["view metric"]),
        )
        self.assertLess(
            snapshot["items"].index(by_title["higher"]),
            snapshot["items"].index(by_title["lower"]),
        )

    def test_collect_snapshot_enforces_channel_caps(self):
        self.trends.return_value = (
            [{"keyword": "T%d" % i, "trafficValue": i, "ts": i, "news": []} for i in range(25)],
            0,
            [],
            3600,
        )
        self.youtube.return_value = (
            [{"id": str(i), "title": "Y%d" % i, "views": i} for i in range(25)],
            0,
        )
        self.reels.return_value = (
            [{"title": "R%d" % i, "url": str(i), "views": i, "takenAt": i} for i in range(25)],
            [], 0, [], 3600,
        )
        self.x_posts.return_value = (
            [{"text": "X%d" % i, "url": str(i), "views": i, "likes": i} for i in range(25)],
            [], 0, [], 3600,
        )
        self.threads.return_value = (
            [{"text": "H%d" % i, "url": str(i), "likes": i, "createdAt": i} for i in range(25)],
            [], 0, [], 3600,
        )
        self.tiktok.return_value = (
            [{"title": "K%d" % i, "url": str(i), "views": i, "createdAt": i} for i in range(25)],
            [], 0,
        )
        self.ai_news.return_value = (
            {"news": [{"title": "A%d" % i, "link": str(i), "ts": i} for i in range(35)]},
            0,
        )

        counts = Counter(
            item["platform"] for item in aggregate_tool.collect_snapshot(deadline=1)["items"]
        )
        self.assertEqual(
            counts,
            Counter({
                "trends": 20, "youtube": 20, "reels": 20, "x": 20,
                "threads": 20, "tiktok": 20, "ai_news": 30,
            }),
        )

    def test_collect_snapshot_returns_fixed_order_partial_on_deadline(self):
        release = threading.Event()
        getter_finished = threading.Event()
        executors = []
        real_executor = concurrent.futures.ThreadPoolExecutor

        def blocked_tiktok(force):
            del force
            try:
                release.wait(2)
                return [], [], 0
            finally:
                getter_finished.set()

        def executor_factory(*args, **kwargs):
            executor = real_executor(*args, **kwargs)
            executors.append(executor)
            return executor

        self.trends.return_value = ([{"keyword": "A", "trafficValue": 1, "news": []}], 0, [], 1)
        self.youtube.return_value = ([{"id": "b", "title": "B", "views": 1}], 0)
        self.reels.return_value = ([{"title": "C", "url": "c", "views": 1}], [], 0, [], 1)
        self.x_posts.return_value = ([{"text": "D", "url": "d", "views": 1}], [], 0, [], 1)
        self.threads.return_value = ([{"text": "E", "url": "e", "likes": 1}], [], 0, [], 1)
        self.tiktok.side_effect = blocked_tiktok
        self.ai_news.return_value = ({"news": [{"title": "G", "link": "g"}]}, 0)

        try:
            with mock.patch.object(
                aggregate_tool.concurrent.futures,
                "ThreadPoolExecutor",
                side_effect=executor_factory,
            ):
                snapshot = aggregate_tool.collect_snapshot(deadline=0.02)
            self.assertEqual(
                [item["platform"] for item in snapshot["items"]],
                ["trends", "youtube", "reels", "x", "threads", "ai_news"],
            )
            self.assertIn({"channel": "tiktok", "kind": "timeout"}, snapshot["errors"])
        finally:
            release.set()
            self.assertTrue(getter_finished.wait(1))
            for executor in executors:
                for worker in executor._threads:
                    worker.join(1)
                    self.assertFalse(worker.is_alive())

    def test_collect_snapshot_contains_channel_error_when_getter_raises(self):
        self.trends.return_value = (
            [{"keyword": "Still Here", "trafficValue": 10, "news": []}], 0, [], 1
        )
        self.youtube.side_effect = RuntimeError("boom")

        snapshot = aggregate_tool.collect_snapshot(deadline=1)

        self.assertEqual([item["platform"] for item in snapshot["items"]], ["trends"])
        self.assertIn({"channel": "youtube", "kind": "error"}, snapshot["errors"])

    def test_collect_snapshot_harvests_embedded_error_indexes(self):
        self.trends.return_value = ([], 1, [{"kind": "trend-feed"}], 30)
        self.reels.return_value = ([], [], 2, [{"kind": "reels-feed"}], 30)
        self.x_posts.return_value = ([], [], 3, [{"kind": "x-feed"}], 30)
        self.threads.return_value = ([], [], 4, [{"kind": "threads-feed"}], 30)

        snapshot = aggregate_tool.collect_snapshot(deadline=1)

        self.assertEqual(snapshot["errors"], [
            {"kind": "trend-feed", "channel": "trends"},
            {"kind": "reels-feed", "channel": "reels"},
            {"kind": "x-feed", "channel": "x"},
            {"kind": "threads-feed", "channel": "threads"},
        ])

    def test_collect_snapshot_propagates_force_to_every_getter(self):
        aggregate_tool.collect_snapshot(country="JP", force=True, deadline=1)

        self.trends.assert_called_once_with("JP", True)
        self.youtube.assert_called_once_with("전체", "week", False, True, country="JP")
        self.reels.assert_called_once_with(True)
        self.x_posts.assert_called_once_with(True)
        self.threads.assert_called_once_with(True)
        self.tiktok.assert_called_once_with(True)
        self.ai_news.assert_called_once_with(True)

    def test_ensure_registered_repairs_cleared_registry_before_getters(self):
        aggregate_tool.ensure_registered()
        self.assertTrue({"reels", "threads", "tiktok", "x"}.issubset(accounts_tool._sources))
        accounts_tool._sources.clear()

        def require_source(name, result):
            def getter(force):
                del force
                if accounts_tool.get_source(name) is None:
                    raise KeyError(name)
                return result
            return getter

        self.reels.side_effect = require_source("reels", ([], [], 0, [], 1))
        self.threads.side_effect = require_source("threads", ([], [], 0, [], 1))
        self.tiktok.side_effect = require_source("tiktok", ([], [], 0))
        self.x_posts.side_effect = require_source("x", ([], [], 0, [], 1))

        snapshot = aggregate_tool.collect_snapshot(deadline=1)

        self.assertEqual(snapshot["errors"], [])
        self.assertTrue({"reels", "threads", "tiktok", "x"}.issubset(accounts_tool._sources))

    def test_correlate_scores_cross_platform_and_single_trend_without_double_count(self):
        snapshot = {"items": [
            {"platform": "trends", "title": "Alpha Launch", "url": "t1", "metric": 99, "ts": 0},
            {"platform": "youtube", "title": "Alpha Launch coverage", "url": "y1", "metric": 999, "ts": 0},
            {"platform": "trends", "title": "Solo Topic", "url": "t2", "metric": 99, "ts": 0},
        ], "errors": []}

        topics = aggregate_tool.correlate(snapshot)

        self.assertEqual([topic["keyword"] for topic in topics], ["alpha launch", "solo topic"])
        self.assertEqual(topics[0]["score"], 7.5)
        self.assertEqual(topics[0]["platforms"], ["trends", "youtube"])
        self.assertEqual(topics[1]["score"], 2.0)
        self.assertNotIn("alpha", [topic["keyword"] for topic in topics])
        self.assertEqual(
            [(item["platform"], item["url"]) for item in topics[0]["items"]],
            [("trends", "t1"), ("youtube", "y1")],
        )

    def test_correlate_emits_only_real_two_platform_fallback_overlap(self):
        topics = aggregate_tool.correlate({"items": [
            {"platform": "youtube", "title": "Nebula breakthrough", "url": "y", "metric": 99},
            {"platform": "x", "title": "Nebula discovery", "url": "x", "metric": 99},
        ]})
        self.assertEqual([topic["keyword"] for topic in topics], ["nebula"])
        self.assertEqual(topics[0]["platforms"], ["x", "youtube"])

        no_overlap = aggregate_tool.correlate({"items": [
            {"platform": "youtube", "title": "Orchid canyon", "url": "y", "metric": 9},
            {"platform": "x", "title": "Quartz meadow", "url": "x", "metric": 9},
        ]})
        self.assertEqual(no_overlap, [])

    def test_correlate_breaks_score_ties_by_keyword(self):
        topics = aggregate_tool.correlate({"items": [
            {"platform": "youtube", "title": "Beta prism", "url": "yb", "metric": 9},
            {"platform": "x", "title": "Beta canyon", "url": "xb", "metric": 9},
            {"platform": "youtube", "title": "Alpha comet", "url": "ya", "metric": 9},
            {"platform": "x", "title": "Alpha orbit", "url": "xa", "metric": 9},
        ]})
        self.assertEqual([topic["keyword"] for topic in topics], ["alpha", "beta"])

    def test_velocity_covers_rising_falling_flat_and_new(self):
        now = 100000.0
        topics = [
            {"keyword": "rising", "score": 12.0},
            {"keyword": "falling", "score": 8.0},
            {"keyword": "flat", "score": 10.5},
            {"keyword": "new", "score": 1.0},
        ]
        history = [
            {"ts": now - 7200, "country": "KR", "topics": {"rising": 1, "falling": 1, "flat": 1}},
            {"ts": now - 3600, "country": "KR", "topics": {"rising": 10, "falling": 10, "flat": 10}},
        ]

        result = aggregate_tool.velocity(topics, history, "KR", now)

        self.assertEqual(
            {topic["keyword"]: topic["velocity"] for topic in result["topics"]},
            {"rising": "rising", "falling": "falling", "flat": "flat", "new": "new"},
        )
        self.assertEqual(
            result["velocityBaseline"], {"available": True, "elapsedSeconds": 3600}
        )

    def test_velocity_is_insufficient_without_same_country_baseline_in_window(self):
        now = 100000.0
        history = [
            {"ts": now - 1000, "country": "KR", "topics": {"topic": 1}},
            {"ts": now - 90000, "country": "KR", "topics": {"topic": 1}},
            {"ts": now - 3600, "country": "JP", "topics": {"topic": 1}},
        ]

        result = aggregate_tool.velocity([{"keyword": "topic", "score": 2}], history, "KR", now)

        self.assertEqual(result, {
            "topics": [{"keyword": "topic", "score": 2, "velocity": "insufficient"}],
            "velocityBaseline": {"available": False, "elapsedSeconds": None},
        })

    def test_history_missing_and_corrupt_files_reset_to_empty(self):
        self.assertEqual(aggregate_tool.load_history(), [])
        path = os.path.join(self.tmpdir.name, "analysis_history.json")
        with open(path, "w", encoding="utf-8") as history_file:
            history_file.write("{not-json")
        self.assertEqual(aggregate_tool.load_history(), [])

        self.assertTrue(
            aggregate_tool.record_history("KR", [{"keyword": "fixed", "score": 1}], now=1)
        )
        with open(path, encoding="utf-8") as history_file:
            self.assertEqual(json.load(history_file)[0]["topics"], {"fixed": 1})

    def test_history_ring_keeps_only_latest_48_entries(self):
        for index in range(55):
            self.assertTrue(aggregate_tool.record_history("KR", [], now=index))

        history = aggregate_tool.load_history()

        self.assertEqual(len(history), 48)
        self.assertEqual((history[0]["ts"], history[-1]["ts"]), (7.0, 54.0))

    def test_history_lock_keeps_concurrent_writer_json_valid(self):
        def writer(offset):
            for index in range(10):
                aggregate_tool.record_history(
                    "KR", [{"keyword": "topic-%d" % offset, "score": index}], now=offset + index
                )

        writers = [threading.Thread(target=writer, args=(offset,)) for offset in (100, 200)]
        for thread in writers:
            thread.start()
        for thread in writers:
            thread.join(2)
            self.assertFalse(thread.is_alive())

        path = os.path.join(self.tmpdir.name, "analysis_history.json")
        with open(path, encoding="utf-8") as history_file:
            history = json.load(history_file)
        self.assertEqual(len(history), 20)
        self.assertTrue(all(set(entry) == {"ts", "country", "topics"} for entry in history))

    def test_analyze_empty_snapshot_has_exact_insufficient_envelope_and_briefing(self):
        with mock.patch.object(aggregate_tool.time, "time", return_value=1000):
            result = aggregate_tool.analyze_heuristic("KR", False)

        self.assertEqual(result, {
            "topics": [],
            "velocityBaseline": {"available": False, "elapsedSeconds": None},
            "briefing": [
                "상승세 토픽: 감지되지 않았습니다.",
                "교차 플랫폼 토픽: 감지되지 않았습니다.",
            ],
            "errors": [],
            "generatedBy": "heuristic",
        })

    def test_analyze_uses_prior_history_then_records_current_snapshot(self):
        calls = []

        def velocity_side_effect(topics, history, country, now):
            del history, country, now
            calls.append("velocity")
            return {
                "topics": [dict(topic, velocity="insufficient") for topic in topics],
                "velocityBaseline": {"available": False, "elapsedSeconds": None},
            }

        def record_side_effect(country, topics, now=None):
            del country, topics, now
            calls.append("record")
            return True

        with mock.patch.object(aggregate_tool, "velocity", side_effect=velocity_side_effect), \
                mock.patch.object(aggregate_tool, "record_history", side_effect=record_side_effect):
            aggregate_tool.analyze_heuristic("KR", False)

        self.assertEqual(calls, ["velocity", "record"])

    def test_analyze_exact_eligible_baseline_envelope(self):
        aggregate_tool.record_history("KR", [{"keyword": "alpha", "score": 1.0}], now=1000)
        self.trends.return_value = (
            [{
                "keyword": "Alpha",
                "trafficValue": 99,
                "ts": 100,
                "news": [{"url": "https://trend.test/alpha"}],
            }],
            0,
            [],
            3600,
        )

        with mock.patch.object(aggregate_tool.time, "time", return_value=4600):
            result = aggregate_tool.analyze_heuristic("KR", True)

        self.assertEqual(result, {
            "topics": [{
                "keyword": "alpha",
                "title": "Alpha",
                "platforms": ["trends"],
                "score": 2.0,
                "items": [{
                    "platform": "trends",
                    "title": "Alpha",
                    "url": "https://trend.test/alpha",
                    "metric": 99,
                    "ts": 100.0,
                }],
                "velocity": "rising",
            }],
            "velocityBaseline": {"available": True, "elapsedSeconds": 3600},
            "briefing": [
                "상승세 토픽: Alpha",
                "교차 플랫폼 토픽: 감지되지 않았습니다.",
            ],
            "errors": [],
            "generatedBy": "heuristic",
        })

    def test_analyze_tolerates_history_write_oserror_and_reports_it(self):
        with mock.patch.object(aggregate_tool.os, "replace", side_effect=OSError("read only")):
            result = aggregate_tool.analyze_heuristic("KR", False)

        self.assertEqual(result["topics"], [])
        self.assertIn({"channel": "history", "kind": "error"}, result["errors"])


if __name__ == "__main__":
    unittest.main()
