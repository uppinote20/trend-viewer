# 060 — WP4: x_twitter + threads 모듈 (diff-level plan)

## Loop-spec

- **Loop archetype**: spec-satisfaction repair
- **Trigger**: HOTL 루프 WP4 — 010 계획의 P5
- **Goal**: `/api/x`, `/api/threads` 동등 계약 + x/threads 계정 소스 레지스트리 등록
- **Non-goals**: 다른 플랫폼 모듈, frontend, ai_news
- **Verifier**: compileall + unittest + 서버 스모크 (x syndication은 빈 응답 가능, threads
  doc_id 실패 가능 — 둘 다 픽스처 테스트로 보완, 실 API 실패 시 BLOCKED 기록)
- **Stop condition**: verifier 통과
- **Expected terminal outcomes**: DONE / 부분 BLOCKED(외부)
- **HOTL resource bounds**: worker 1(gpt-5.5) + reviewer 1, 쓰기범위 `src/x_twitter/`,
  `src/threads/`, `src/main.py`(해당 라우트 교체부만)

## 파일 변경 맵

| 파일 | 작업 | 업스트림 출처 (server.py) |
|---|---|---|
| `src/x_twitter/x_twitter_tool.py` | 신규 — `DEFAULT_X_ACCOUNTS`:70 (대소문자 보존 리스트 — preserve_case=True), `_find_timeline_entries`:332 (재귀 트리 순회, timeline.entries 검색), `fetch_x_posts`:350 (syndication URL, Accept:text/html 헤더, __NEXT_DATA__ JSON 파싱, tweetResult/result 폴백 :367-369, 미디어 첫 URL, views dict→int 변환 :385-386), `get_x_posts`:393 (pool 3, cache key `("x", tuple(accounts))`). 임포트: `from shared import accounts_tool, cache_tool, http_tool` | :68-73, :332-399 |
| `src/x_twitter/test_x_twitter_tool.py` | 신규 — 픽스처: _find_timeline_entries (중첩 dict에서 timeline.entries 발견/미발견), fetch_x_posts HTML fixture (__NEXT_DATA__ 포함 mock → 파싱 결과 검증: account, text, likes, replies, retweets, views, media, url 필드), tweetResult 폴백 경로, 예외→[] 폴백, 캐시 계약 | — |
| `src/x_twitter/__init__.py` | 배럴 (`get_x_posts`, `register`) | — |
| `src/threads/threads_tool.py` | 신규 — `IG_APP_ID_THREADS`:80 ("238260118697367"), `DEFAULT_THREADS_ACCOUNTS`:77, `THREADS_DOC_IDS`:427 (5개 후보 리스트 바이트 보존), `_threads_lsd_and_userid`:406 (LSD 정규식, IG web_profile_info로 user_id 조회), `fetch_threads_posts`:433 (doc_id 순회, GraphQL x-www-form-urlencoded POST, 에러시 다음 doc_id), `_parse_threads`:466 (재귀 순회, caption.text[:280], like_count/direct_reply_count/repost_count, image_versions2.candidates), `get_threads_posts`:496 (pool 5, cache key `("threads", tuple(accounts))`). 임포트: `from shared import accounts_tool, cache_tool, http_tool` + `urllib.request` (GraphQL POST 직접 구성 — http_tool.http_get은 JSON payload용이므로
urlencode 본문에는 부적합, 업스트림도 직접 구성 :446-454). **UA 헤더 필수**:
http_tool.http_get을 우회하므로 `req.add_header("User-Agent", settings.UA)` 를
직접 추가해야 한다 (업스트림 :450-451 참조, 누락 시 403/빈 응답 위험) | :75-81, :406-505 |
| `src/threads/test_threads_tool.py` | 신규 — 픽스처: _parse_threads (중첩 post 구조 파싱, caption 절단 280자, image URL 추출), _threads_lsd_and_userid 정규식(LSD 토큰 추출 mock HTML), doc_id 순회 로직(첫 번째 성공 시 중단, 전부 errors 시 []), 예외→[], 캐시 계약 | — |
| `src/threads/__init__.py` | 배럴 (`get_threads_posts`, `register`) | — |
| `src/main.py` | 수정 — x_twitter/threads 임포트 + register() 호출, `/api/x` 스텁 → `{"posts": posts, "accounts": accounts, "fetchedAt": ...}`:701-703 (슬라이스 없음!), `/api/threads` 스텁 → `{"posts": posts, "accounts": accounts, "fetchedAt": ...}`:706-708 (역시 슬라이스 없음), STUB_PATHS에서 제거, force 파싱 WP2 패턴 재사용 | :701-708 |

**IN**: 위 파일들. **OUT**: 그 외 (`_upstream/` 불가침).

임포트 표면: WP2/WP3 패턴 동일 (`from shared import ...` 모듈 스타일).
x_twitter register에서 `preserve_case=True` (업스트림 :769: `raw if source == "x" else raw.lower()` — 현재 accounts_tool이 이미 지원).
threads는 **두 앱 ID를 모두 사용**: `_threads_lsd_and_userid`에서 user_id 조회 시
릴스와 동일한 `IG_APP_ID` (:61 "936619743392459", web_profile_info 호출 :417)를 쓰고,
GraphQL POST 시에는 자체 `IG_APP_ID_THREADS` (:80 "238260118697367", :439)를 쓴다.
threads_tool은 reels_tool에서 `IG_APP_ID`를 임포트하거나 동일 상수를 복제해야 한다
(reels_tool.IG_APP_ID 임포트 채택 — 단일 소스).

## 수용 기준

1. compileall + unittest 0 실패 (기존 27 + 신규).
2. `POST /api/x/accounts {"action":"add","username":"test"}` → 200 + accounts에
   "test" (소문자 아닌 원본 보존 확인) → remove 후 복구.
3. `POST /api/threads/accounts {"action":"add","username":"@Test"}` → 200 + "test"
   (소문자 정규화 확인).
4. `GET /api/x` → 200 `{posts, accounts, fetchedAt}` (syndication 빈 응답 가능
   — 빈 posts 배열도 수용, 구조만 확인).
5. `GET /api/threads` → 200 `{posts, accounts, fetchedAt}` (doc_id 전부 실패 가능
   — 빈 posts 수용, 구조만 확인; 폴백 동작은 프론트가 처리, 서버는 빈 배열).
6. `/api/x`, `/api/threads`가 STUB_PATHS에서 제거됨.
7. 응답에 슬라이스 없음 (x와 threads는 업스트림도 전체 반환).

## A 감사 synthesis (1차 FAIL → 반영)

블로커 2건 수용: (1) threads 앱 ID 이중 사용 미명시 → _threads_lsd_and_userid는
릴스와 동일한 IG_APP_ID(:61)로 user_id를 조회하고, GraphQL에만 IG_APP_ID_THREADS(:80)
사용함을 명시. reels_tool에서 임포트 채택. (2) 직접 urllib POST에서 UA 헤더 누락 위험
→ settings.UA를 req.add_header로 직접 추가 필수 명시 (업스트림 :450-451). 기각: 없음.
