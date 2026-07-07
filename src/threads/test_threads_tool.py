import json
import tempfile
import unittest
from unittest import mock

from shared import accounts_tool, cache_tool
from threads import threads_tool


def _post(caption="hello"):
    return {
        "post": {
            "caption": {"text": caption},
            "like_count": 8,
            "text_post_app_info": {
                "direct_reply_count": 2,
                "repost_count": 3,
            },
            "image_versions2": {
                "candidates": [{"url": "https://img.test/threads.jpg"}]
            },
            "code": "abc123",
            "taken_at": 123,
        }
    }


class _FakeResponse:
    def __init__(self, data):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.data).encode()


class ThreadsToolTest(unittest.TestCase):
    def setUp(self):
        accounts_tool._sources.clear()
        cache_tool._cache.clear()
        self.tmpdir = tempfile.TemporaryDirectory()
        self.config_patch = mock.patch(
            "shared.accounts_tool.settings.CONFIG_DIR", self.tmpdir.name
        )
        self.config_patch.start()
        threads_tool.register()

    def tearDown(self):
        self.config_patch.stop()
        self.tmpdir.cleanup()
        accounts_tool._sources.clear()
        cache_tool._cache.clear()

    def test_parse_threads_nested_post(self):
        caption = "a" * 300
        data = {"data": [{"node": {"deep": _post(caption)}}]}

        posts = threads_tool._parse_threads(data, "openai")

        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]["account"], "openai")
        self.assertEqual(posts[0]["text"], "a" * 280)
        self.assertEqual(posts[0]["likes"], 8)
        self.assertEqual(posts[0]["replies"], 2)
        self.assertEqual(posts[0]["reposts"], 3)
        self.assertEqual(posts[0]["views"], 0)
        self.assertEqual(posts[0]["media"], "https://img.test/threads.jpg")
        self.assertEqual(posts[0]["url"], "https://www.threads.com/@openai/post/abc123")
        self.assertEqual(posts[0]["createdAt"], 123)

    def test_threads_lsd_and_userid_uses_ig_app_id(self):
        html = b'"LSD",[],{"token":"lsd-token"}'
        captured = {}

        def fake_http_json(url, headers=None, timeout=15):
            captured["url"] = url
            captured["headers"] = headers
            captured["timeout"] = timeout
            return {"data": {"user": {"id": "42"}}}

        with (
            mock.patch(
                "threads.threads_tool.http_tool.http_get",
                return_value=("text/html", html),
            ),
            mock.patch(
                "threads.threads_tool.http_tool.http_json", side_effect=fake_http_json
            ),
        ):
            lsd, user_id = threads_tool._threads_lsd_and_userid("Open AI")

        self.assertEqual(lsd, "lsd-token")
        self.assertEqual(user_id, "42")
        self.assertEqual(
            captured["url"],
            "https://www.instagram.com/api/v1/users/web_profile_info/?username=Open%20AI",
        )
        self.assertEqual(captured["headers"], {"x-ig-app-id": threads_tool.IG_APP_ID})
        self.assertEqual(captured["timeout"], 12)

    def test_fetch_threads_posts_doc_id_loop_and_user_agent_header(self):
        seen_doc_ids = []
        seen_headers = []

        def fake_urlopen(req, timeout=15):
            self.assertEqual(timeout, 12)
            body = req.data.decode()
            for doc_id in threads_tool.THREADS_DOC_IDS:
                if "doc_id=%s" % doc_id in body:
                    seen_doc_ids.append(doc_id)
                    break
            seen_headers.append(dict(req.header_items()))
            if len(seen_doc_ids) == 1:
                return _FakeResponse({"errors": [{"message": "stale doc"}]})
            return _FakeResponse({"data": {"thread": _post("ok")}})

        with (
            mock.patch(
                "threads.threads_tool._threads_lsd_and_userid",
                return_value=("lsd-token", "42"),
            ),
            mock.patch("threads.threads_tool.urllib.request.urlopen", fake_urlopen),
        ):
            posts = threads_tool.fetch_threads_posts("openai")

        self.assertEqual(seen_doc_ids, threads_tool.THREADS_DOC_IDS[:2])
        self.assertEqual(posts[0]["text"], "ok")
        self.assertEqual(
            seen_headers[0]["User-agent"],
            threads_tool.UA,
        )
        self.assertEqual(
            seen_headers[0]["X-ig-app-id"],
            threads_tool.IG_APP_ID_THREADS,
        )

    def test_fetch_threads_posts_all_failures_and_missing_ids(self):
        with mock.patch(
            "threads.threads_tool._threads_lsd_and_userid", return_value=(None, "42")
        ):
            self.assertEqual(threads_tool.fetch_threads_posts("openai"), [])

        with (
            mock.patch(
                "threads.threads_tool._threads_lsd_and_userid",
                return_value=("lsd-token", "42"),
            ),
            mock.patch(
                "threads.threads_tool.urllib.request.urlopen",
                side_effect=TimeoutError,
            ),
        ):
            self.assertEqual(threads_tool.fetch_threads_posts("openai"), [])

    def test_get_threads_posts_cache_key_includes_accounts_tuple(self):
        path = accounts_tool.get_source("threads")["path"]
        with open(path, "w") as f:
            json.dump(["b", "a"], f)

        calls = []

        def fake_fetch(account):
            calls.append(account)
            return [{"account": account}]

        with mock.patch(
            "threads.threads_tool.fetch_threads_posts", side_effect=fake_fetch
        ):
            posts, accounts, fetched_at = threads_tool.get_threads_posts(False)
            posts2, accounts2, fetched_at2 = threads_tool.get_threads_posts(False)

        self.assertEqual(accounts, ["b", "a"])
        self.assertEqual(accounts2, accounts)
        self.assertEqual(posts, [{"account": "b"}, {"account": "a"}])
        self.assertEqual(posts2, posts)
        self.assertEqual(fetched_at2, fetched_at)
        self.assertEqual(calls, ["b", "a"])
        self.assertIn(("threads", ("b", "a")), cache_tool._cache)


if __name__ == "__main__":
    unittest.main()
