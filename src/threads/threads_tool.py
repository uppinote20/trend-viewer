"""Threads helpers ported from the upstream stdlib server."""

import json
import re
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote, urlencode

from reels.reels_tool import IG_APP_ID
from settings import UA
from shared import accounts_tool, cache_tool, http_tool


DEFAULT_THREADS_ACCOUNTS = [
    "openai",
    "runway",
    "google",
    "meta.ai",
    "zuck",
]
IG_APP_ID_THREADS = "238260118697367"
THREADS_DOC_IDS = [
    "25073444226023094",
    "7451607104958938",
    "23996318550159868",
    "9925907010825989",
    "26286467210919721",
]


def register():
    accounts_tool.register_source(
        "threads", "threads_accounts.json", DEFAULT_THREADS_ACCOUNTS
    )


def _threads_lsd_and_userid(username: str):
    lsd = None
    try:
        _, body = http_tool.http_get(
            "https://www.threads.com/@" + quote(username), timeout=12
        )
        match = re.search(
            r'"LSD",\[\],\{"token":"([^"]+)"', body.decode("utf-8", "ignore")
        )
        lsd = match.group(1) if match else None
    except (urllib.error.URLError, TimeoutError, OSError):
        pass

    user_id = None
    try:
        info = http_tool.http_json(
            "https://www.instagram.com/api/v1/users/web_profile_info/?username="
            + quote(username),
            headers={"x-ig-app-id": IG_APP_ID},
            timeout=12,
        )
        user_id = ((info.get("data") or {}).get("user") or {}).get("id")
    except (
        urllib.error.URLError,
        TimeoutError,
        json.JSONDecodeError,
        UnicodeDecodeError,
        OSError,
    ):
        pass
    return lsd, user_id


def fetch_threads_posts(username: str):
    lsd, user_id = _threads_lsd_and_userid(username)
    if not lsd or not user_id:
        return []

    headers = {
        "X-FB-LSD": lsd,
        "X-IG-App-ID": IG_APP_ID_THREADS,
        "Sec-Fetch-Site": "same-origin",
        "X-FB-Friendly-Name": "BarcelonaProfileThreadsTabQuery",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    for doc_id in THREADS_DOC_IDS:
        payload = urlencode(
            {
                "lsd": lsd,
                "doc_id": doc_id,
                "variables": json.dumps(
                    {
                        "userID": str(user_id),
                        "__relay_internal__pv__BarcelonaIsLoggedInrelayprovider": False,
                    }
                ),
            }
        ).encode()
        req = urllib.request.Request(
            "https://www.threads.com/api/graphql", data=payload
        )
        req.add_header("User-Agent", UA)
        for key, value in headers.items():
            req.add_header(key, value)
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode())
        except (
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
            UnicodeDecodeError,
            OSError,
        ):
            continue
        if data.get("errors"):
            continue
        posts = _parse_threads(data, username)
        if posts:
            return posts
    return []


def _parse_threads(data, username):
    posts = []

    def walk(value):
        if isinstance(value, dict):
            post = value.get("post")
            if isinstance(post, dict) and post.get("caption") is not None:
                caption = (
                    (post.get("caption") or {}).get("text", "")
                    if isinstance(post.get("caption"), dict)
                    else ""
                )
                info = post.get("text_post_app_info", {}) or {}
                images = (post.get("image_versions2") or {}).get("candidates") or []
                posts.append(
                    {
                        "account": username,
                        "text": caption[:280],
                        "likes": post.get("like_count") or 0,
                        "replies": info.get("direct_reply_count") or 0,
                        "reposts": info.get("repost_count") or 0,
                        "views": 0,
                        "media": images[0]["url"] if images else "",
                        "url": "https://www.threads.com/@%s/post/%s"
                        % (username, post.get("code", "")),
                        "createdAt": post.get("taken_at") or 0,
                    }
                )
            for nested in value.values():
                walk(nested)
        elif isinstance(value, list):
            for nested in value:
                walk(nested)

    walk(data)
    return posts


def get_threads_posts(force: bool):
    source = accounts_tool.get_source("threads")
    accounts = accounts_tool.load_accounts(source["path"], source["defaults"])

    def fetch():
        with ThreadPoolExecutor(max_workers=5) as pool:
            results = pool.map(fetch_threads_posts, accounts)
        return [post for chunk in results for post in chunk]

    posts, fetched_at = cache_tool.cached(("threads", tuple(accounts)), force, fetch)
    return posts, accounts, fetched_at
