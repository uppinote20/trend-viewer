# 070 — WP5: ai_news 모듈 (diff-level plan)

## Loop-spec

- **Loop archetype**: spec-satisfaction repair
- **Trigger**: HOTL 루프 WP5 — 010 계획의 P6
- **Goal**: `/api/ai`, `/api/oembed` 동등 계약 응답, STUB_PATHS 비움
- **Non-goals**: frontend(WP6), str_func(WP7)
- **Verifier**: compileall + unittest + 서버 스모크
- **Stop condition**: verifier 통과
- **Expected terminal outcomes**: DONE / BLOCKED(외부 RSS/HF 불가 시)
- **HOTL resource bounds**: worker 1(gpt-5.5), 쓰기범위 `src/ai_news/`, `src/main.py`

## 파일 변경 맵

| 파일 | 작업 | 업스트림 출처 (server.py) |
|---|---|---|
| `src/ai_news/ai_news_tool.py` | 신규 — `NEWS_FEEDS`:94 (구글뉴스 RSS URL 2개, `quote` 사용 보존), `HF_PIPELINES`:100 ("text-to-video","image-to-video"), `fetch_news`:568 (RSS XML 파싱 ET.fromstring, email.utils.parsedate_to_datetime, pool 2, items[:25] per feed, merged[:40]), `fetch_hf_models`:596 (HF API 호출, createdAt/trendingScore 정렬 jobs, pool 4, dedupe by id, latest[:12] trending[:12]), `get_ai_data`:627 (pool 2 submit, cache key `("ai",)`, 반환 `{news, models}`), `fetch_oembed`:638 (tiktok/youtube oEmbed 프록시, unsupported/fetch_failed 에러 형태). 임포트: `from shared import cache_tool, http_tool` + `email.utils`, `xml.etree.ElementTree` | :92-100, :568-655 |
| `src/ai_news/test_ai_news_tool.py` | 신규 — 픽스처: RSS XML fixture → fetch_news 파싱(title/source/link/ts 추출, 25개 제한, 시간순 정렬), HF API JSON fixture → fetch_hf_models (dedupe, latest/trending 분리, 12개 제한), fetch_oembed (tiktok URL → endpoint, youtube URL → endpoint, unsupported host, 예외→fetch_failed), get_ai_data 캐시 계약 | — |
| `src/ai_news/__init__.py` | 배럴 (`get_ai_data`, `fetch_oembed`) | — |
| `src/main.py` | 수정 — ai_news 임포트, `/api/ai` 스텁 → `{**data, "fetchedAt": fetched_at}`:716-718, `/api/oembed` 스텁 → `fetch_oembed(qs.get("url",[""])[0])`:720-721, STUB_PATHS 완전 비움 (상수 유지하되 빈 set), force 파싱 (/api/ai만, oembed는 캐시 없음) | :716-721 |

**IN**: 위 파일들. **OUT**: 그 외.

AI_YT_QUERIES (:93)는 이미 youtube_tool이 소유 (WP2에서 이식됨). ai_news에서는 불필요.
NEWS_FEEDS의 `quote()` 호출은 `urllib.parse.quote`로 바이트 보존.

## 수용 기준

1. compileall + unittest 0 실패 (기존 37 + 신규).
2. `GET /api/ai` → 200 `{news:[...], models:{latest:[...],trending:[...]}, fetchedAt}`.
3. `GET /api/oembed?url=https://www.tiktok.com/@x/video/1` → 200 `{ok:true/false, ...}`.
4. `GET /api/oembed?url=https://example.com/x` → 200 `{ok:false, reason:"unsupported"}`.
5. STUB_PATHS가 비어 있음 (모든 스텁 교체 완료).
6. `/api/ai?force=1` 캐시 강제 갱신 동작 (테스트 검증).
