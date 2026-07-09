# 260708 date-radar-automation

## Summary

Added a date-course automation lane to trend-viewer using the existing stdlib-only, unauthenticated source pattern.

## Changes

- `src/date/date_tool.py`: new date radar backend that merges YouTube InnerTube search results and KR Google Trends date-related keywords.
- `src/date/test_date_tool.py`: coverage for merge/filter/cache behavior.
- `src/main.py`: new `/api/date` endpoint.
- `src/frontend/index.html`: new `데이트` tab, country-aware loading, home briefing section, and date cards.
- `src/shared/cache_tool.py`: monotonic guard for same-tick cache writes while preserving mocked/time-travel tests.
- `README.md`: documented the new tab and updated test count.
- `devlog/str_func/date.md`: module notes.

## Verification

- `python3 -m unittest discover -s src -p 'test_*.py'` → 93 tests OK.
- Local server smoke: `GET http://127.0.0.1:8779/api/date?country=KR` returned 14 ideas and 2 briefing lines.
- Browser smoke: opened `http://127.0.0.1:8779/#tab=date`, verified the 데이트 tab renders with no console errors.

## Risks

- YouTube InnerTube and Google Trends RSS are unauthenticated/public endpoints and can change format or throttle.
- Google Trends keyword enrichment is KR-only for now; US/JP still use locale-specific YouTube search.
