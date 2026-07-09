---
created: 2026-07-10
tags: [trend-viewer, analysis, gpt-5.6-luna, cross-platform, velocity]
aliases: [분석 엔진 계획, analysis engine plan]
---

# 130 — 분석 엔진 (WP2: LLM 클라이언트 + 휴리스틱 집계)

trend-viewer를 수집기에서 분석기로 올리는 첫 단계 계획이다. 로컬 ocx 프록시의
cursor/gpt-5.6-luna를 선택적 강화 수단으로 쓰고, LLM 없이도 완전한 휴리스틱
교차 플랫폼 상관·속도 분석이 돌아가야 한다. 아래는 3회 적대 감사(FAIL x2,
GO-WITH-FIXES)를 통과한 REV 4 계획 원문이다. WP3(/api/analysis)와 WP4(분석 탭)는
140/150 문서로 이어진다.

---

# WP2 — Analysis foundation: LLM client + heuristic aggregation core

> REV 4 after audit rounds 1-3 (Dewey; round 3 GO-WITH-FIXES blockers=3, folded as [Fn]).

Loop-spec: archetype=spec-satisfaction; trigger=goal outcome 2+3; goal=stdlib `src/analysis/` package
(SSE LLM client + deterministic cross-platform aggregation with velocity); non-goals=endpoint wiring
(WP3), frontend (WP4); verifier=`python3 -m unittest discover -s src -p 'test_*.py'` (mandatory
gate); live client smoke is CONDITIONAL on healthy proxy (`curl {base}/models` ok) and merely
recorded, never gating [R3]; stop=suite green; memory=goalplan c2/c3; terminal=DONE.

## Files (new)
- `src/analysis/__init__.py` — barrel; exports exactly: `llm_client_tool`, `keyword_tool`,
  `aggregate_tool` (module re-exports via `from . import ...`, matching src/shared/__init__.py
  barrel pattern) [B9][R9].
- `src/analysis/llm_client_tool.py` — stdlib SSE Responses client:
  - `is_enabled()` -> TREND_ANALYSIS_ENABLED != "0"
  - `complete(prompt, system=None, timeout=15, deadline=120)` -> str|None; POST {base}/responses
    with model, store:false, stream:true, input:[{role,content:[{type:"input_text",text}]}].
  - SSE parse [B7]: read line-by-line; events are `event:`/`data:` blocks; ignore comment lines,
    blank lines, and `data: [DONE]`. Per-line `json.loads` failure -> skip that line (tolerant),
    but transport-level failures (URLError incl. connection refused, HTTPError, socket.timeout)
    -> return None. Text assembly keyed by (output_index, content_index): store delta
    accumulation AND done-text per key; per key prefer its own `response.output_text.done`
    text, else its joined deltas; final result = keys concatenated in (output_index,
    content_index) sorted order. Empty assembled text -> None.
  - Deadlines [B7][R2][F1]: use http.client.HTTPConnection directly (NOT urllib) so the
    watchdog owns the socket: timeout=15 (inactivity per socket op); threading.Timer started
    BEFORE connect() (connection time counts toward the total deadline); at deadline (default
    120s) the watchdog calls conn.sock.shutdown(socket.SHUT_RDWR) (guarded for None/closed)
    which reliably interrupts a blocked recv/readline even under newline-less byte drip —
    urllib response.close() was empirically shown NOT to interrupt. Reader catches the raised
    OSError, returns partial text if non-empty else None; timer cancelled + conn.close() in
    finally. Activation test [F1]: REAL local ephemeral HTTP server (localhost socket, not a
    cooperative fake) dripping newline-less bytes; assert complete() returns within
    deadline+slack. (Localhost test server is allowed; "no live network" means no external
    endpoints.)
  - Real ocx stream shape (captured live 2026-07-10, model cursor/gpt-5.6-luna):
    `event: response.output_text.delta` + `data: {"type":"response.output_text.delta",
    "output_index":0,"content_index":0,"delta":"UNA"}` ... then `event: response.output_text.done`
    + `data: {..."text":"LUNA-OK"}`, then response.completed, then `data: [DONE]`.
  - Env: TREND_ANALYSIS_BASE_URL (default http://127.0.0.1:10100/v1),
    TREND_ANALYSIS_MODEL (default cursor/gpt-5.6-luna), TREND_ANALYSIS_ENABLED (default on).
  - No API key header needed for local ocx (verified live: LUNA-OK).
  - LLM policy [B7][R3]: default stays ENABLED (single-user local deployment). Mandatory gate =
    mocked SSE unittest suite ONLY. Live smoke runs in C-phase IF `{base}/models` responds
    within 5s; if proxy is down the smoke is skipped and recorded as skipped — never blocks
    completion. Heuristic-fallback CALLER verification belongs to WP3 acceptance, not WP2 [R3].
- `src/analysis/test_llm_client_tool.py` — mock urllib.request.urlopen with fake SSE byte
  stream; activation scenarios [B8]: happy path (delta+done), delta-ONLY stream (no done event),
  mixed multipart (two output_index keys, one done-only one delta-only), empty stream -> None,
  malformed JSON data lines skipped while rest parses, HTTPError -> None, URLError(connection
  refused) -> None, socket.timeout mid-read -> None returns without raise, trickle past
  deadline -> partial text returned, socket shut down (real local drip server, wall-clock
  bounded) [F1],
  disabled -> None with urlopen asserted NOT called.
- `src/analysis/keyword_tool.py` [B4 concretized]:
  - `normalize(text)` -> NFKC + casefold + collapse whitespace/punct (`re.sub(r"[^\w\s]", " ")`).
  - `tokens(text)` -> significant tokens: ASCII words len>=2 via `[a-z0-9]{2,}` with token
    boundaries, Hangul runs len>=2 via `[\uac00-\ud7a3]{2,}`, Kana/Han runs len>=2; minus
    static STOPWORDS frozenset (Korean particles/generic: 오늘, 이번, 영상, 공식, 발표, 뉴스,
    추천, 정리, full list in code; English: the/and/for/with/this/that/video/official/news/...).
  - `matches(anchor, text)` -> bool: compact substring hit with script-aware threshold [R6]:
    compact anchor (spaces stripped) must be len>=4 for ASCII/mixed, len>=3 for pure-Hangul
    (3-syllable entities like 손흥민); OR token rule: every anchor token present in text
    tokens, where ASCII tokens use boundary equality and HANGUL anchor tokens (len>=2) match
    by prefix (text token startswith anchor token, so 손흥민 matches 손흥민이) [R6].
    Tests: 손흥민 vs "손흥민이 해트트릭" positive; 카페 vs "카페인 효과" negative (prefix on
    anchor-token side only, anchor 카페 len 2 <3 compact rule, token 카페 vs 카페인 prefix — 
    counter-guard: prefix match requires anchor token len>=3 OR exact equality) [R6].
  - No character bigrams [B4]. Deterministic, pure functions.
- `src/analysis/aggregate_tool.py` — deterministic core:
  - `ensure_registered()` [B2][R7]: calls reels/threads/tiktok/x `register()` UNCONDITIONALLY
    (each register() is a plain idempotent _sources assignment — no flag, so a cleared
    registry is always repaired). Invoked at top of collect_snapshot. Test: call, clear
    accounts_tool._sources, call again -> sources present both times.
  - `collect_snapshot(country="KR", force=False, deadline=25)` [B1]: 7 channels (date EXCLUDED
    [B4] — derived from youtube+trends, would fabricate cross-platform amplification and
    duplicate cold fetches). Submit each channel fn to ThreadPoolExecutor(max_workers=7); use
    `concurrent.futures.wait(futs, timeout=remaining_deadline)`; completed futures collected in
    FIXED channel order; unfinished channels -> errors entry {channel, kind:"timeout"} (workers
    CONTINUE in background and warm the channel cache for the next refresh — documented
    behavior); executor created WITHOUT a with-block, explicit shutdown(wait=False) [R8].
    `force` propagates to every getter [B3]. Channel exceptions -> {channel, kind:"error"};
    embedded errors harvested [B3][R1]: trends returns a 4-tuple — errors at index 2;
    reels/x/threads return 5-tuples — errors at index 3.
    Blocked-future test hygiene [R8]: the never-completing fake getter blocks on an Event that
    the test SETS in finally, then joins/waits for the leaked worker so interpreter shutdown
    is clean.
  - Adapter contract [B3] — item = {platform, title, url, metric:int, ts:float|0}:
      trends:  get_trends(country, force)[0][:20]; title=keyword; url=first news url or
               google search url; metric=trafficValue; ts=item ts.
      youtube: get_videos("전체","week",False,force,country=country)[0][:20]; title;
               url=watch?v=id; metric=views; ts=0 (relative "published" text unusable).
      reels:   get_reels(force)[0][:20]; title; url; metric=views; ts=takenAt.
      x:       get_x_posts(force)[0] sorted by (views or likes) desc [:20]; title=text[:160];
               url; metric=views if views>0 else likes; ts=0 (createdAt is a str format).
      threads: get_threads_posts(force)[0] sorted by likes desc [:20]; title=text[:160]; url;
               metric=likes (views always 0 upstream); ts=createdAt.
      tiktok:  get_tiktok(force)[0][:20]; title; url; metric=views; ts=createdAt.
      ai_news: get_ai_data(force)[0]["news"][:30]; title; url=link; metric=0 (recency channel);
               ts=item ts.
  - `correlate(snapshot)` [B4]: anchor-based, no transitive unions. Anchors = trend keywords
    (primary) + fallback anchors: normalized tokens appearing in items of >=2 distinct
    platforms (exact token equality). A platform matches an anchor when keyword_tool.matches
    (anchor, item.title). Topic emitted ONLY with >=2 distinct platforms, except trend-anchored
    topics which may stand with 1 (they carry their own trafficValue signal) but get no
    amplification. score [R5] = sum over matched items of log10(metric+1) — the trend item
    itself IS one of the matched items (metric=trafficValue), so there is NO separate
    +log10(trafficValue+1) term (double-count removed) — times (1.0 + 0.5*(nplatforms-1)).
    Test includes an exact numeric score assertion on a fixed fixture [R5]. Deterministic
    order: sort key (-score, keyword); item lists sorted (platform, url).
  - History [B5]: path = os.path.join(settings.CONFIG_DIR, "analysis_history.json");
    `.gitignore` += `config/analysis_history.json`. Module-level threading.Lock guards the
    WHOLE read/append/prune/write transaction; write = tmp file + os.replace (atomic). Ring:
    last 48 entries {ts, country, topics:{keyword:score}}. Missing file -> empty history;
    corrupt JSON -> reset to empty (and overwrite on next write); write OSError -> analysis
    still returns (history skipped, error noted).
  - `velocity(topics, history, country, now)` [B6][R4]: history prefiltered to same-country
    entries (country is an explicit arg). baseline = most recent entry with ts <= now-1800 and
    ts >= now-86400. If none: velocity="insufficient" for all topics and
    baselineAvailable=False in the result envelope (no fake flat/new claims) [R4]. Else per
    topic: absent from baseline -> "new"; score > baseline*1.10 -> "rising"; score <
    baseline*0.90 -> "falling"; else "flat". Output includes elapsedSeconds +
    baselineAvailable=True. `now` and history ts injected in tests.
  - `analyze_heuristic(country, force)` -> {topics:[{keyword,title,platforms,score,velocity,
    items[:5]}], velocityBaseline:{available:bool, elapsedSeconds:int|null} (top-level, from
    velocity(); per-topic velocity strings stay on topics) [F3], briefing:[deterministic
    Korean lines naming top rising + top cross-platform topics], errors,
    generatedBy:"heuristic"}. Tests assert exact envelope for BOTH eligible-baseline and
    insufficient cases [F3].
- `src/analysis/test_aggregate_tool.py` — all channel getters mocked; activation scenarios [B8]:
  adapter mapping per channel (metric/url/ts rules incl. x views-vs-likes fallback and threads
  likes), fixed-order partial snapshot when one future never completes (blocked via Event +
  tiny deadline -> timeout error entry, others collected), one channel raising -> error entry +
  others aggregate, embedded errors harvested (trends fixture = 4-tuple (items, fetched_at,
  errors, cache_ttl); reels/x/threads fixtures = 5-tuples) [F2], force=True propagated to
  every getter (mock assert), ensure_registered with cleared _sources (getters callable, no
  KeyError), all channels empty -> topics=[] briefing still returned, correlation: anchor match
  across 2 platforms amplified vs single-platform trend topic not amplified, no-overlap items
  produce no fabricated topic, deterministic tie order, velocity: rising/falling/flat/new +
  no-baseline-within-window cases (injected ts), history: missing file, corrupt JSON reset,
  ring cap 48, concurrent writers (two threads x N writes -> file stays valid JSON, lock
  serializes), write OSError tolerated.

## Scope
IN: files above + .gitignore line + devlog/str_func/analysis.md FULL module doc with ALL
sections required by devlog/str_func/AGENTS.md (check its header for the exact section list
and length bar before writing; mirror the structure of an existing done doc e.g. date.md/
trends.md at comparable depth) [R9] + str_func/AGENTS.md index row + numbered plan doc
devlog/_plan/130_analysis-engine.md [B9]. OUT: main.py routes (WP3), index.html (WP4), any
external dep.

## Accept criteria
- Suite green, zero live network in tests (activation scenario per branch named in tests) —
  the ONLY mandatory gate [R3].
- Live smoke: conditional on proxy health probe; recorded either way, never gating [R3].
- analyze_heuristic works with proxy down (no LLM involvement in WP2 heuristics).
