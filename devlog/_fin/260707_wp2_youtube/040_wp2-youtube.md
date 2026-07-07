# 040 — WP2: youtube 모듈 (diff-level plan)

## Loop-spec

- **Loop archetype**: spec-satisfaction repair
- **Trigger**: HOTL 루프 WP2 — 010 계획의 P3
- **Goal**: `/api/videos`가 업스트림과 동등 계약으로 응답 (카테고리/기간/쇼츠/검색/
  좋아요 보강), 카테고리 상수가 youtube 모듈로 이동.
- **Non-goals**: 다른 플랫폼 모듈, frontend, AI 탭(`AI_YT_QUERIES`는 youtube가 아니라
  AI 카테고리 검색어이므로 여기서 함께 이식하되 소유는 youtube — 업스트림도 유튜브
  검색에 사용, server.py:93)
- **Verifier**: compileall + unittest (픽스처 기반) + 서버 기동 후
  `/api/videos?category=AI&period=day` 실 스모크 (외부 API 막히면 픽스처 검증으로
  대체하고 BLOCKED-외부 사유 기록)
- **Stop condition**: verifier 통과 (LOOP-REPAIR-01 준수)
- **Memory artifact**: 본 문서 + goalplan ledger (wp2)
- **Expected terminal outcomes**: DONE / BLOCKED(외부 InnerTube 응답 불가 시 스모크만)
- **Escalation**: stdlib 밖 의존 필요 시 UNSAFE
- **HOTL resource bounds**: worker 1(gpt-5.5) + reviewer 1, 쓰기범위 `src/youtube/`
  + `src/main.py`(라우트 교체부만)

## 파일 변경 맵

| 파일 | 작업 | 업스트림 출처 (server.py) |
|---|---|---|
| `src/youtube/youtube_tool.py` | 신규 — `CATEGORIES`:35, `ALL_MERGE`:47, `PERIOD_CODE`:50, `PERIOD_EXCLUDE`:54, `AI_YT_QUERIES`:93, `within_period`:107, `build_search_params`:113, `extract_videos`:158, `yt_search`:183, `yt_like_count`:207, `enrich_likes`:221 (ThreadPoolExecutor 12), `merge_yt_searches`:233 (pool 6), `get_videos`:246. **임포트 표면 확정**: `from shared import cache_tool, http_tool` 후 `http_tool.parse_view_count`(extract_videos 내 사용 :170), `http_tool.http_json`(yt_search :194), `http_tool.http_get`(yt_like_count :213), `cache_tool.cached`(get_videos :260) — shared 배럴은 모듈만 export하므로 함수 직접 임포트 금지 | :33-58, :92-93, :107-119, :156-261 |
| `src/youtube/test_youtube_tool.py` | 신규 — 픽스처 기반: extract_videos(중첩 videoRenderer 트리), within_period 기간별, build_search_params base64 값(업스트림 함수 출력과 동일성), yt_search 페이로드 구성(clientVersion "2.20250624.01.00" 바이트 보존, urlopen 목킹), yt_like_count 정규식(한/영), get_videos 쿼리 선택 로직(전체=ALL_MERGE, AI=AI_YT_QUERIES, 검색어 우선) | — |
| `src/youtube/__init__.py` | 배럴 export (`get_videos`, `CATEGORIES`) | — |
| `src/main.py` | 수정 — `/api/videos` 스텁 제거 → youtube 위임 핸들러 (:672,:679-691 포팅: **`force = qs.get("force",["0"])[0] == "1"` 핸들러 내 파싱 필수** — WP1 라우팅은 qs만 전달, 업스트림은 do_GET 상단 :672에서 공통 파싱), category/period/shorts/enrich/q 파싱, unknown category 400 (`if not query and category not in ("전체","AI") and category not in CATEGORIES` :685 그대로), `{"videos": videos[:60], "fetchedAt": fetched_at}` :689, `/api/categories`를 youtube.CATEGORIES 기반으로 교체(placeholder 상수 삭제, TODO(WP2) 해소) | :672, :679-694 |

**IN**: 위 4파일. **OUT**: 그 외 전부 (`_upstream/` 불가침).

## 수용 기준 (activation scenario 포함)

1. compileall + unittest 0 실패 (WP1 13개 + WP2 신규 테스트).
2. `curl ":8779/api/videos?category=없는카테고리&period=day"` → 400 unknown category
   (가드 활성화 증명).
3. `curl ":8779/api/videos?category=AI&period=day"` → 200 + `{videos:[...60↓], fetchedAt}`
   구조. 실 네트워크 가능 시 videos 비어있지 않음 확인, 불가 시 픽스처 테스트로 대체.
4. `curl :8779/api/categories` → WP1과 동일 JSON (youtube 소유로 이동 후에도 무변화).
5. main.py의 placeholder CATEGORIES 상수가 삭제됨 (`grep -n "TODO(WP2)" src/main.py` 공출력).
6. **force 캐시 계약**: 단위 테스트로 get_videos가 force=False 재호출 시 fetch 함수를
   다시 부르지 않고(fetchedAt 동일), force=True 시 재호출함을 증명 (cached 활성화
   시나리오 — C-ACTIVATION-GROUNDING-01). 핸들러 레벨 force=1 파싱도 테스트.

## A 감사 synthesis (1차 FAIL → 반영)

블로커 3건 수용: (1) force 파라미터 누락 → 핸들러 내 파싱 명시 + 수용기준 6 추가.
(2) shared 의존 임포트 표면 미명시 → `from shared import cache_tool, http_tool` 모듈
임포트로 확정. (3) force 없이는 get_videos 시그니처 동등 호출 불가 → (1)로 해소.
기각: 없음. 라우트 인용도 :672 포함으로 수정.

2차 재검증에서 함수별 사용처 인용 오기 지적 → :170(parse_view_count), :194(http_json),
:213(http_get), :260(cached)으로 정정.
