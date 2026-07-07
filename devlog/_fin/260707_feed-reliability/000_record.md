# Feed reliability record

2026-07-07 작업 기록.

### src/shared/cache_tool.py — 음수 결과 TTL 분리
- **Changes**: `cached()`가 기존 `(result, fetched_at)` 반환 형태를 유지하면서 항목별 TTL을 저장하도록 `ttl` 선택자를 받게 했다. 기존 2튜플 캐시 항목도 읽을 수 있게 `_entry_ttl()`로 호환 처리했다 (`src/shared/cache_tool.py:13`, `src/shared/cache_tool.py:17`, `src/shared/cache_tool.py:33`).
- **Impact**: X, Reels, Threads가 “결과 0개 + 오류 1개 이상”일 때 120초 TTL을 저장하고, 정상/빈 성공은 기존 3600초 TTL을 유지한다.
- **Verification**: `python3 -m unittest discover -s src -p 'test_*.py'` → 66 tests OK.

### src/x_twitter/x_twitter_tool.py — 계정별 오류 계약
- **Changes**: `fetch_x_posts()`가 더 이상 실패를 빈 배열로 숨기지 않고 `(items, error)`를 반환한다. HTTPError는 `kind=http` 및 실제 status code, Timeout은 `kind=timeout`, JSON/HTML 파싱 실패는 `kind=parse`로 매핑했다 (`src/x_twitter/x_twitter_tool.py:52`, `src/x_twitter/x_twitter_tool.py:64`, `src/x_twitter/x_twitter_tool.py:71`).
- **Impact**: `get_x_posts()`는 계정별 결과를 `(posts, errors)`로 합산하고, 음수 오류 결과는 120초로 캐시한다 (`src/x_twitter/x_twitter_tool.py:117`, `src/x_twitter/x_twitter_tool.py:128`, `src/x_twitter/x_twitter_tool.py:132`).
- **Verification**: `python3 -m unittest discover -s src -p 'test_*.py'` → 66 tests OK.

### src/reels/reels_tool.py — Reels 오류 합산
- **Changes**: Instagram web_profile_info 호출 실패를 `http`, `timeout`, `parse` 오류 객체로 보존하고 `(items, error)`를 반환한다 (`src/reels/reels_tool.py:30`, `src/reels/reels_tool.py:37`, `src/reels/reels_tool.py:44`).
- **Impact**: `get_reels()`는 기존 view 정렬을 유지하면서 errors를 함께 캐시하고, 음수 오류 TTL은 120초로 낮춘다 (`src/reels/reels_tool.py:76`, `src/reels/reels_tool.py:88`, `src/reels/reels_tool.py:92`).
- **Verification**: `python3 -m unittest discover -s src -p 'test_*.py'` → 66 tests OK.

### src/threads/threads_tool.py — Threads 단계별 오류 보존
- **Changes**: LSD 페이지, Instagram user_id 조회, Threads GraphQL doc_id 루프의 실패를 가능한 실제 `kind/code`로 남긴다. 특히 user_id HTTP 401 같은 오류는 `kind=http`, `code=401`로 전파된다 (`src/threads/threads_tool.py:39`, `src/threads/threads_tool.py:74`, `src/threads/threads_tool.py:123`).
- **Impact**: `fetch_threads_posts()`는 missing LSD/user_id나 모든 doc_id 실패를 빈 성공으로 숨기지 않고 오류로 반환한다. `get_threads_posts()`는 posts/errors를 합산하고 음수 오류 TTL 120초를 적용한다 (`src/threads/threads_tool.py:88`, `src/threads/threads_tool.py:191`, `src/threads/threads_tool.py:202`).
- **Verification**: `python3 -m unittest discover -s src -p 'test_*.py'` → 66 tests OK.

### src/main.py — 고정 API 계약 추가
- **Changes**: `/api/x`, `/api/reels`, `/api/threads`에 additive 필드 `status`, `errors`, effective `cacheTtl`을 추가했다. 상태 계산은 `ok`, `empty`, `error`, `partial` 네 값만 반환한다 (`src/main.py:28`, `src/main.py:80`, `src/main.py:90`, `src/main.py:95`).
- **Impact**: 기존 `posts`/`reels`, `accounts`, `fetchedAt` 필드는 유지된다. 프론트엔드가 일부 계정 실패와 전체 실패를 구분할 수 있다.
- **Verification**: `python3 -m unittest discover -s src -p 'test_*.py'` → 66 tests OK.

### X 429 진단
- **Current code**: `http_tool.http_get()`는 공통 Chrome UA를 넣고, X fetcher는 기존 upstream 보존 헤더인 `Accept: text/html`만 추가한다 (`src/shared/http_tool.py:9`, `src/x_twitter/x_twitter_tool.py:58`).
- **Live test**: 한 계정 `OpenAI` 기준으로 `current_python`, `curl_like`, `chrome_accept_any`, `chrome_accept_lang`, `chrome_accept_any_lang` Python urllib 요청은 모두 HTTP 429 `Rate limit exceeded`를 받았다.
- **Cookie test**: curl이 받은 `__cf_bm` 쿠키를 Python urllib 요청에 넣어도 HTTP 429가 유지됐다.
- **curl comparison**: 같은 URL에서 `curl` 기본 요청은 HTTP/2 200, `curl --http1.1`도 200과 `__NEXT_DATA__` HTML을 받았다.
- **Decision**: 성공하는 최소 header delta가 없었다. 따라서 X 요청 헤더는 변경하지 않았다. 현재 환경에서는 urllib/TLS 또는 클라이언트 fingerprint 차이로 추정되며, 앱은 새 오류 계약으로 계정별 `{"kind":"http","code":429}`를 사용자에게 노출한다.
