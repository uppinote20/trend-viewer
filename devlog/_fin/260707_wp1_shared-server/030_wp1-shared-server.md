# 030 — WP1: shared 기반 + 서버 골격 (diff-level plan)

## Loop-spec

- **Loop archetype**: spec-satisfaction repair (verifier가 done을 정의)
- **Trigger**: HOTL 루프 WP1 — 010 계획의 P1+P2
- **Goal**: `python3 src/main.py`로 서버가 뜨고, `/`가 업스트림 index.html을 서빙하며,
  shared 4모듈이 픽스처 기반 단위 테스트를 통과한다.
- **Non-goals**: 플랫폼 모듈(youtube 등) 포팅, frontend 분리, 디자인 교정 (WP2-WP6)
- **Verifier**: `python3 -m compileall src` + `python3 -m unittest discover -s src -p "test_*.py"`
  + 기동 후 `curl -sI localhost:8779/` 200 + `curl -s localhost:8779/api/categories`
- **Stop condition**: verifier 전부 통과 (LOOP-REPAIR-01: 같은 실패 2회 → RCA 모드)
- **Memory artifact**: 본 문서 + goalplan ledger (`trend-viewer-hotl-*`)
- **Expected terminal outcomes**: DONE (verifier 통과) / BLOCKED (없음 — 네트워크 불요)
- **Escalation**: stdlib 밖 의존 필요 발견 시 UNSAFE 중단
- **HOTL resource bounds**: worker 서브에이전트 1개(gpt-5.5), 쓰기범위 `src/shared/`,
  `src/main.py`, `config/settings.py`, 리뷰어 1개(read-only)

## 파일 변경 맵

| 파일 | 작업 | 업스트림 출처 (server.py) |
|---|---|---|
| `src/settings.py` | 신규 — PORT(8779, env `TREND_VIEWER_PORT`), CACHE_TTL(env), BASE_DIR, CONFIG_DIR(계정 JSON 저장 위치=`config/`), UA:23, IMG_CACHE_MAX:31, IMG_PROXY_ALLOW:102 | :20-31, :101-104 |
| `src/shared/http_tool.py` | 신규 — `http_get`:122, `http_json`:134, `parse_view_count`:139 | :122-141 |
| `src/shared/test_http_tool.py` | 신규 — parse_view_count 케이스, http_get 헤더 구성(urlopen 목킹) | — |
| `src/shared/cache_tool.py` | 신규 — `cached`:144 + `_cache`/lock, TTL은 settings 주입 | :26-29, :144-155 |
| `src/shared/test_cache_tool.py` | 신규 — TTL 만료/force/히트 시나리오 | — |
| `src/shared/accounts_tool.py` | 신규 — `load_accounts`:264, `save_accounts`:275, **소스 레지스트리** `register_source(name, filename, defaults)` / `get_source(name)` / `update_accounts(name, action, username)` (업스트림 `ACCOUNT_SOURCES`:281 + do_POST 본문 :757-773 의 범용화; X만 대소문자 보존 규칙 포함). 저장 경로는 `settings.CONFIG_DIR` | :62-90, :264-287, :750-775 |
| `src/shared/test_accounts_tool.py` | 신규 — tmpdir 라운드트립, 손상 JSON 폴백, 레지스트리 add/remove, 미등록 소스 거부, X 대소문자 보존 | — |
| `src/shared/img_proxy_tool.py` | 신규 — `/api/img` 핸들러 로직 추출. **`_img_cache`/`_img_lock` 모듈 전역 상태를 이 모듈이 소유** (업스트림 :29-31과 동일한 락 문법: 락 밖 읽기, clear/쓰기만 락 — ThreadingHTTPServer 하 동시성 보존). allowlist 검사, 상한 600, 502 폴백 | :29-31, :102-104, :725-748 |
| `src/shared/test_img_proxy_tool.py` | 신규 — allowlist 거부(http://, 비허용 호스트), 캐시 히트, 상한 초과 클리어 | — |
| `src/shared/__init__.py` | 배럴 export | — |
| `src/main.py` | 신규 — ThreadingHTTPServer + Handler 골격(`_send`:660, `/`:674, `/api/img`:725, `/api/categories`:692, 404), GET 라우팅 테이블 dict. **do_POST도 WP1 범위**: `^/api/([a-z_]+)/accounts$` 매치 후 `accounts_tool` 레지스트리에 위임 — 등록된 소스만 허용, 미등록은 404. 플랫폼 WP는 레지스트리 등록만 하면 되고 main.py 재수정 불필요 (업스트림 tiktok 404 버그의 구조적 수정) | :656-781 |

**IN**: 위 파일들. **OUT**: `src/{youtube,reels,x_twitter,threads,tiktok,ai_news}/`(스텁 배럴만 이미 존재), `_upstream/` 일체, frontend 분리.

임포트 경로 결정: `python3 src/main.py` 실행 시 `sys.path[0]=src/`이므로 settings는
`src/settings.py`에 둔다 (`import settings`, `from shared import ...` 둘 다 동작).
`config/`는 코드가 아니라 **계정 JSON 데이터 디렉토리**로만 쓴다.
기본 계정 상수(DEFAULT_*, :63-88)는 각 플랫폼 모듈 소유 — 플랫폼 WP가
`register_source()`를 호출해 레지스트리에 등록한다. POST 핸들러 자체는 WP1이 완성한다.

## A 감사 synthesis (1차 FAIL → 반영)

리뷰어 블로커 3건 전부 수용: (1) `config/settings.py` 임포트 불가
(ModuleNotFoundError 재현) → `src/settings.py`로 이동. (2) POST 계정 라우트 소유권
모호 → WP1이 범용 POST 핸들러+레지스트리를 완성하는 것으로 확정 (tiktok 404 버그의
구조적 수정). (3) `_img_cache`/`_img_lock` 소유권 미명시 → `img_proxy_tool` 소유로
명시, 업스트림 락 문법 보존. 기각한 블로커: 없음.

## 수용 기준 (activation scenario 포함)

1. compileall + unittest 0 실패 (명령 출력 캡처).
2. `python3 src/main.py` 기동 → `curl -sI :8779/` = `200` + `text/html`.
3. `curl -s ":8779/api/img?u=http://evil.example/x.jpg"` → 400 `host not allowed`
   (allowlist 가드 활성화 증명 — C-ACTIVATION-GROUNDING-01).
4. `curl -s :8779/api/videos` → 501 스텁 응답 (라우팅 테이블 동작 증명).
5. `curl -s :8779/api/categories` → 업스트림과 동일 JSON.
6. index.html은 이번 페이즈에서는 `_upstream/index.html`을 그대로 서빙 (WP6에서 교체).
   업스트림과 동일 바이트 응답 확인 (`diff <(curl -s :8779/) _upstream/index.html`).
7. `curl -s -X POST :8779/api/tiktok/accounts -d '{"action":"add","username":"test"}'`
   → 404 (미등록 소스 거부 — WP3에서 등록 후 200으로 바뀌는 것이 WP3 수용 기준).
   등록 경로 활성화 증명은 테스트에서 임시 소스 등록으로 수행.
