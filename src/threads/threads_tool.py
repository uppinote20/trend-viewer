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


NEGATIVE_CACHE_TTL = 120
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
    lsd_error = None
    try:
        _, body = http_tool.http_get(
            "https://www.threads.com/@" + quote(username), timeout=12
        )
        match = re.search(
            r'"LSD",\[\],\{"token":"([^"]+)"', body.decode("utf-8", "ignore")
        )
        lsd = match.group(1) if match else None
        if not lsd:
            lsd_error = {"account": username, "kind": "parse", "code": None}
    except urllib.error.HTTPError as exc:
        lsd_error = {"account": username, "kind": "http", "code": exc.code}
    except TimeoutError:
        lsd_error = {"account": username, "kind": "timeout", "code": None}
    except urllib.error.URLError as exc:
        kind = "timeout" if isinstance(exc.reason, TimeoutError) else "http"
        lsd_error = {"account": username, "kind": kind, "code": None}
    except OSError:
        lsd_error = {"account": username, "kind": "http", "code": None}

    user_id = None
    user_id_error = None
    try:
        info = http_tool.http_json(
            "https://www.instagram.com/api/v1/users/web_profile_info/?username="
            + quote(username),
            headers={"x-ig-app-id": IG_APP_ID},
            timeout=12,
        )
        user_id = ((info.get("data") or {}).get("user") or {}).get("id")
        if not user_id:
            user_id_error = {"account": username, "kind": "parse", "code": None}
    except urllib.error.HTTPError as exc:
        user_id_error = {"account": username, "kind": "http", "code": exc.code}
    except TimeoutError:
        user_id_error = {"account": username, "kind": "timeout", "code": None}
    except urllib.error.URLError as exc:
        kind = "timeout" if isinstance(exc.reason, TimeoutError) else "http"
        user_id_error = {"account": username, "kind": kind, "code": None}
    except (json.JSONDecodeError, UnicodeDecodeError):
        user_id_error = {"account": username, "kind": "parse", "code": None}
    except OSError:
        user_id_error = {"account": username, "kind": "http", "code": None}
    return lsd, user_id, lsd_error, user_id_error


def fetch_threads_posts(username: str):
    lsd, user_id, lsd_error, user_id_error = _threads_lsd_and_userid(username)
    if not lsd or not user_id:
        return [], user_id_error or lsd_error or {"account": username, "kind": "parse", "code": None}

    headers = {
        "X-FB-LSD": lsd,
        "X-IG-App-ID": IG_APP_ID_THREADS,
        "Sec-Fetch-Site": "same-origin",
        "X-FB-Friendly-Name": "BarcelonaProfileThreadsTabQuery",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    last_error = None
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
        except urllib.error.HTTPError as exc:
            last_error = {"account": username, "kind": "http", "code": exc.code}
            continue
        except TimeoutError:
            last_error = {"account": username, "kind": "timeout", "code": None}
            continue
        except urllib.error.URLError as exc:
            kind = "timeout" if isinstance(exc.reason, TimeoutError) else "http"
            last_error = {"account": username, "kind": kind, "code": None}
            continue
        except (json.JSONDecodeError, UnicodeDecodeError):
            last_error = {"account": username, "kind": "parse", "code": None}
            continue
        except OSError:
            last_error = {"account": username, "kind": "http", "code": None}
            continue
        if data.get("errors"):
            last_error = {"account": username, "kind": "parse", "code": None}
            continue
        posts = _parse_threads(data, username)
        if posts:
            return posts, None
    return [], last_error or {"account": username, "kind": "parse", "code": None}


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
    cache_key = ("threads", tuple(accounts))

    def fetch():
        with ThreadPoolExecutor(max_workers=5) as pool:
            results = pool.map(fetch_threads_posts, accounts)
        posts = []
        errors = []
        for items, error in results:
            posts.extend(items)
            if error:
                errors.append(error)
        return posts, errors

    def ttl_for_outcome(outcome):
        posts, errors = outcome
        return NEGATIVE_CACHE_TTL if not posts and errors else None

    (posts, errors), fetched_at = cache_tool.cached(cache_key, force, fetch, ttl=ttl_for_outcome)
    return posts, accounts, fetched_at, errors, cache_tool.ttl_for(cache_key)
