# 010 — trend-viewer 포팅 계획

`데일리-트렌드-뷰어` 프로토타입(단일 `server.py` 781줄 + 단일 `index.html` 893줄)을
기능 단위 모듈 구조로 포팅한다. 목표는 동작을 1:1로 보존하면서 파일당 책임을 하나로
줄이는 것 — 리라이트가 아니라 **이식**이다. 외부 엔드포인트 URL, 공개 앱 ID, 요청 헤더는
바이트 단위로 보존한다(무인증 트릭이 헤더에 의존하므로). 상세 근거는
`000_upstream-analysis.md` 참조.

제약: **Python 3 표준 라이브러리만 사용.** 업스트림의 "파이썬만 있으면 더블클릭 실행"
약속을 유지한다. 프레임워크(FastAPI 등) 도입은 이 계획의 범위 밖이며 별도 승인 필요.

검증 전략: 각 페이즈마다 (1) 모듈 단위 콜로케이션 테스트(`test_*.py`, 네트워크는 캡처된
픽스처로 대체), (2) 서버 기동 후 해당 API 라우트를 업스트림 응답과 스모크 비교,
(3) 브라우저에서 해당 탭 수동 확인. 포팅 중에는 업스트림 서버(8778)와 포트를 달리해
(기본 8779) 나란히 비교한다.

---

## 페이즈 개요

| Phase | 내용 | 산출물 | 검증 |
|---|---|---|---|
| P1 | shared 기반: http 클라이언트, 캐시, 계정 저장, 이미지 프록시 | `src/shared/` 4모듈 + 테스트 | 단위 테스트 통과 |
| P2 | HTTP 서버 골격 + 라우팅 + frontend 서빙 | `src/main.py`, `src/frontend/` | 서버 기동, index 응답 |
| P3 | youtube 모듈 (InnerTube 검색, 카테고리 병합, 좋아요 보강) | `src/youtube/` | `/api/videos` 스모크 |
| P4 | reels + tiktok (계정 기반 수집 계열) | `src/reels/`, `src/tiktok/` | 각 탭 스모크 |
| P5 | x_twitter + threads (syndication / GraphQL+폴백) | `src/x_twitter/`, `src/threads/` | 각 탭 스모크 |
| P6 | ai_news (구글 뉴스 RSS + HF 모델) + oEmbed | `src/ai_news/` | AI 탭 스모크 |
| P7 | frontend 분리 (index.html → html/css/js), 통합 QA | `src/frontend/*` | 전 탭 브라우저 QA |
| P8 | str_func 문서 8종 작성, 감사(scaffold-audit), 마무리 | `devlog/str_func/*.md` | audit 통과 |

각 페이즈 완료 시 `devlog/_fin/YYMMDD_pN_이름/`으로 기록을 옮기고 str_func를 갱신한다.

## 모듈 매핑 (업스트림 → 포트)

정확한 함수 단위 매핑은 `000_upstream-analysis.md` §6이 확정한다. 개요:

| 업스트림 (server.py) | 포트 위치 |
|---|---|
| `http_get/http_json/parse_view_count/UA` | `src/shared/http_tool.py` |
| `cached/CACHE_TTL` | `src/shared/cache_tool.py` |
| `load_accounts/save_accounts/ACCOUNT_SOURCES` | `src/shared/accounts_tool.py` |
| `/api/img` 프록시 + `IMG_PROXY_ALLOW` + 메모리 캐시 | `src/shared/img_proxy_tool.py` |
| `yt_search/extract_videos/yt_like_count/enrich_likes/merge_yt_searches/get_videos/CATEGORIES` | `src/youtube/youtube_tool.py` |
| `fetch_ig_reels/get_reels/IG_APP_ID` | `src/reels/reels_tool.py` |
| `fetch_x_posts/get_x_posts/_find_timeline_entries` | `src/x_twitter/x_twitter_tool.py` |
| `fetch_threads_posts/_parse_threads/_threads_lsd_and_userid/THREADS_DOC_IDS` | `src/threads/threads_tool.py` |
| `fetch_tiktok_user/fetch_tiktok_trending/_tiktok_item/get_tiktok` | `src/tiktok/tiktok_tool.py` |
| `fetch_news/fetch_hf_models/get_ai_data/fetch_oembed` | `src/ai_news/ai_news_tool.py` |
| `Handler` 클래스 + 라우팅 | `src/main.py` (라우팅 테이블) + 각 모듈의 route 함수 |
| `index.html` | `src/frontend/` (P7에서 분리) |

설정값(`PORT`, `CACHE_TTL` 등)은 `config/` + 환경변수(`TREND_VIEWER_*`)로 외부화한다.
계정 JSON 파일은 `config/`에 저장한다(업스트림은 서버 옆에 저장 — 위치만 변경, 포맷 유지).

## 리스크

- **Threads doc_id 로테이션**: 업스트림도 폴백 설계. 폴백 경로를 1급 동작으로 포팅.
- **tikwm 무료 티어**: 낮은 동시성(3) + 1시간 캐시 정책을 그대로 유지.
- **IG/CDN 핫링크**: `IMG_PROXY_ALLOW` 허용 목록과 프록시 경유를 정확히 보존.
- **InnerTube 응답 구조 변화**: `extract_videos`의 방어적 순회 로직을 단순화하지 말 것.
- **테스트의 네트워크 의존**: 실 네트워크 테스트는 스모크로 한정, 단위 테스트는 픽스처 기반.

## 업스트림 알려진 버그 (포팅 시 수정)

- **틱톡 계정 관리 404**: 프론트는 `POST /api/tiktok/accounts`를 호출하지만
  (`_upstream/index.html:816`) 서버 `do_POST` 정규식은 `reels|x|threads`만 허용한다
  (`_upstream/server.py:753`). `ACCOUNT_SOURCES` 딕셔너리에는 tiktok이 이미 있으므로
  (`_upstream/server.py:285`) 정규식에 `tiktok`만 추가하면 된다 — P4에서 처리.

## Decisions

- 폴더명 snake_case (Python 패키지 임포트 제약; Lidge kebab-case 규칙의 언어별 예외).
- stdlib-only 유지. `http.server` 기반 골격 유지하되 라우팅 테이블만 선언적으로 정리.
- 포팅 중 기본 포트 8779 (업스트림 8778과 병행 비교), 완료 후 8778 복귀.
