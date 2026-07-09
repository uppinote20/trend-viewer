# date

## 역할

`date` 모듈은 기존 오픈소스/무인증 데이터 수집 구조를 재사용해 데이트 코스 후보를 자동 브리핑한다. YouTube와 Trends의 수치 단위가 다르므로 각 소스 안에서만 지표순으로 정렬한 뒤 영상부터 1:1로 교차 배치한다.

## 데이터 소스

- YouTube InnerTube 검색: 국가별 5개 질의를 병렬 수집한다. KR은 기존 한국어 질의를 유지하고 US/JP는 현지어 데이트 질의를 사용한다.
- Google Trends Trending Now RSS: 한국 급상승 키워드만 보강한다. `데이트`가 직접 나오거나, 전시/맛집/카페 같은 활동어와 커플/연인/기념일 같은 데이트 맥락어가 함께 나온 항목만 허용한다.

## 공개 API

- `date_tool.get_date_radar(country="KR", force=False)`
  - 반환: `(data, fetched_at, cache_ttl)`
  - `data.ideas`: 자동 정렬된 후보 카드
  - `data.briefing`: 화면 상단 요약 문장
  - `data.errors`: `youtube` 또는 `trends` 단위 수집 오류

## 제약

- Python 표준 라이브러리만 사용한다.
- 별도 API 키/로그인/외부 패키지를 추가하지 않는다.
- 국가는 YouTube locale과 같은 `KR`, `US`, `JP`를 허용하며 미지원 값은 `KR`로 폴백한다.
- Trends 보강은 KR만 지원한다.
- 전체 후보가 비고 수집 오류가 있으면 실패 결과를 120초만 캐시한다.
