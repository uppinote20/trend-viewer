---
created: 2026-07-07
tags: [trend-viewer, shared-tools, stdlib-python, cache, accounts]
aliases: [shared 모듈, 공유 도구, http cache accounts]
---

# shared 모듈 문서

이 문서는 `src/shared/` 모듈을 다음 작업자가 바로 이어받을 수 있게 설명한다.
소스 코드를 먼저 읽고, 파일 경계와 함수 경계를 기준으로 책임을 적는다.
여기서 말하는 동기화는 코드 변경 뒤 이 문서와 테스트 관점도 함께 맞추는 일을 뜻한다.
외부 웹 검색 없이 로컬 소스와 포팅 계획 문서만 근거로 삼는다.

---

## File Tree

이 섹션은 실제 파일 수와 라인 수를 기준으로 모듈의 표면적을 보여준다.
라인 수가 달라지면 이 표도 같이 갱신한다.

| 파일 | 라인 수 | 역할 |
|---|---:|---|
| `src/shared/__init__.py` | 3 | shared 하위 도구 배럴 import |
| `src/shared/http_tool.py` | 29 | HTTP 요청과 JSON 파싱, 조회수 숫자 파싱 |
| `src/shared/cache_tool.py` | 23 | 메모리 TTL 캐시 |
| `src/shared/accounts_tool.py` | 54 | 계정 파일 저장소와 source registry |
| `src/shared/img_proxy_tool.py` | 32 | 썸네일 이미지 프록시와 allowlist 캐시 |
| `src/shared/test_http_tool.py` | 59 | HTTP helper 단위 테스트 |
| `src/shared/test_cache_tool.py` | 48 | TTL 캐시 단위 테스트 |
| `src/shared/test_accounts_tool.py` | 62 | 계정 저장소 단위 테스트 |
| `src/shared/test_img_proxy_tool.py` | 47 | 이미지 프록시 단위 테스트 |

### 파일별 읽기 순서

1. `src/shared/__init__.py`를 읽는다. shared 하위 도구 배럴 import 라인 수는 3줄이다.
2. `src/shared/http_tool.py`를 읽는다. HTTP 요청과 JSON 파싱, 조회수 숫자 파싱 라인 수는 29줄이다.
3. `src/shared/cache_tool.py`를 읽는다. 메모리 TTL 캐시 라인 수는 23줄이다.
4. `src/shared/accounts_tool.py`를 읽는다. 계정 파일 저장소와 source registry 라인 수는 54줄이다.
5. `src/shared/img_proxy_tool.py`를 읽는다. 썸네일 이미지 프록시와 allowlist 캐시 라인 수는 32줄이다.
6. `src/shared/test_http_tool.py`를 읽는다. HTTP helper 단위 테스트 라인 수는 59줄이다.
7. `src/shared/test_cache_tool.py`를 읽는다. TTL 캐시 단위 테스트 라인 수는 48줄이다.
8. `src/shared/test_accounts_tool.py`를 읽는다. 계정 저장소 단위 테스트 라인 수는 62줄이다.
9. `src/shared/test_img_proxy_tool.py`를 읽는다. 이미지 프록시 단위 테스트 라인 수는 47줄이다.

### 파일 경계 메모

- `src/shared/__init__.py`는 shared 하위 도구 배럴 import을 맡는다.
- `src/shared/__init__.py`의 현재 기준 라인 수는 3줄이다.
- `src/shared/__init__.py`가 바뀌면 File Tree와 관련 체크리스트를 함께 갱신한다.
- `src/shared/http_tool.py`는 HTTP 요청과 JSON 파싱, 조회수 숫자 파싱을 맡는다.
- `src/shared/http_tool.py`의 현재 기준 라인 수는 29줄이다.
- `src/shared/http_tool.py`가 바뀌면 File Tree와 관련 체크리스트를 함께 갱신한다.
- `src/shared/cache_tool.py`는 메모리 TTL 캐시을 맡는다.
- `src/shared/cache_tool.py`의 현재 기준 라인 수는 23줄이다.
- `src/shared/cache_tool.py`가 바뀌면 File Tree와 관련 체크리스트를 함께 갱신한다.
- `src/shared/accounts_tool.py`는 계정 파일 저장소와 source registry을 맡는다.
- `src/shared/accounts_tool.py`의 현재 기준 라인 수는 54줄이다.
- `src/shared/accounts_tool.py`가 바뀌면 File Tree와 관련 체크리스트를 함께 갱신한다.
- `src/shared/img_proxy_tool.py`는 썸네일 이미지 프록시와 allowlist 캐시을 맡는다.
- `src/shared/img_proxy_tool.py`의 현재 기준 라인 수는 32줄이다.
- `src/shared/img_proxy_tool.py`가 바뀌면 File Tree와 관련 체크리스트를 함께 갱신한다.
- `src/shared/test_http_tool.py`는 HTTP helper 단위 테스트을 맡는다.
- `src/shared/test_http_tool.py`의 현재 기준 라인 수는 59줄이다.
- `src/shared/test_http_tool.py`가 바뀌면 File Tree와 관련 체크리스트를 함께 갱신한다.
- `src/shared/test_cache_tool.py`는 TTL 캐시 단위 테스트을 맡는다.
- `src/shared/test_cache_tool.py`의 현재 기준 라인 수는 48줄이다.
- `src/shared/test_cache_tool.py`가 바뀌면 File Tree와 관련 체크리스트를 함께 갱신한다.
- `src/shared/test_accounts_tool.py`는 계정 저장소 단위 테스트을 맡는다.
- `src/shared/test_accounts_tool.py`의 현재 기준 라인 수는 62줄이다.
- `src/shared/test_accounts_tool.py`가 바뀌면 File Tree와 관련 체크리스트를 함께 갱신한다.
- `src/shared/test_img_proxy_tool.py`는 이미지 프록시 단위 테스트을 맡는다.
- `src/shared/test_img_proxy_tool.py`의 현재 기준 라인 수는 47줄이다.
- `src/shared/test_img_proxy_tool.py`가 바뀌면 File Tree와 관련 체크리스트를 함께 갱신한다.

## Module Responsibility

`src/shared/`는 포팅된 기능 모듈들이 반복해서 쓰는 HTTP, 캐시, 계정 저장소, 이미지 프록시를 한 곳에 둔다.
각 기능 모듈은 외부 API 파싱에 집중하고, 네트워크 요청과 TTL, 계정 파일 처리는 shared에 위임한다.
서버 라우트도 이미지 프록시와 계정 갱신을 shared 함수로 처리하므로 이 폴더는 작은 공통 런타임 계층이다.

### 책임 경계

- HTTP helper는 User-Agent와 JSON payload 규칙을 소유한다.
- Cache helper는 1시간 TTL과 force refresh 계약을 소유한다.
- Accounts helper는 config 디렉터리의 JSON 파일 계약을 소유한다.
- Image proxy는 프론트 썸네일 CORS와 allowlist 정책을 소유한다.

### 운영 관점

- `cached`의 반환 계약은 항상 데이터와 epoch timestamp 쌍이다.
- `update_accounts`는 unknown source일 때 KeyError를 낼 수 있고, main.py는 먼저 `get_source`로 막는다.
- `fetch_image`는 dict body를 JSON으로 보낼 수 있게 main.py의 `_send` 계약에 맞춘다.
- allowlist는 `settings.IMG_PROXY_ALLOW` tuple의 suffix 매칭이다.

## Key Function Signatures

아래 함수명은 실제 소스의 공개 함수와 내부 헬퍼를 기준으로 한다.
테스트 헬퍼는 동작 계약을 보여주는 경우에만 포함한다.

### `http_get(url: str, payload=None, headers=None, timeout=15)`

- `settings.UA`를 User-Agent로 붙여 `urllib.request.Request`를 만든다.
- payload가 있으면 JSON으로 인코딩하고 `Content-Type: application/json`을 붙인다.
- 반환값은 `(content_type, body_bytes)` 튜플이다.

### `http_json(url: str, payload=None, headers=None, timeout=15)`

- `http_get` 결과 body를 UTF-8 문자열로 디코딩한 뒤 JSON으로 파싱한다.
- 기능 모듈들이 외부 API 호출을 표준화할 때 사용한다.

### `parse_view_count(text: str) -> int`

- 조회수 문자열에서 숫자만 남긴다.
- 숫자가 없으면 0을 반환한다.

### `cached(key, force, fetch_fn)`

- 캐시 hit이고 TTL 안이며 force가 거짓이면 저장된 값을 반환한다.
- miss이거나 force가 참이면 `fetch_fn`을 실행하고 현재 시각과 함께 저장한다.
- 반환값은 `(result, fetched_at)`이다.

### `load_accounts(path, defaults)`

- JSON 파일에서 계정 목록을 읽는다.
- 파일 오류, JSON 오류, 빈 리스트는 defaults 복사본으로 폴백한다.

### `save_accounts(path, accounts)`

- 상위 디렉터리를 만들고 계정 목록을 UTF-8 JSON으로 저장한다.
- `ensure_ascii=False`, `indent=2` 형식을 유지한다.

### `register_source(name, filename, defaults, preserve_case=False)`

- source 이름을 config 파일 경로와 기본 계정 목록에 연결한다.
- X처럼 대소문자를 보존해야 하는 모듈은 `preserve_case=True`를 넘긴다.

### `get_source(name)`

- 등록된 source dict를 반환한다.
- 등록되지 않았으면 `None`을 반환한다.

### `update_accounts(name, action, username)`

- username을 strip하고 앞의 `@`를 제거한다.
- add/remove를 처리한 뒤 저장하고 최신 계정 목록을 반환한다.

### `fetch_image(url)`

- https URL과 allowlist host를 검사한다.
- 캐시 hit이면 네트워크를 건너뛴다.
- 성공은 `(200, content_type, body)`, 차단은 400, fetch 실패는 502를 반환한다.

### 테스트 함수 지도

- `HttpToolTest.test_parse_view_count_digits_and_empty`
- `HttpToolTest.test_http_get_header_and_payload_construction`
- `CacheToolTest.test_cached_hit`
- `CacheToolTest.test_cached_ttl_expiry`
- `CacheToolTest.test_cached_force`
- `AccountsToolTest.test_load_save_roundtrip`
- `AccountsToolTest.test_load_corrupt_json_falls_back_to_defaults`
- `AccountsToolTest.test_registry_add_remove_lowercases_by_default`
- `AccountsToolTest.test_registry_preserves_case_for_x`
- `AccountsToolTest.test_unknown_source`
- `ImgProxyToolTest.test_allowlist_rejects_http_and_disallowed_host`
- `ImgProxyToolTest.test_cache_hit_skips_fetch`
- `ImgProxyToolTest.test_cache_clear_at_max`

## Dependencies

이 모듈이 직접 가져오는 대상과 런타임으로 기대하는 설정을 적는다.

- `json`, `re`, `urllib.request`
- `threading`, `time`
- `os`
- `urllib.parse.urlparse`
- `settings.UA`
- `settings.CACHE_TTL`
- `settings.CONFIG_DIR`
- `settings.IMG_CACHE_MAX`
- `settings.IMG_PROXY_ALLOW`
- `shared.http_tool`

### 의존성 변경 시 주의점

- json, re, urllib.request 변경은 호출 경로와 테스트 더블을 함께 확인한다.
- threading, time 변경은 호출 경로와 테스트 더블을 함께 확인한다.
- os 변경은 호출 경로와 테스트 더블을 함께 확인한다.
- urllib.parse.urlparse 변경은 호출 경로와 테스트 더블을 함께 확인한다.
- settings.UA 변경은 호출 경로와 테스트 더블을 함께 확인한다.
- settings.CACHE_TTL 변경은 호출 경로와 테스트 더블을 함께 확인한다.
- settings.CONFIG_DIR 변경은 호출 경로와 테스트 더블을 함께 확인한다.
- settings.IMG_CACHE_MAX 변경은 호출 경로와 테스트 더블을 함께 확인한다.
- settings.IMG_PROXY_ALLOW 변경은 호출 경로와 테스트 더블을 함께 확인한다.
- shared.http_tool 변경은 호출 경로와 테스트 더블을 함께 확인한다.

## Dependents

이 모듈을 import하거나 HTTP 라우트로 소비하는 쪽이다.

- `src/main.py` imports `accounts_tool`, `img_proxy_tool`
- `src/youtube/youtube_tool.py` imports `cache_tool`, `http_tool`
- `src/reels/reels_tool.py` imports `accounts_tool`, `cache_tool`, `http_tool`
- `src/x_twitter/x_twitter_tool.py` imports `accounts_tool`, `cache_tool`, `http_tool`
- `src/threads/threads_tool.py` imports `accounts_tool`, `cache_tool`, `http_tool`
- `src/tiktok/tiktok_tool.py` imports `accounts_tool`, `cache_tool`, `http_tool`
- `src/ai_news/ai_news_tool.py` imports `cache_tool`, `http_tool`
- `src/frontend/index.html` consumes `/api/img` and account POST routes through main.py

### 호출자 영향 범위

- `src/main.py` imports `accounts_tool`, `img_proxy_tool` 쪽 응답 shape가 깨지지 않는지 확인한다.
- `src/youtube/youtube_tool.py` imports `cache_tool`, `http_tool` 쪽 응답 shape가 깨지지 않는지 확인한다.
- `src/reels/reels_tool.py` imports `accounts_tool`, `cache_tool`, `http_tool` 쪽 응답 shape가 깨지지 않는지 확인한다.
- `src/x_twitter/x_twitter_tool.py` imports `accounts_tool`, `cache_tool`, `http_tool` 쪽 응답 shape가 깨지지 않는지 확인한다.
- `src/threads/threads_tool.py` imports `accounts_tool`, `cache_tool`, `http_tool` 쪽 응답 shape가 깨지지 않는지 확인한다.
- `src/tiktok/tiktok_tool.py` imports `accounts_tool`, `cache_tool`, `http_tool` 쪽 응답 shape가 깨지지 않는지 확인한다.
- `src/ai_news/ai_news_tool.py` imports `cache_tool`, `http_tool` 쪽 응답 shape가 깨지지 않는지 확인한다.
- `src/frontend/index.html` consumes `/api/img` and account POST routes through main.py 쪽 응답 shape가 깨지지 않는지 확인한다.

## Sync Checklist

코드를 바꾼 뒤에는 아래 항목을 순서대로 확인한다.
체크박스는 실제 변경에서 완료 여부를 남기는 용도다.

- [ ] HTTP header 변경 시 `test_http_tool.py` 요청 캡처를 갱신한다.
- [ ] 캐시 key shape가 바뀌면 모든 기능 모듈의 cache contract 테스트를 확인한다.
- [ ] CONFIG_DIR 위치가 바뀌면 계정 저장 테스트의 mock patch 경로를 갱신한다.
- [ ] IMG_PROXY_ALLOW가 바뀌면 프론트 썸네일 도메인과 함께 검토한다.
- [ ] 공유 helper에 새 책임을 넣기 전에 기능 모듈 소유가 아닌지 확인한다.

### 실패 동작 체크

- [ ] HTTP 오류가 기능 모듈에서 잡히도록 helper는 예외를 삼키지 않는다.
- [ ] 캐시 force가 참이면 TTL hit라도 fetch_fn을 호출해야 한다.
- [ ] 깨진 계정 JSON은 기본값으로 복구되어야 한다.
- [ ] 이미지 fetch 실패는 502 JSON error로 변환되어야 한다.

### 문서 동기화 체크

- [ ] `src/shared/__init__.py` 라인 수가 3줄에서 바뀌면 File Tree를 갱신한다.
- [ ] `src/shared/__init__.py`의 shared 하위 도구 배럴 import 설명이 실제 코드와 어긋나지 않는지 확인한다.
- [ ] `src/shared/http_tool.py` 라인 수가 29줄에서 바뀌면 File Tree를 갱신한다.
- [ ] `src/shared/http_tool.py`의 HTTP 요청과 JSON 파싱, 조회수 숫자 파싱 설명이 실제 코드와 어긋나지 않는지 확인한다.
- [ ] `src/shared/cache_tool.py` 라인 수가 23줄에서 바뀌면 File Tree를 갱신한다.
- [ ] `src/shared/cache_tool.py`의 메모리 TTL 캐시 설명이 실제 코드와 어긋나지 않는지 확인한다.
- [ ] `src/shared/accounts_tool.py` 라인 수가 54줄에서 바뀌면 File Tree를 갱신한다.
- [ ] `src/shared/accounts_tool.py`의 계정 파일 저장소와 source registry 설명이 실제 코드와 어긋나지 않는지 확인한다.
- [ ] `src/shared/img_proxy_tool.py` 라인 수가 32줄에서 바뀌면 File Tree를 갱신한다.
- [ ] `src/shared/img_proxy_tool.py`의 썸네일 이미지 프록시와 allowlist 캐시 설명이 실제 코드와 어긋나지 않는지 확인한다.
- [ ] `src/shared/test_http_tool.py` 라인 수가 59줄에서 바뀌면 File Tree를 갱신한다.
- [ ] `src/shared/test_http_tool.py`의 HTTP helper 단위 테스트 설명이 실제 코드와 어긋나지 않는지 확인한다.
- [ ] `src/shared/test_cache_tool.py` 라인 수가 48줄에서 바뀌면 File Tree를 갱신한다.
- [ ] `src/shared/test_cache_tool.py`의 TTL 캐시 단위 테스트 설명이 실제 코드와 어긋나지 않는지 확인한다.
- [ ] `src/shared/test_accounts_tool.py` 라인 수가 62줄에서 바뀌면 File Tree를 갱신한다.
- [ ] `src/shared/test_accounts_tool.py`의 계정 저장소 단위 테스트 설명이 실제 코드와 어긋나지 않는지 확인한다.
- [ ] `src/shared/test_img_proxy_tool.py` 라인 수가 47줄에서 바뀌면 File Tree를 갱신한다.
- [ ] `src/shared/test_img_proxy_tool.py`의 이미지 프록시 단위 테스트 설명이 실제 코드와 어긋나지 않는지 확인한다.

### 테스트 동기화 체크

- [ ] `HttpToolTest.test_parse_view_count_digits_and_empty`가 변경된 계약을 검증하는지 확인한다.
- [ ] `HttpToolTest.test_http_get_header_and_payload_construction`가 변경된 계약을 검증하는지 확인한다.
- [ ] `CacheToolTest.test_cached_hit`가 변경된 계약을 검증하는지 확인한다.
- [ ] `CacheToolTest.test_cached_ttl_expiry`가 변경된 계약을 검증하는지 확인한다.
- [ ] `CacheToolTest.test_cached_force`가 변경된 계약을 검증하는지 확인한다.
- [ ] `AccountsToolTest.test_load_save_roundtrip`가 변경된 계약을 검증하는지 확인한다.
- [ ] `AccountsToolTest.test_load_corrupt_json_falls_back_to_defaults`가 변경된 계약을 검증하는지 확인한다.
- [ ] `AccountsToolTest.test_registry_add_remove_lowercases_by_default`가 변경된 계약을 검증하는지 확인한다.
- [ ] `AccountsToolTest.test_registry_preserves_case_for_x`가 변경된 계약을 검증하는지 확인한다.
- [ ] `AccountsToolTest.test_unknown_source`가 변경된 계약을 검증하는지 확인한다.
- [ ] `ImgProxyToolTest.test_allowlist_rejects_http_and_disallowed_host`가 변경된 계약을 검증하는지 확인한다.
- [ ] `ImgProxyToolTest.test_cache_hit_skips_fetch`가 변경된 계약을 검증하는지 확인한다.
- [ ] `ImgProxyToolTest.test_cache_clear_at_max`가 변경된 계약을 검증하는지 확인한다.

## 변경 기록

- 2026-07-07: 실제 소스 기준으로 str_func 모듈 문서를 작성했다.

## 문서 연결

- [ ] 동기화 보강 1: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 2: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 3: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 4: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 5: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 6: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 7: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 8: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 9: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 10: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 11: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 12: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 13: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 14: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 15: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 16: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 17: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 18: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 19: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 20: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 21: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 22: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 23: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 24: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 25: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 26: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 27: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 28: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 29: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 30: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 31: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 32: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 33: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 34: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 35: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 36: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 37: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 38: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 39: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 40: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 41: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 42: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 43: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 44: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 45: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- [ ] 동기화 보강 46: 함수명, 라우트명, 응답 키, 테스트 이름 중 하나라도 바뀌면 이 문서의 해당 항목을 같이 고친다.
- 이전: [[frontend.md]]
- 다음: [[youtube.md]]

