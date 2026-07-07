---
created: 2026-07-07
tags: [trend-viewer, research, collection-channels, feeds, youtube-locale]
aliases: [수집채널 리서치, WP2 리서치]
---

# 무인증 수집채널 리서치 (2026-07-07 실측)

이 문서는 110 감사 문서의 수리 방향을 실제 엔드포인트 실측으로 확정한 기록이다.
gpt-5.5 익스플로러 3기가 병렬로 curl 라이브 검증했고, 본선 web_search로 교차 확인했다.
모든 결론은 2026-07-07 KST 기준 실측이다. 구현(WP3)은 이 문서의 표를 그대로 코드로 옮긴다.

---

## R1. 트렌딩 채널 실측 결과

| 채널 | 상태 | 판정 (20-80) |
|---|---|---:|
| Google Trends RSS `trends.google.com/trending/rss?geo=KR\|US\|JP` | 200, RSS 10건, `ht:approx_traffic`/`ht:picture`/`ht:news_item*` 필드 제공 | 75 채택 |
| HN Algolia `hn.algolia.com/api/v1/search?query=...&tags=story` | 200, JSON, `points/num_comments/created_at_i` | 80 채택 |
| YouTube innertube `FEtrending` browse | 400 INVALID_ARGUMENT (KR/US/JP 전부, 차트 variant 포함) | 20 폐기 |
| Google Trends legacy daily RSS | 404 | 20 폐기 |
| Reddit `.json` 무인증 | 403 (UA 위장 불충분) | 25 폐기 |

🟢 Google Trends RSS가 geo별 급상승 신호의 유일한 안정 무인증 소스다.
item당 검색어 + 근사 트래픽 + 대표 이미지 + 관련 뉴스 기사(제목/URL/소스/이미지)가 온다.

> 출처: gpt-5.5 익스플로러 실측 curl (2026-07-07), [Google Trends RSS KR](https://trends.google.com/trending/rss?geo=KR)
> 출처: [YouTube Data API Revision History — Trending 폐지](https://developers.google.com/youtube/v3/revision_history)

## R2. YouTube 검색 국가 파라미터화 실측

같은 protobuf params blob(`CAMSBAgDEAE=` 등 6종)이 KR/US/JP 전 로케일에서 동작한다. 🟢
로케일은 `context.client.hl/gl`로만 결정된다. 즉 `build_search_params`는 그대로 두고
payload의 hl/gl만 파라미터화하면 된다.

상대시간 문자열 실측 (기간 필터 어휘):

| 로케일 | day 초과 배제 | week 초과 배제 | month 초과 배제 |
|---|---|---|---|
| ko | `일 전`, `주 전`, `개월 전`, `년 전` | `주 전`, `개월 전`, `년 전` | `개월 전`, `년 전` |
| en | `day ago`, `days ago`, `week ago`, `weeks ago`, `month ago`, `months ago`, `year ago`, `years ago` | `week`/`month`/`year` 계열 | `month`/`year` 계열 |
| ja | `日前`, `週間前`, `か月前`, `年前` | `週間前`, `か月前`, `年前` | `か月前`, `年前` |

주의: en은 `7 days ago`→`2 weeks ago`로 넘어가며 단복수 둘 다 존재. ja는 숫자와 단위 사이 공백(`2 日前`).
en week 필터에서 `days ago`는 배제하면 안 된다(1~13일이 day 표기로 옴). day 필터에서만 `day(s) ago`를 배제한다.
라이브 스트림 접두(`Streamed ...`, `... に配信済み`)는 상대시간 부분 문자열 매칭으로 자연 처리된다.

조회수 표기 실측:

| 로케일 | viewCountText (전체 표기) | shortViewCountText (축약) |
|---|---|---|
| ko | `조회수 17,086,098,547회` → digits-only OK | `조회수 170억회` → 170 오파싱 |
| en | `17,086,098,940 views` → OK | `4.5B views` → 45 오파싱 |
| ja | `17,086,098,940回視聴` → OK | `2.5億回視聴` → 25 오파싱 |

현행 코드는 viewCountText만 읽으므로 당장은 무사하지만, 접미사 파서(K/M/B=1e3/1e6/1e9,
만/万=1e4, 억/億=1e8)를 `parse_view_count`에 넣어 축약 표기까지 방어한다.
`watching`/`시청 중`/`人が視聴中`은 라이브 시청자 수이므로 조회수로 취급하지 않는다.

> 출처: gpt-5.5 익스플로러 실측 curl, [YouTube InnerTube search](https://www.youtube.com/youtubei/v1/search) (2026-07-07 KST)

국가별 카테고리 검색어 (구현 시 그대로 사용):

| KR 카테고리 | US | JP |
|---|---|---|
| 먹방 | mukbang / food challenge | モッパン / 大食い |
| 뷰티/패션 | makeup tutorial / beauty vlog | メイク 美容 / ファッション 購入品 |
| 브이로그 | daily vlog / week in my life | 日常 vlog / 一日密着 |
| 예능/코미디 | funny videos / comedy skits | お笑い コント / バラエティ 面白い |
| 영화/드라마 | movie review / Netflix review | 映画 レビュー / ドラマ 考察 |
| 테크/IT | tech review / AI tools | ガジェット レビュー / AI ツール |
| 지식/교육 | explained / educational documentary | 解説 わかりやすい / ゆっくり解説 |
| 여행 | travel vlog / best places to visit | 旅行 vlog / ひとり旅 |
| 동물 | cute animals / funny pets | 動物 かわいい / 猫 犬 癒し |

## R3. AI 뉴스 피드 레지스트리 (16개 전수 200 OK 실측)

글로벌: TechCrunch AI, The Verge AI, VentureBeat AI, Ars Technica AI, MIT Tech Review AI,
arXiv cs.AI, HN Algolia(search_by_date), Google News US AI.
국내: AI타임스, 전자신문 AI(04046.xml), 전자신문 IT(03.xml), ZDNet Korea(feedburner),
한국경제 IT, Google News KR AI, Google News KR 정책·규제.

전 피드 pubDate 존재(HN은 created_at). 상세 URL 표와 기본 카테고리 매핑은 익스플로러
보고서 기준으로 ai_news_tool의 FEED_REGISTRY 상수에 그대로 옮긴다.

분류기 스펙 (키워드 스코어링):
- 카테고리 4종: 모델·제품 / 연구 / 산업·투자 / 정책·규제. 무득점·동점은 피드 기본 카테고리, 그것도 mixed면 mixed.
- 엔티티·구문 히트 2점, 일반 단어 1점. 2점 이상 리드 시 확정.
- 종합지(Google News, ZDNet, 한경, HN 등)는 AI 앵커 키워드(ai, 인공지능, llm, gpt, openai,
  anthropic, gemini, 생성형, machine learning, 머신러닝 등) 1개 이상 없으면 수집 제외.
- "AI" 단독 매칭은 단어 경계 필수(Airport 오탐 방지, HN 실측 사례).

> 출처: gpt-5.5 익스플로러 실측 curl 16피드 (2026-07-07 KST)
> 출처: [Google News RSS 크롤링 유지 확인 — Feedfetcher](https://developers.google.com/crawling/docs/crawlers-fetchers/feedfetcher)

## R4. WP3 구현 결정 사항

1. `youtube_tool`: `COUNTRY_LOCALE = {KR:(ko,KR), US:(en,US), JP:(ja,JP)}`, 국가별 CATEGORY 쿼리 테이블, `within_period` 다국어화(day에서만 en `day(s) ago` 배제), 캐시 키에 country 포함.
2. `shared/http_tool.parse_view_count`: 접미사 배수 파서로 교체(하위호환: 전체 표기는 동일 결과).
3. 신규 `trends/trends_tool.py`: Google Trends RSS geo별 수집(`ht:` 네임스페이스 파싱), `/api/trends?country=KR` 라우트.
4. `ai_news_tool`: FEED_REGISTRY(16피드) + `classify_news()` + 제목 정규화 dedupe + ts=0 폴백을 수집 시각으로 교체, item에 `region`/`category` 필드. HN Algolia는 일반 트렌딩이 아니라 AI 뉴스 보강 전용으로 한정한다(리뷰어 지적 반영).
5. 프론트: 영상/쇼츠 탭 국가 세그먼트(KR/US/JP), 급상승(트렌드) 섹션, AI 뉴스 카테고리 칩.
   국가 상태는 4곳을 함께 만진다(리뷰어 지적 반영): `state`에 country 추가, 해시 저장/복원에 country 포함,
   국가 변경 시 영상/쇼츠 캐시 무효화, 홈 브리핑의 `/api/videos?period=week` 하드코딩 URL에 country 반영.

범위 밖 유지: reels/tiktok/threads/x 재설계, 유료·인증 API, 신규 의존성.
