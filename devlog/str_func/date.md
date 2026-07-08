# date

## 역할

`date` 모듈은 기존 오픈소스/무인증 데이터 수집 구조를 재사용해 데이트 코스 후보를 자동 브리핑한다.

## 데이터 소스

- YouTube InnerTube 검색: `서울 데이트 코스`, `주말 데이트 추천`, `실내 데이트`, `전시 데이트`, `맛집 데이트`
- Google Trends Trending Now RSS: 한국 급상승 키워드 중 데이트/전시/맛집/카페/축제/공연/핫플 등과 맞는 항목

## 공개 API

- `date_tool.get_date_radar(country="KR", force=False)`
  - 반환: `(data, fetched_at, cache_ttl)`
  - `data.ideas`: 자동 정렬된 후보 카드
  - `data.briefing`: 화면 상단 요약 문장

## 제약

- Python 표준 라이브러리만 사용한다.
- 별도 API 키/로그인/외부 패키지를 추가하지 않는다.
- 국가는 YouTube locale과 같은 `KR`, `US`, `JP`를 허용하며 미지원 값은 `KR`로 폴백한다.
