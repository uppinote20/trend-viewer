---
created: 2026-07-07
tags: [trend-viewer, cxc-loop, trends, country, categorization]
aliases: [트렌드 로직 업그레이드 루프]
---

# 트렌드 로직 정합성 업그레이드 루프 기록

"트렌드 도구인데 트렌드 신호가 없다"는 지적에서 시작한 HOTL 루프다.
감사 → 리서치 → 백엔드 → 프론트 → 문서의 4개 워크페이즈를 PABCD로 돌렸고,
각 사이클마다 gpt-5.5 독립 리뷰어의 FAIL→수리→PASS 게이트를 통과했다.

## 무엇이 바뀌었나

수집이 "하드코딩 KR 검색어 9개 + 조회수 정렬"에서 다음으로 바뀌었다.

1. 국가 축: `/api/videos?country=KR|US|JP` — hl/gl 파라미터화, 국가별 검색어
   세트(mukbang/モッパン 등), ko/en/ja 상대시간 기간 필터, 캐시 키 분리.
2. 급상승 축: 신규 `src/trends/` — Google Trends Trending Now RSS(geo별),
   근사 검색량 + 관련 뉴스 3건, 실패 시 120초 네거티브 캐시. `/api/trends`.
3. 카테고리 축: AI 뉴스가 2피드 → 17피드(글로벌 8 + 국내 7 + 기존 2)로,
   가중 키워드 분류기(엔티티 2점/일반 1점, 리드 2점 이상 확정)가
   모델·제품/연구/산업·투자/정책·규제를 붙이고 제목 정규화로 dedupe한다.
4. 파서 방어: `parse_view_count`가 1.5만/4.5B/2.5億/1,5K 축약 표기를 처리한다.
5. 프론트: 국가 세그먼트(해시 영속·캐시 무효화·홈 브리핑 연동), 급상승 탭 +
   홈 선두 섹션, AI 뉴스 카테고리 칩, safeUrl 스킴 가드, 모바일 탭 nowrap.

## 근거 문서

- 감사: [110_logic-audit.md](../../_plan/110_logic-audit.md) — A1~A9 코드 라인 근거.
- 리서치: [120_channel-research.md](../../_plan/120_channel-research.md) — 익스플로러
  3기의 라이브 curl 실측 (FEtrending 400 사망 확인, Trends RSS 채택 등).

## 검증 증거 (2026-07-07)

- `python3 -m unittest discover -s src -p 'test_*.py'` → 91개 통과 (기존 66).
- 라이브: KR 20 / US 39 / JP쇼츠 40건, 제목 언어 국가 일치. `/api/trends`
  geo별 10건(status=ok). `/api/ai` 80건 전부 region/category 보유, 소스 34종.
- Playwright 스크린샷: 데스크톱 1440px + 모바일 390px, 가로 오버플로 없음,
  국가 연속 전환 레이스에서 마지막 국가(일본) 렌더 확인. docs/에 5장 갱신.

## 리뷰 사이클

- WP3 백엔드 리뷰어: FAIL(분류기 가중치 블로커 + 경고 2) → 수리 → PASS.
- WP4 프론트 리뷰어: FAIL(URL 스킴 XSS 블로커 + 경고 3) → 수리 → PASS.

범위 밖으로 남긴 것: reels/tiktok/threads/x 계정 기반 수집 재설계(별도 루프),
영상 정렬의 신선도 결합 점수(A2 후속 과제), JP 기간 필터의 週間前 경계 실측 보강.
