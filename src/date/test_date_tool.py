import threading
import unittest
from unittest import mock

from date import date_tool
from shared import cache_tool


class DateToolTest(unittest.TestCase):
    def setUp(self):
        cache_tool._cache.clear()

    def tearDown(self):
        cache_tool._cache.clear()

    def test_date_radar_merges_video_and_trend_ideas(self):
        barrier = threading.Barrier(len(date_tool.DATE_QUERIES_BY_COUNTRY["KR"]))

        def fake_merge(queries, period, shorts, country):
            barrier.wait(timeout=2)
            query = queries[0]
            return [
                {
                    "id": "vid-" + query,
                    "title": query + " 영상",
                    "channel": "dateclub",
                    "views": 1000,
                    "viewsText": "1천회",
                    "published": "1일 전",
                    "thumbnail": "https://img.test/" + query + ".jpg",
                }
            ]

        trends = [
            {
                "keyword": "서울 전시 데이트",
                "traffic": "20,000+",
                "trafficValue": 20000,
                "picture": "https://img.test/trend.jpg",
                "news": [{"url": "https://news.test/date", "source": "News"}],
            },
            {"keyword": "정치 뉴스", "traffic": "50,000+", "trafficValue": 50000, "news": []},
        ]

        with (
            mock.patch("date.date_tool.youtube_tool.merge_yt_searches", side_effect=fake_merge),
            mock.patch("date.date_tool.trends_tool.fetch_trends", return_value=(trends, [])),
        ):
            data, fetched_at, cache_ttl = date_tool.get_date_radar("KR")

        self.assertGreater(fetched_at, 0)
        self.assertGreater(cache_ttl, 0)
        self.assertEqual(len(data["briefing"]), 2)
        self.assertEqual(len(data["ideas"]), 6)
        self.assertEqual(data["errors"], [])
        self.assertTrue(
            any(
                item["type"] == "trend" and item["title"] == "서울 전시 데이트"
                for item in data["ideas"]
            )
        )
        self.assertFalse(any(item["title"] == "정치 뉴스" for item in data["ideas"]))
        self.assertTrue(all(item["url"].startswith("https://") for item in data["ideas"]))

    def test_interleave_ranks_each_source_by_its_own_metric(self):
        videos = [
            {"title": "weak video", "score": 10},
            {"title": "strong video", "score": 1000},
        ]
        trends = [
            {"title": "weak trend", "score": 1},
            {"title": "strong trend", "score": 100000},
        ]

        ideas = date_tool._interleave_ideas(videos, trends)

        self.assertEqual(
            [item["title"] for item in ideas],
            ["strong video", "strong trend", "weak video", "weak trend"],
        )

    def test_date_relevance_requires_direct_date_or_activity_with_context(self):
        self.assertTrue(date_tool._is_date_related("서울 데이트 코스"))
        self.assertTrue(date_tool._is_date_related("커플 전시 추천"))
        self.assertFalse(date_tool._is_date_related("일본 여행"))
        self.assertFalse(date_tool._is_date_related("지역 카페 휴무 뉴스"))
        self.assertFalse(date_tool._is_date_related("앱 업데이트 소식"))

    def test_total_failure_uses_negative_ttl_and_reports_source_errors(self):
        trend_error = {"country": "KR", "kind": "TimeoutError"}
        with (
            mock.patch(
                "date.date_tool.youtube_tool.merge_yt_searches",
                side_effect=TimeoutError("youtube unavailable"),
            ),
            mock.patch(
                "date.date_tool.trends_tool.fetch_trends",
                return_value=([], [trend_error]),
            ),
        ):
            data, _, cache_ttl = date_tool.get_date_radar("KR", force=True)

        self.assertEqual(data["ideas"], [])
        self.assertEqual(cache_ttl, date_tool.NEGATIVE_CACHE_TTL)
        error_kinds = [error["kind"] for error in data["errors"]]
        self.assertEqual(error_kinds.count("youtube"), 5)
        self.assertEqual(error_kinds.count("trends"), 1)

    def test_empty_youtube_source_uses_negative_ttl(self):
        with (
            mock.patch(
                "date.date_tool.youtube_tool.merge_yt_searches", return_value=[]
            ),
            mock.patch(
                "date.date_tool.trends_tool.fetch_trends", return_value=([], [])
            ),
        ):
            data, _, cache_ttl = date_tool.get_date_radar("KR", force=True)

        self.assertEqual(data["ideas"], [])
        self.assertEqual(
            data["errors"], [{"kind": "youtube", "error": "EmptyResult"}]
        )
        self.assertEqual(cache_ttl, date_tool.NEGATIVE_CACHE_TTL)

    def test_country_specific_queries_do_not_fetch_non_kr_trends(self):
        for country in ("US", "JP"):
            calls = []

            def fake_merge(queries, period, shorts, requested_country):
                calls.append((queries[0], requested_country))
                return []

            with self.subTest(country=country):
                with (
                    mock.patch(
                        "date.date_tool.youtube_tool.merge_yt_searches",
                        side_effect=fake_merge,
                    ),
                    mock.patch(
                        "date.date_tool.trends_tool.fetch_trends"
                    ) as fetch_trends,
                ):
                    date_tool.get_date_radar(country, force=True)

                expected_queries = {
                    query for query, _ in date_tool.DATE_QUERIES_BY_COUNTRY[country]
                }
                self.assertEqual({query for query, _ in calls}, expected_queries)
                self.assertTrue(all(requested == country for _, requested in calls))
                fetch_trends.assert_not_called()

    def test_unknown_country_falls_back_to_kr_and_uses_cache(self):
        calls = []

        def fake_fetch(country):
            calls.append(country)
            return {"ideas": [], "briefing": [country]}

        with mock.patch("date.date_tool._fetch_date_radar", side_effect=fake_fetch):
            first, first_ts, _ = date_tool.get_date_radar("ca")
            second, second_ts, _ = date_tool.get_date_radar("KR")

        self.assertEqual(first, {"ideas": [], "briefing": ["KR"]})
        self.assertEqual(second, first)
        self.assertEqual(second_ts, first_ts)
        self.assertEqual(calls, ["KR"])
        self.assertIn(("date_radar", "KR"), cache_tool._cache)


if __name__ == "__main__":
    unittest.main()
