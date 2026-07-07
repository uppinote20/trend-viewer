# Cache Age API Record

## 이야기

프론트엔드가 모든 트렌드 탭에서 같은 방식으로 신선도를 계산할 수 있도록, 서버의 JSON 데이터 API 응답에 캐시 기준 시간을 명시했다. 기존에는 `/api/videos`, `/api/reels`, `/api/x`, `/api/threads`, `/api/tiktok`, `/api/ai`가 `fetchedAt`을 이미 반환했지만, 캐시 수명 값은 응답에 없어서 프론트가 진행률이나 만료 임박 상태를 비율로 표현하기 어려웠다.

이번 변경은 additive contract로 제한했다. 외부 엔드포인트, 헤더, fetch 로직, 기존 응답 키는 건드리지 않았고, `src/settings.py`의 기존 `CACHE_TTL` 값을 그대로 `cacheTtl`로 노출했다. 각 핸들러는 캐시 도구가 돌려준 원래 `fetched_at` 값을 `fetchedAt`에 유지하고, 같은 payload 최상위에 `cacheTtl`을 추가한다. 적용 위치는 `src/main.py:68`, `src/main.py:73`, `src/main.py:78`, `src/main.py:83`, `src/main.py:88`, `src/main.py:93`이다.

캐시 시간 의미도 다시 확인했다. `cached()`는 히트 시 저장된 `(fetched_at, result)`에서 `hit[0]`을 그대로 반환하므로, 캐시 히트가 새 시각을 만들지 않는다. 이 계약은 `src/shared/cache_tool.py:13-23`에 있고, `src/shared/test_cache_tool.py:26-32`에 seed된 캐시가 원래 `fetched_at`을 보존하는 테스트를 추가했다.

API 핸들러 계약 테스트는 네트워크를 쓰지 않도록 fetcher를 monkeypatch했다. `src/test_main_api_cache_metadata.py:22-84`는 `/api/videos`, `/api/reels`, `/api/x`, `/api/threads`, `/api/tiktok`, `/api/ai`의 응답 body에 `fetchedAt`과 `cacheTtl`이 모두 들어가는지 확인한다.

---

## 변경 기록

### `src/main.py` — 데이터 API 캐시 메타데이터 통일
- **Changes**: `CACHE_TTL`을 settings에서 가져오고, 여섯 JSON 데이터 API 응답에 top-level `cacheTtl`을 추가했다.
- **Impact**: 프론트엔드는 모든 데이터 탭에서 `{ fetchedAt, cacheTtl }`을 공통 freshness contract로 사용할 수 있다.
- **Verification**: `python3 -m unittest discover -s src -p 'test_*.py'` → 59 tests OK. `TREND_VIEWER_PORT=8792 python3 src/main.py` 후 `curl -s 'localhost:8792/api/saved'` → `{"items": []}`.

### `src/shared/test_cache_tool.py` — 캐시 히트 timestamp 회귀 테스트
- **Changes**: seed된 cache hit이 fetcher를 호출하지 않고 기존 `fetched_at`을 반환하는 테스트를 추가했다.
- **Impact**: `/api/*`의 `fetchedAt`이 캐시 히트에서도 실제 수집 시각을 유지한다는 전제를 보호한다.
- **Verification**: `python3 -m unittest discover -s src -p 'test_*.py'` → 59 tests OK.

### `src/test_main_api_cache_metadata.py` — API payload contract 테스트
- **Changes**: 각 핸들러를 직접 호출하고 fetcher를 stub 처리해 `fetchedAt`, `cacheTtl` 존재와 값 전달을 검증한다.
- **Impact**: 앞으로 새로고침/캐시 UI가 의존하는 metadata contract가 깨지면 unit test에서 바로 잡힌다.
- **Verification**: `python3 -m unittest discover -s src -p 'test_*.py'` → 59 tests OK.
