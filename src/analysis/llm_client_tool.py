"""Small stdlib client for streamed Responses API completions."""

import http.client
import json
import os
import socket
import threading
import urllib.parse


DEFAULT_BASE_URL = "http://127.0.0.1:10100/v1"
DEFAULT_MODEL = "cursor/gpt-5.6-luna"


def is_enabled() -> bool:
    return os.environ.get("TREND_ANALYSIS_ENABLED", "1") != "0"


def _shutdown_socket(connection: http.client.HTTPConnection) -> None:
    sock = connection.sock
    if sock is None:
        return

    try:
        if sock.fileno() < 0:
            return
        sock.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass


def _assemble_text(
    deltas: dict[tuple[int, int], list[str]],
    done_text: dict[tuple[int, int], str],
) -> str | None:
    parts = []
    for key in sorted(set(deltas) | set(done_text)):
        if key in done_text:
            parts.append(done_text[key])
        else:
            parts.append("".join(deltas[key]))
    return "".join(parts) or None


def _read_sse(response: http.client.HTTPResponse) -> str | None:
    deltas = {}
    done_text = {}

    try:
        while True:
            raw_line = response.readline()
            if not raw_line:
                break

            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line or line.startswith(":") or not line.startswith("data:"):
                continue

            data = line[5:].lstrip()
            if data == "[DONE]":
                continue

            try:
                event = json.loads(data)
            except json.JSONDecodeError:
                continue

            output_index = event.get("output_index", 0)
            content_index = event.get("content_index", 0)
            if not isinstance(output_index, int) or not isinstance(content_index, int):
                continue
            key = (output_index, content_index)

            if event.get("type") == "response.output_text.delta":
                delta = event.get("delta")
                if isinstance(delta, str):
                    deltas.setdefault(key, []).append(delta)
            elif event.get("type") == "response.output_text.done":
                text = event.get("text")
                if isinstance(text, str):
                    done_text[key] = text
    except OSError:
        pass

    return _assemble_text(deltas, done_text)


def complete(
    prompt: str,
    system: str | None = None,
    timeout: float = 15,
    deadline: float = 120,
) -> str | None:
    if not is_enabled():
        return None

    base_url = os.environ.get("TREND_ANALYSIS_BASE_URL", DEFAULT_BASE_URL)
    model = os.environ.get("TREND_ANALYSIS_MODEL", DEFAULT_MODEL)
    payload_input = []
    if system:
        payload_input.append(
            {
                "role": "system",
                "content": [{"type": "input_text", "text": system}],
            }
        )
    payload_input.append(
        {
            "role": "user",
            "content": [{"type": "input_text", "text": prompt}],
        }
    )
    body = json.dumps(
        {
            "model": model,
            "store": False,
            "stream": True,
            "input": payload_input,
        }
    )

    try:
        parsed = urllib.parse.urlsplit(base_url)
        if parsed.scheme != "http" or not parsed.hostname:
            return None
        path_prefix = parsed.path.rstrip("/")
        target = path_prefix + "/responses"
        connection = http.client.HTTPConnection(
            parsed.hostname, parsed.port, timeout=timeout
        )
    except ValueError:
        return None

    watchdog = threading.Timer(deadline, _shutdown_socket, args=(connection,))
    watchdog.daemon = True
    watchdog.start()
    try:
        connection.connect()
        connection.request(
            "POST",
            target,
            body=body,
            headers={"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        if response.status != 200:
            return None
        return _read_sse(response)
    except (OSError, http.client.HTTPException):
        return None
    finally:
        watchdog.cancel()
        connection.close()
