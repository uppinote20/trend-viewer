# 050 — WP3: reels + tiktok 모듈 (diff-level plan)

## Loop-spec

- **Loop archetype**: spec-satisfaction repair
- **Trigger**: HOTL 루프 WP3 — 010 계획의 P4 (계정 기반 수집 계열)
- **Goal**: `/api/reels`, `/api/tiktok` 동등 계약 + 계정 소스 레지스트리 등록으로
  `POST /api/{reels,tiktok}/accounts` 동작 (업스트림 tiktok 404 버그의 구조적 수정 완성).
- **Non-goals**: x_twitter/threads(WP4), ai_news(WP5), frontend(WP6)
- **Verifier**: compileall + unittest + 서버 스모크 (reels는 IG 레이트리밋 가능성 —
  실패 시 픽스처 검증 + BLOCKED-외부 기록; tikwm은 낮은 동시성 유지)
- **Stop condition**: verifier 통과 (LOOP-REPAIR-01)
- **Expected terminal outcomes**: DONE / 부분 BLOCKED(외부)
- **HOTL resource bounds**: worker 1(gpt-5.5) + reviewer 1, 쓰기범위 `src/reels/`,
  `src/tiktok/`, `src/main.py`(해당 라우트 교체부만)

## 파일 변경 맵

| 파일 | 작업 | 업스트림 출처 (server.py) |
|---|---|---|
| `src/reels/reels_tool.py` | 신규 — `IG_APP_ID`:61 ("936619743392459" 바이트 보존), `DEFAULT_IG_ACCOUNTS`:63, `fetch_ig_reels`:289 (web_profile_info URL + x-ig-app-id 헤더, timeout 12, 캡션 첫줄 120자, is_video 필터), `get_reels`:318 (pool 6, views 정렬, cached 키 `("reels", tuple(accounts))`). 계정은 `accounts_tool.register_source("reels", "reels_accounts.json", DEFAULT_IG_ACCOUNTS)` + `load_accounts(source path)` 경유 | :60-66, :289-329 |
| `src/reels/test_reels_tool.py` | 신규 — 픽스처: web_profile_info 응답 → 파싱(is_video 필터, 캡션 절단, views/likes/comments/shortcode URL), 예외 → [] 폴백, get_reels 정렬+캐시 계약 | — |
| `src/reels/__init__.py` | 배럴 (`get_reels`, `register`) | — |
| `src/tiktok/tiktok_tool.py` | 신규 — `TIKWM_BASE`:89, `TIKTOK_REGION`:90, `DEFAULT_TIKTOK_ACCOUNTS`:85, `_tiktok_item`:508, `fetch_tiktok_user`:527 (count=12), `fetch_tiktok_trending`:537 (region KR count=20), `get_tiktok`:547 (**pool 3 — tikwm 무료 티어 동시성 보존**, 트렌딩+계정 병합 dedup). `register_source("tiktok", "tiktok_accounts.json", DEFAULT_TIKTOK_ACCOUNTS)` | :82-90, :508-565 |
| `src/tiktok/test_tiktok_tool.py` | 신규 — 픽스처: tikwm user/trending 응답 파싱(_tiktok_item 필드 매핑, cover 폴백), 예외 → [], dedup 로직, 캐시 계약 | — |
| `src/tiktok/__init__.py` | 배럴 (`get_tiktok`, `register`) | — |
| `src/main.py` | 수정 — 모듈 임포트 시 두 `register()` 호출(또는 임포트 부수효과 없이 main에서 명시 호출 — 명시 호출 채택), `/api/reels` 스텁 → `{"reels": reels[:80], "accounts": accounts, "fetchedAt": ...}`:696-699, `/api/tiktok` 스텁 → `{"posts": posts[:100], "accounts": accounts, "fetchedAt": ...}`:711-714. force 파싱은 WP2 패턴 재사용 | :696-699, :711-714 |

**IN**: 위 파일들. **OUT**: 그 외 (x/threads/ai 스텁 유지, `_upstream/` 불가침).

임포트 표면: `from shared import accounts_tool, cache_tool, http_tool` (모듈 스타일,
WP2 확정 패턴). reels/tiktok 모듈이 각자 `register()` 함수를 노출하고 main.py 기동부가
호출 — 등록 순서가 테스트에서 재현 가능해야 하므로 임포트 부수효과 금지.

페이징 노트 (A 감사 논블로킹 반영): WP3 이후에도 `/api/x/accounts`,
`/api/threads/accounts`는 미등록이라 404 — 의도된 상태이며 WP4에서 등록되면 200이 된다.
tiktok 캐시 키도 reels와 동일하게 `("tiktok", tuple(accounts))` 계약을 테스트로 고정한다.

## 수용 기준 (activation scenario 포함)

1. compileall + unittest 0 실패 (기존 19 + 신규).
2. `POST /api/tiktok/accounts {"action":"add","username":"@TestUser"}` → 200 +
   accounts에 "testuser" 포함 (레지스트리 등록 활성화 + 소문자 정규화 증명 —
   WP1 수용기준 7의 404가 200으로 바뀜: 업스트림 버그 수정 완성).
   remove 라운드트립 후 원상복구. config/tiktok_accounts.json 생성 확인.
3. `GET /api/reels` → 200 `{reels, accounts, fetchedAt}` (실패 시 픽스처 대체 + 기록).
4. `GET /api/tiktok` → 200 `{posts, accounts, fetchedAt}` (tikwm 실 응답 기대).
5. reels 픽스처 테스트: is_video=false 항목 제외 활성화 증명.
6. `/api/reels`,`/api/tiktok`이 STUB_PATHS에서 제거됨.
