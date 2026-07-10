---
created: 2026-07-10
tags: [trend-viewer, analysis-engine, LLM-synthesis, frontend-QA, date-radar]
aliases: [분석 엔진 완료 기록, WP1-WP4 완료, analysis engine record]
---

# 260710 analysis-engine

## Summary

WP1-WP4를 통해 날짜 레이더 기반을 안정화하고, trend-viewer를 7개 채널의 흐름을
서로 연결해 읽는 분석 도구로 확장했다. WP1은 PR #2의 date radar를 병합한 뒤
국가별 질의, 소스별 순위 교차 배치, 실패 결과 단기 캐시를 보강했다. WP2는 stdlib
SSE 클라이언트와 휴리스틱 상관·속도 분석 package를 만들었다. WP3는 근거 ID로
제한한 LLM 합성과 `/api/analysis`를 추가했다. WP4는 분석 탭과 홈 비동기 분석
섹션을 기존 단일 파일 프론트엔드에 연결했다.

## Changes

- `src/date/date_tool.py`, `src/date/test_date_tool.py`: PR #2 구현을 국가별 5개 질의, KR Trends 선택 수집, 소스별 정렬·1:1 교차 배치, 120초 negative TTL로 강화했다.
- `src/shared/cache_tool.py`, `src/shared/test_cache_tool.py`: 결과별 callable TTL과 같은 tick의 cache timestamp 안정성을 보강했다.
- `src/analysis/llm_client_tool.py`, `src/analysis/test_llm_client_tool.py`: Python 표준 라이브러리 기반 Responses SSE client와 inactivity·total deadline을 추가했다.
- `src/analysis/keyword_tool.py`, `src/analysis/test_keyword_tool.py`: NFKC·casefold 정규화와 한글·ASCII·Kana/Han token matching을 추가했다.
- `src/analysis/aggregate_tool.py`, `src/analysis/test_aggregate_tool.py`: 7채널 병렬 snapshot, anchor correlation, history, velocity, 휴리스틱 briefing을 추가했다.
- `src/analysis/synthesis_tool.py`, `src/analysis/test_synthesis_tool.py`: evidence ID grounding, JSON·schema validation, UTF-8 정제, 휴리스틱 fallback, 1800/300초 TTL을 추가했다.
- `src/main.py`, `src/test_main_api_cache_metadata.py`: 국가·force를 받는 `/api/date`, `/api/analysis`와 entry별 cache metadata 전달을 고정했다.
- `src/frontend/index.html`: 분석·데이트 탭, 분석 cluster 카드, LLM 상태, 홈 비동기 분석, 국가 invalidation, 데스크톱·모바일 반응형 UI를 추가했다.
- `devlog/str_func/analysis.md`, `devlog/str_func/date.md`, `devlog/str_func/frontend.md`: 현재 모듈과 화면 계약을 문서화했다.
- `README.md`, `.env.example`, `AGENTS.md`, `docs/screenshot-analysis-desktop.png`: 사용자 실행·환경·API·분석 화면 안내를 현재 구현에 맞췄다.

## Verification

- `python3 -m unittest discover -s src -p 'test_*.py'` → 179 tests OK. 작업 시작 시 163개였으며 동시성 하드닝과 회귀 테스트에서 16개가 추가되었다.
- LLM-on live curl → `generatedBy: gpt-5.6-luna`, 5 clusters.
- `TREND_ANALYSIS_ENABLED=0` live curl → `generatedBy: heuristic`, 6 clusters.
- Playwright desktop·mobile 분석 탭과 home screenshot 확인 → console error 0건.
- `file docs/screenshot-analysis-desktop.png` → 1440 x 1173, 8-bit/color RGB PNG.
- `git diff --check` → clean.

## Risks

- LLM 출력은 요청마다 달라질 수 있다. 서버가 schema를 재검증하고 evidence ID를 신뢰된 title·URL로 복원해 변동 범위와 링크 위조를 제한한다.
- 로컬 프록시가 내려가면 휴리스틱 결과를 반환하고 300초 TTL 뒤 다시 시도한다. LLM 성공 결과는 1800초 동안 재사용한다.
- 휴리스틱 anchor는 제목 token과 script별 경계 규칙에 기반한다. 동의어, 번역어, 의미가 같지만 표기가 다른 주제는 하나로 묶이지 않을 수 있다.

## 변경 기록

- 2026-07-10: WP1-WP4의 구현과 검증 근거를 완료 기록으로 정리했다.
- 2026-07-10: 전체 delta 적대 리뷰 2회를 돌려 P1 5건(캐시 stale-commit 경합, force 폭주,
  history 오염 crash, 부분 snapshot velocity 왜곡, ASCII substring 오탐)과 P2 4건을 수정했다.
  잔여 3건(미스 coalescing, executor 상한, 채널 커버리지 guard 확대)까지 반영해 캐시
  single-flight와 module 단일 executor(7 thread 상한)를 도입했다.
