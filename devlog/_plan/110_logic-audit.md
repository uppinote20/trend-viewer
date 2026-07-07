---
created: 2026-07-07
tags: [trend-viewer, logic-audit, trending, ai-news, categorization]
aliases: [로직 정합성 감사, WP1 감사]
---

# 트렌드 수집 로직 정합성 감사

이 문서는 trend-viewer가 "트렌드 도구"라는 이름값을 실제로 하는지 소스 코드 기준으로 감사한 기록이다.
결론부터 말하면 현재 구조는 "고정 검색어의 조회수 상위 모음"이지 급상승 신호를 담은 트렌딩이 아니다.
아래 각 항목은 코드 라인 근거와 함께 무엇이 왜 약한지, 어떤 방향으로 고칠지를 적는다.
후속 구현(WP3/WP4)은 이 문서의 번호를 참조한다.

---

## A1. 검색 결과를 트렌딩으로 오인하는 구조

`src/youtube/youtube_tool.py:12` 의 `CATEGORIES` 는 9개의 하드코딩 한국어 검색어이고,
`get_videos` 는 이 검색어를 youtubei `/v1/search` 로 조회한 뒤 결과를 합친다.
검색 API는 "관련도 + 필터" 기준이지 급상승(velocity) 기준이 아니므로,
오래됐지만 조회수 큰 영상이 항상 이길 수밖에 없다. 기간 필터가 이를 일부 보정하지만
"이번 주 안에서 누적 조회수 상위"일 뿐 "지금 뜨는 것"과는 다른 신호다.

- 근거: `CATEGORIES`(12행), `ALL_MERGE`(24행), `merge_yt_searches` 정렬(151행).

YouTube 자체 트렌딩 대체재는 이제 없다. 2025-07-21부로 Trending 페이지가 제거됐고
Data API `chart=mostPopular` 도 음악/영화/게임 차트만 반환한다. 🟢
따라서 검색 기반 수집은 유지하되, 급상승 축은 외부 신호(Google Trends RSS)로 채워야 한다.

> 출처: [YouTube Data API Revision History](https://developers.google.com/youtube/v3/revision_history)
> 출처: [Videos: list | YouTube Data API](https://developers.google.com/youtube/v3/docs/videos/list)

## A2. 조회수 단독 정렬

`merge_yt_searches` (151행)는 `views` 내림차순 정렬만 한다. 신선도(published), 좋아요,
채널 규모 대비 성과 같은 신호가 전혀 반영되지 않는다. 기간이 "week"면 6일 전 1,000만 회
영상이 12시간 전 300만 회 영상을 항상 이긴다. 트렌드 도구라면 후자가 더 중요한 신호다.

- 방향: 정렬 키를 조회수 단독에서 (조회수, 신선도) 결합 점수로 바꾸거나,
  최소한 프론트에 "최신순" 토글을 주고 published 상대시간을 정규화한 rank 필드를 제공한다.

## A3. 국가 고정 (gl=KR / hl=ko)

`yt_search` payload(85-86행)와 `yt_like_count` payload(112-113행) 모두 `hl:ko, gl:KR` 고정.
국내 트렌드만 볼 수 있고, 쇼츠처럼 글로벌 밈이 국경을 넘는 포맷에서 미국/일본 신호를 놓친다.
`/api/videos` 핸들러(`src/main.py` `_handle_videos`)에도 country 파라미터가 없다.

- 방향: `country` 파라미터(KR/US/JP)를 받아 hl/gl 매핑, 캐시 키에 country 포함,
  국가별 카테고리 검색어 세트 분리(먹방→mukbang→モッパン 등).

## A4. 상대시간 텍스트 필터의 로케일 취약성

`PERIOD_EXCLUDE`(28행)는 "일 전/주 전/개월 전/년 전" 한국어 문자열 매칭이다.
`within_period`(37행)는 이 문자열이 없으면 통과시키므로, hl을 en/ja로 바꾸는 순간
"3 days ago" / "3 日前" 이 걸러지지 않아 기간 필터가 조용히 전부 통과로 무력화된다.
빈 published(40행 첫 분기)도 무조건 통과라서 실패가 보이지 않는다.

- 방향: ko/en/ja 상대시간 어휘 테이블로 확장하고, 알 수 없는 포맷은 보수적으로 처리한다.

## A5. parse_view_count 의 축약 표기 오파싱

`src/shared/http_tool.py:27` 의 `parse_view_count` 는 숫자만 남긴다.
KR 검색 결과는 보통 "조회수 1,234,567회" 전체 표기라 무사하지만, 로케일에 따라
"1.5M views" → 15, "150万回視聴" → 150 처럼 자릿수가 무너질 수 있다.
국가 다변화 전에 만/억, K/M/B, 万/億 접미사 파싱을 넣어야 정렬(A2)이 유지된다.

- 근거: 27-29행 digits-only 정규식. 실측 포맷은 WP2 리서치(120 문서)에서 확정.

## A6. AI 뉴스 채널 협소성

`src/ai_news/ai_news_tool.py:13` 의 `NEWS_FEEDS` 는 Google News RSS 2개뿐이고
쿼리도 "AI 영상 생성/AI video model" 한정이다. AI 뉴스 탭이라는 이름과 달리
영상생성 소식 외의 모델 릴리스, 연구, 투자, 규제 뉴스가 구조적으로 들어올 수 없다.
카테고리 축도, 소스 다양성도 없다. Google News RSS 자체는 2026-07 현재 정상 동작한다. 🟢

> 출처: [Google News publication pages 전환 공지](https://support.google.com/news/publisher-center/answer/15898024?hl=en)
> 출처: [Google Feedfetcher](https://developers.google.com/crawling/docs/crawlers-fetchers/feedfetcher)

- 방향: 피드 레지스트리(지역 KR/글로벌 × 카테고리 모델·제품/연구/산업·투자/정책·규제)로 확장,
  헤드라인 키워드 분류기 + region/category 필드 부여.

## A7. ts=0 폴백과 정렬 왜곡

pubDate 파싱 실패 시 `ts = 0`(47행)으로 두고 ts 내림차순 정렬(62행)하므로,
날짜 포맷이 다른 피드의 기사는 전부 목록 맨 끝에 깔린다. 소스를 늘리는 순간
이 왜곡이 커진다. 파싱 실패는 수집 시각으로 폴백하거나 별도 표기해야 한다.

## A8. 지역/소스 간 dedupe 부재

`fetch_news` 는 피드별 25개(57행)를 이어붙여 40개(63행)로 자를 뿐, 같은 사건을 다룬
국내/해외 기사 중복을 제거하지 않는다. 다중 피드 확장 시 제목 정규화 기반
dedupe(공백/구두점 제거 + 소스 우선순위)가 필요하다.

## A9. 급상승 축 부재 (신규 채널 필요)

현재 어떤 탭에도 "지금 검색량이 튀는 주제" 신호가 없다. Google Trends의 geo별
Trending Now RSS(`trends.google.com/trending/rss?geo=KR|US|JP`)가 무인증으로 살아 있어 🟢
이를 새 수집 채널로 붙이면 검색어 + 관련 뉴스 + 트래픽 근사치를 얻는다.
실측 응답 구조는 WP2 리서치 문서에서 확정한다.

> 출처: [Explore the searches that are Trending now — Google Help](https://support.google.com/trends/answer/3076011?hl=en)
> 출처: [Introducing the Google Trends API (alpha)](https://developers.google.com/search/blog/2025/07/trends-api)

---

## 수리 우선순위 (WP3 입력)

| 순위 | 항목 | 대상 |
|---|---|---|
| 1 | A3+A4+A5 국가 파라미터화 3종 세트 | youtube_tool, http_tool, main.py |
| 2 | A6+A7+A8 AI 뉴스 레지스트리/분류기/dedupe | ai_news_tool |
| 3 | A9 Google Trends RSS 채널 신설 | 신규 trends 모듈 + main.py |
| 4 | A2 정렬 개선(신선도 결합) | youtube_tool + frontend |

reels/tiktok/threads/x 계정 기반 수집은 이번 범위 밖이다(계정 큐레이션 모델 자체는 정합).
