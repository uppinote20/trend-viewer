"""X/Twitter helpers ported from the upstream stdlib server."""

import json
import re
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

from shared import accounts_tool, cache_tool, http_tool


DEFAULT_X_ACCOUNTS = [
    "OpenAI",
    "runwayml",
    "Kling_ai",
    "GoogleDeepMind",
    "midjourney",
    "LumaLabsAI",
    "pika_labs",
    "heygen_com",
    "elevenlabsio",
    "AIatMeta",
]


def register():
    accounts_tool.register_source(
        "x", "x_accounts.json", DEFAULT_X_ACCOUNTS, preserve_case=True
    )


def _find_timeline_entries(node):
    """Find the timeline entries list in syndication __NEXT_DATA__."""
    if isinstance(node, dict):
        timeline = node.get("timeline")
        if isinstance(timeline, dict) and isinstance(timeline.get("entries"), list):
            return timeline["entries"]
        for value in node.values():
            result = _find_timeline_entries(value)
            if result:
                return result
    elif isinstance(node, list):
        for value in node:
            result = _find_timeline_entries(value)
            if result:
                return result
    return None


def fetch_x_posts(username: str):
    url = (
        "https://syndication.twitter.com/srv/timeline-profile/screen-name/"
        + quote(username)
    )
    try:
        _, body = http_tool.http_get(url, headers={"Accept": "text/html"}, timeout=12)
        html = body.decode("utf-8", "ignore")
        match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
        if not match:
            return []
        data = json.loads(match.group(1))
    except (
        urllib.error.URLError,
        TimeoutError,
        json.JSONDecodeError,
        UnicodeDecodeError,
        OSError,
    ):
        return []

    posts = []
    for entry in _find_timeline_entries(data) or []:
        content = entry.get("content", {}) if isinstance(entry, dict) else {}
        tweet = content.get("tweet")
        if not isinstance(tweet, dict):
            tweet_result = content.get("tweetResult") or {}
            tweet = tweet_result.get("result") if isinstance(tweet_result, dict) else None
        if not isinstance(tweet, dict) or tweet.get("favorite_count") is None:
            continue

        user = tweet.get("user", {}) if isinstance(tweet.get("user"), dict) else {}
        media = ""
        for item in tweet.get("mediaDetails") or []:
            if isinstance(item, dict) and item.get("media_url_https"):
                media = item["media_url_https"]
                break

        views = tweet.get("views")
        posts.append(
            {
                "account": username,
                "name": user.get("name", username),
                "text": (tweet.get("full_text") or tweet.get("text") or "").strip(),
                "likes": tweet.get("favorite_count") or 0,
                "replies": tweet.get("reply_count") or 0,
                "retweets": tweet.get("retweet_count") or 0,
                "views": int(views.get("count", 0)) if isinstance(views, dict) else 0,
                "media": media,
                "url": "https://x.com/%s/status/%s"
                % (username, tweet.get("id_str", "")),
                "createdAt": tweet.get("created_at", ""),
            }
        )
    return posts


def get_x_posts(force: bool):
    source = accounts_tool.get_source("x")
    accounts = accounts_tool.load_accounts(source["path"], source["defaults"])

    def fetch():
        with ThreadPoolExecutor(max_workers=3) as pool:
            results = pool.map(fetch_x_posts, accounts)
        return [post for chunk in results for post in chunk]

    posts, fetched_at = cache_tool.cached(("x", tuple(accounts)), force, fetch)
    return posts, accounts, fetched_at
