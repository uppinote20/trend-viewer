# WP1 Shared Server Evidence

Recorded: 2026-07-07 05:00:52 KST

## Judgement

PASS. Fresh compileall, unittest, local server smoke checks, status-code checks, and `_upstream/index.html` byte diff passed for WP1.

## Command Output

### python3 -m compileall src

Exit code: 0

```text
Listing 'src'...
Listing 'src/ai_news'...
Compiling 'src/ai_news/__init__.py'...
Listing 'src/frontend'...
Compiling 'src/frontend/__init__.py'...
Compiling 'src/main.py'...
Listing 'src/reels'...
Compiling 'src/reels/__init__.py'...
Compiling 'src/settings.py'...
Listing 'src/shared'...
Compiling 'src/shared/__init__.py'...
Compiling 'src/shared/accounts_tool.py'...
Compiling 'src/shared/cache_tool.py'...
Compiling 'src/shared/http_tool.py'...
Compiling 'src/shared/img_proxy_tool.py'...
Compiling 'src/shared/test_accounts_tool.py'...
Compiling 'src/shared/test_cache_tool.py'...
Compiling 'src/shared/test_http_tool.py'...
Compiling 'src/shared/test_img_proxy_tool.py'...
Listing 'src/threads'...
Compiling 'src/threads/__init__.py'...
Listing 'src/tiktok'...
Compiling 'src/tiktok/__init__.py'...
Listing 'src/x_twitter'...
Compiling 'src/x_twitter/__init__.py'...
Listing 'src/youtube'...
Compiling 'src/youtube/__init__.py'...
```

### python3 -m unittest discover -s src -p "test_*.py" -t src

Exit code: 0

```text
.............
----------------------------------------------------------------------
Ran 13 tests in 0.004s

OK
```

### python3 src/main.py

Server started successfully.

```text
트렌드 뷰어 실행 중: http://localhost:8779
```

### curl -sI localhost:8779/

Exit code: 0

```text
HTTP/1.0 200 OK
Server: BaseHTTP/0.6 Python/3.13.7
Date: Mon, 06 Jul 2026 20:00:52 GMT
Content-Type: text/html; charset=utf-8
Content-Length: 45700
Cache-Control: no-store
```

### curl -s -w '\nHTTP %{http_code}\n' "localhost:8779/api/img?u=http://evil.example/x.jpg"

Exit code: 0

```text
{"error": "host not allowed"}
HTTP 400
```

### curl -s -w '\nHTTP %{http_code}\n' localhost:8779/api/videos

Exit code: 0

```text
{"error": "not implemented"}
HTTP 501
```

### curl -s localhost:8779/api/categories

Exit code: 0

```text
{"categories": ["전체", "AI", "먹방", "뷰티/패션", "브이로그", "예능/코미디", "영화/드라마", "테크/IT", "지식/교육", "여행", "동물"]}
```

### curl -s -w '\nHTTP %{http_code}\n' -X POST localhost:8779/api/tiktok/accounts -d '{"action":"add","username":"t"}'

Exit code: 0

```text
{"error": "not found"}
HTTP 404
```

### diff <(curl -s localhost:8779/) _upstream/index.html

Exit code: 0

```text

```

### Server stop

Stopped with Ctrl-C after smoke checks.

```text
[05:00:52] "HEAD / HTTP/1.1" 200 -
[05:00:52] "GET /api/img?u=http://evil.example/x.jpg HTTP/1.1" 400 -
[05:00:52] "GET /api/videos HTTP/1.1" 501 -
[05:00:53] "GET /api/categories HTTP/1.1" 200 -
[05:00:53] "GET / HTTP/1.1" 200 -
[05:00:53] "POST /api/tiktok/accounts HTTP/1.1" 404 -
```
