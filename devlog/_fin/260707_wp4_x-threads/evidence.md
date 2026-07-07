# WP4 x_twitter + threads Evidence Receipt

Hook attempt: 3 of 3
Timestamp: 20260707-054531
Workspace: `/Users/jun/Developer/new/700_projects/trend-viewer`

## Judgement

PASS. I re-ran the relevant checks and smoke commands. Compileall passed, unittest
passed, account mutation endpoints returned 200 and were cleaned up, `/api/x` and
`/api/threads` returned the expected response shape, and `STUB_PATHS` contains only
`/api/ai` and `/api/oembed`.

## Outputs

### compileall

```bash
python3 -m compileall -q src
```

```text
<no output, exit 0>
```

### unittest

```bash
python3 -m unittest discover -s src -p "test_*.py" -t src
```

```text
.....................................
----------------------------------------------------------------------
Ran 37 tests in 0.012s

OK
```

### server start

```bash
python3 src/main.py
```

```text
트렌드 뷰어 실행 중: http://localhost:8779
```

### X account add

```bash
curl -s -w '\n%{http_code}\n' -X POST localhost:8779/api/x/accounts -d '{"action":"add","username":"test"}'
```

```text
{"accounts": ["OpenAI", "runwayml", "Kling_ai", "GoogleDeepMind", "midjourney", "LumaLabsAI", "pika_labs", "heygen_com", "elevenlabsio", "AIatMeta", "test"]}
200
```

### Threads account add

```bash
curl -s -w '\n%{http_code}\n' -X POST localhost:8779/api/threads/accounts -d '{"action":"add","username":"@Test"}'
```

```text
{"accounts": ["openai", "runway", "google", "meta.ai", "zuck", "test"]}
200
```

### X account cleanup

```bash
curl -s -X POST localhost:8779/api/x/accounts -d '{"action":"remove","username":"test"}'
```

```text
{"accounts": ["OpenAI", "runwayml", "Kling_ai", "GoogleDeepMind", "midjourney", "LumaLabsAI", "pika_labs", "heygen_com", "elevenlabsio", "AIatMeta"]}
```

### Threads account cleanup

```bash
curl -s -X POST localhost:8779/api/threads/accounts -d '{"action":"remove","username":"test"}'
```

```text
{"accounts": ["openai", "runway", "google", "meta.ai", "zuck"]}
```

### X endpoint shape

```bash
curl -s localhost:8779/api/x | python3 -c "import json,sys;d=json.load(sys.stdin);print(f'x-posts:{len(d.get(\"posts\",[]))} keys:{sorted(d.keys())}')"
```

```text
x-posts:0 keys:['accounts', 'fetchedAt', 'posts']
```

### Threads endpoint shape

```bash
curl -s localhost:8779/api/threads | python3 -c "import json,sys;d=json.load(sys.stdin);print(f'th-posts:{len(d.get(\"posts\",[]))} keys:{sorted(d.keys())}')"
```

```text
th-posts:0 keys:['accounts', 'fetchedAt', 'posts']
```

### STUB_PATHS literal check

```bash
python3 - <<'PY'
import ast
from pathlib import Path
mod = ast.parse(Path('src/main.py').read_text())
for node in mod.body:
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == 'STUB_PATHS':
                print(sorted(ast.literal_eval(node.value)))
PY
```

```text
['/api/ai', '/api/oembed']
```

### server stop

```text
[05:45:07] "POST /api/x/accounts HTTP/1.1" 200 -
[05:45:07] "POST /api/threads/accounts HTTP/1.1" 200 -
[05:45:12] "POST /api/x/accounts HTTP/1.1" 200 -
[05:45:12] "POST /api/threads/accounts HTTP/1.1" 200 -
[05:45:23] "GET /api/threads HTTP/1.1" 200 -
[05:45:23] "GET /api/x HTTP/1.1" 200 -
KeyboardInterrupt
```

## Notes

- Empty live post arrays are accepted by the WP4 plan. Unit fixtures cover parser,
  fallback, doc-id, dual app-id, UA header, and cache contracts.
- Smoke account changes were removed before finishing.
