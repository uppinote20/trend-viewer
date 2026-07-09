import io
import json
import os
import socket
import threading
import time
import unittest
from unittest import mock

from analysis import llm_client_tool


class _Response:
    def __init__(self, lines=b"", status=200):
        self.status = status
        self._stream = io.BytesIO(lines)

    def readline(self):
        return self._stream.readline()


class _InterruptedResponse:
    def __init__(self, lines):
        self.status = 200
        self._lines = iter(lines)

    def readline(self):
        line = next(self._lines)
        if isinstance(line, BaseException):
            raise line
        return line


def _event(event):
    return b"data: " + json.dumps(event).encode() + b"\n\n"


class LlmClientToolTest(unittest.TestCase):
    def _complete_with_response(self, response, **kwargs):
        connection = mock.Mock()
        connection.sock = None
        connection.getresponse.return_value = response
        env = {
            "TREND_ANALYSIS_ENABLED": "1",
            "TREND_ANALYSIS_BASE_URL": "http://proxy.test:10100/v1",
            "TREND_ANALYSIS_MODEL": "test/model",
        }
        with (
            mock.patch.dict(os.environ, env),
            mock.patch.object(
                llm_client_tool.http.client,
                "HTTPConnection",
                return_value=connection,
            ),
        ):
            result = llm_client_tool.complete("hello", system="be brief", **kwargs)
        return result, connection

    def test_happy_path_prefers_done_text_over_deltas(self):
        stream = b"".join(
            [
                b": keepalive\n\n",
                b"event: response.output_text.delta\n",
                _event(
                    {
                        "type": "response.output_text.delta",
                        "output_index": 0,
                        "content_index": 0,
                        "delta": "draft ",
                    }
                ),
                _event(
                    {
                        "type": "response.output_text.done",
                        "output_index": 0,
                        "content_index": 0,
                        "text": "final text",
                    }
                ),
                b"data: [DONE]\n\n",
            ]
        )

        result, connection = self._complete_with_response(_Response(stream))

        self.assertEqual(result, "final text")
        connection.connect.assert_called_once_with()
        request = connection.request.call_args
        self.assertEqual(request.args[:2], ("POST", "/v1/responses"))
        self.assertEqual(request.kwargs["headers"], {"Content-Type": "application/json"})
        payload = json.loads(request.kwargs["body"])
        self.assertEqual(
            payload,
            {
                "model": "test/model",
                "store": False,
                "stream": True,
                "input": [
                    {
                        "role": "system",
                        "content": [{"type": "input_text", "text": "be brief"}],
                    },
                    {
                        "role": "user",
                        "content": [{"type": "input_text", "text": "hello"}],
                    },
                ],
            },
        )
        self.assertNotIn("max_output_tokens", payload)

    def test_delta_only_stream_joins_deltas(self):
        stream = _event(
            {
                "type": "response.output_text.delta",
                "output_index": 0,
                "content_index": 0,
                "delta": "hello ",
            }
        ) + _event(
            {
                "type": "response.output_text.delta",
                "output_index": 0,
                "content_index": 0,
                "delta": "world",
            }
        )

        result, _ = self._complete_with_response(_Response(stream))

        self.assertEqual(result, "hello world")

    def test_mixed_multipart_stream_is_sorted_by_output_index(self):
        stream = _event(
            {
                "type": "response.output_text.delta",
                "output_index": 1,
                "content_index": 0,
                "delta": "second",
            }
        ) + _event(
            {
                "type": "response.output_text.done",
                "output_index": 0,
                "content_index": 0,
                "text": "first ",
            }
        )

        result, _ = self._complete_with_response(_Response(stream))

        self.assertEqual(result, "first second")

    def test_empty_stream_returns_none(self):
        result, _ = self._complete_with_response(_Response())

        self.assertIsNone(result)

    def test_malformed_json_line_is_skipped(self):
        stream = b"data: {not json}\n\n" + _event(
            {
                "type": "response.output_text.done",
                "output_index": 0,
                "content_index": 0,
                "text": "still works",
            }
        )

        result, _ = self._complete_with_response(_Response(stream))

        self.assertEqual(result, "still works")

    def test_non_200_status_returns_none(self):
        result, _ = self._complete_with_response(_Response(status=503))

        self.assertIsNone(result)

    def test_connection_refused_returns_none_quickly(self):
        probe = socket.socket()
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
        probe.close()
        env = {
            "TREND_ANALYSIS_ENABLED": "1",
            "TREND_ANALYSIS_BASE_URL": f"http://127.0.0.1:{port}/v1",
        }

        started = time.monotonic()
        with mock.patch.dict(os.environ, env):
            result = llm_client_tool.complete("hello", timeout=0.2, deadline=1)
        elapsed = time.monotonic() - started

        self.assertIsNone(result)
        self.assertLess(elapsed, 3)

    def test_inactivity_timeout_returns_partial_text_without_raising(self):
        partial = _event(
            {
                "type": "response.output_text.delta",
                "output_index": 0,
                "content_index": 0,
                "delta": "partial",
            }
        )
        cases = [
            ([partial, socket.timeout("inactivity timeout")], "partial"),
            ([socket.timeout("inactivity timeout")], None),
        ]
        for lines, expected in cases:
            with self.subTest(expected=expected):
                result, _ = self._complete_with_response(
                    _InterruptedResponse(lines)
                )

                self.assertEqual(result, expected)

    def test_trickle_without_newline_is_stopped_by_total_deadline(self):
        listener = socket.socket()
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        port = listener.getsockname()[1]
        release = threading.Event()
        server_done = threading.Event()

        def serve_drip():
            client = None
            try:
                listener.settimeout(5)
                client, _ = listener.accept()
                request = b""
                while b"\r\n\r\n" not in request:
                    chunk = client.recv(4096)
                    if not chunk:
                        return
                    request += chunk
                client.sendall(
                    b"HTTP/1.1 200 OK\r\n"
                    b"Content-Type: text/event-stream\r\n"
                    b"Transfer-Encoding: chunked\r\n\r\n"
                )
                while not release.is_set():
                    try:
                        client.sendall(b"1\r\nx\r\n")
                    except OSError:
                        break
                    release.wait(0.05)
            except OSError:
                pass
            finally:
                if client is not None:
                    client.close()
                listener.close()
                server_done.set()

        server = threading.Thread(target=serve_drip)
        server.start()
        env = {
            "TREND_ANALYSIS_ENABLED": "1",
            "TREND_ANALYSIS_BASE_URL": f"http://127.0.0.1:{port}/v1",
        }

        started = time.monotonic()
        try:
            with mock.patch.dict(os.environ, env):
                result = llm_client_tool.complete("hello", timeout=5, deadline=1)
            elapsed = time.monotonic() - started
        finally:
            release.set()
            server.join(timeout=3)

        self.assertIsNone(result)
        self.assertLess(elapsed, 4)
        self.assertTrue(server_done.is_set())
        self.assertFalse(server.is_alive())

    def test_disabled_returns_none_without_constructing_connection(self):
        with (
            mock.patch.dict(os.environ, {"TREND_ANALYSIS_ENABLED": "0"}),
            mock.patch.object(
                llm_client_tool.http.client, "HTTPConnection"
            ) as connection_class,
        ):
            result = llm_client_tool.complete("hello")

        self.assertIsNone(result)
        connection_class.assert_not_called()


if __name__ == "__main__":
    unittest.main()
