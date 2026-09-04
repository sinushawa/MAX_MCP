"""OpenAI-compatible retrieval proxy for the in-Max chat window.

The native chat cannot call Python tools, but its ``base_url`` is configurable. Point
it at this proxy instead of Ollama. Every ``/v1/chat/completions`` request gets the
latest user question (and any recent MAXScript error) embedded, the closest reference
chunks are prepended to the system message, and the request is forwarded unchanged
otherwise. The upstream response is returned verbatim.

    uv run python -m maxmcp.docsearch serve --port 11435

    [llm]
    base_url = http://localhost:11435/v1
"""

from __future__ import annotations

import json
import logging
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Sequence

from .index import (
    DEFAULT_INDEX_PATH,
    DEFAULT_OLLAMA_URL,
    DocIndex,
    Embedder,
    OllamaEmbedder,
    format_context,
)

log = logging.getLogger("maxmcp.docsearch.proxy")

CONTEXT_HEADER = "## MAXScript reference (retrieved for this turn)"
CONTEXT_FOOTER = (
    "Use exact names from the reference above. If it does not cover the API you need, "
    "call introspect_class or inspect_object before guessing property names."
)
_ERROR_MARKERS = ("__MCP_MS_ERR__", "MAXScriptError", "Unknown property", "No \"", "-- ")


def _message_text(message: dict) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            part.get("text", "") for part in content if isinstance(part, dict) and part.get("type") == "text"
        )
    return ""


def build_query(messages: Sequence[dict], max_chars: int = 1500) -> str:
    """Latest user request plus the most recent MAXScript failure, if any.

    After a failed ``execute_maxscript`` the model's next turn is usually a retry, so
    the failing script and its error are the most useful retrieval signal available.
    """
    user_text = ""
    error_text = ""
    failed_code = ""
    for message in reversed(messages):
        role = message.get("role")
        if role == "user" and not user_text:
            user_text = _message_text(message)
        elif role == "tool" and not error_text:
            text = _message_text(message)
            if any(marker in text for marker in _ERROR_MARKERS):
                error_text = text
        elif role == "assistant" and error_text and not failed_code:
            for call in message.get("tool_calls") or []:
                function = call.get("function") or {}
                if function.get("name") == "execute_maxscript":
                    try:
                        args = json.loads(function.get("arguments") or "{}")
                    except ValueError:
                        args = {}
                    failed_code = str(args.get("code") or args.get("command") or "")
                    break
        if user_text and (error_text or role == "user"):
            if not error_text:
                break
            if failed_code:
                break
    query = "\n".join(part for part in (user_text, failed_code, error_text) if part)
    return query[:max_chars]


def inject_context(messages: list[dict], context: str) -> list[dict]:
    """Return a copy of messages with the context appended to the system message."""
    if not context:
        return list(messages)
    block = f"{CONTEXT_HEADER}\n{context}\n\n{CONTEXT_FOOTER}"
    updated = [dict(message) for message in messages]
    if updated and updated[0].get("role") == "system" and isinstance(updated[0].get("content"), str):
        updated[0]["content"] = f"{updated[0]['content'].rstrip()}\n\n{block}"
    else:
        updated.insert(0, {"role": "system", "content": block})
    return updated


def augment_request(
    body: dict,
    index: DocIndex,
    embedder: Embedder,
    top_k: int = 4,
    max_context_chars: int = 6000,
) -> tuple[dict, list[tuple[float, Any]]]:
    messages = body.get("messages")
    if not isinstance(messages, list) or not messages:
        return body, []
    query = build_query(messages)
    if not query.strip():
        return body, []
    vector = embedder([query])[0]
    hits = index.search(vector, query_text=query, top_k=top_k)
    context = format_context(hits, max_chars=max_context_chars)
    augmented = dict(body)
    augmented["messages"] = inject_context(messages, context)
    return augmented, hits


class RetrievalProxy:
    def __init__(
        self,
        index: DocIndex,
        embedder: Embedder,
        upstream: str = DEFAULT_OLLAMA_URL,
        top_k: int = 4,
        max_context_chars: int = 6000,
        upstream_timeout: float = 900.0,
    ) -> None:
        self.index = index
        self.embedder = embedder
        self.upstream = upstream.rstrip("/")
        self.top_k = top_k
        self.max_context_chars = max_context_chars
        self.upstream_timeout = upstream_timeout

    def forward(self, method: str, path: str, body: bytes | None, headers: dict) -> tuple[int, bytes, str]:
        request = urllib.request.Request(f"{self.upstream}{path}", data=body, method=method)
        for key in ("Content-Type", "Authorization", "Accept"):
            if key in headers:
                request.add_header(key, headers[key])
        try:
            with urllib.request.urlopen(request, timeout=self.upstream_timeout) as response:
                return response.status, response.read(), response.headers.get("Content-Type", "application/json")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read(), exc.headers.get("Content-Type", "application/json")
        except urllib.error.URLError as exc:
            payload = json.dumps({"error": {"message": f"upstream {self.upstream} unreachable: {exc.reason}"}})
            return 502, payload.encode("utf-8"), "application/json"

    def handle_chat(self, raw: bytes, headers: dict) -> tuple[int, bytes, str]:
        try:
            body = json.loads(raw.decode("utf-8"))
        except ValueError:
            return self.forward("POST", "/v1/chat/completions", raw, headers)
        try:
            augmented, hits = augment_request(
                body, self.index, self.embedder, top_k=self.top_k, max_context_chars=self.max_context_chars
            )
        except Exception as exc:  # retrieval must never break the chat
            log.warning("retrieval skipped: %s", exc)
            augmented, hits = body, []
        if hits:
            log.info("retrieved: %s", "; ".join(f"{chunk.title} ({score:.2f})" for score, chunk in hits))
        else:
            log.info("no retrieval for this request")
        data = json.dumps(augmented).encode("utf-8")
        return self.forward("POST", "/v1/chat/completions", data, headers)


def make_handler(proxy: RetrievalProxy):
    class Handler(BaseHTTPRequestHandler):
        server_version = "maxmcp-docsearch-proxy/1.0"

        def _send(self, status: int, payload: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def _read_body(self) -> bytes:
            length = int(self.headers.get("Content-Length") or 0)
            return self.rfile.read(length) if length else b""

        def do_POST(self) -> None:  # noqa: N802 (http.server naming)
            raw = self._read_body()
            headers = dict(self.headers.items())
            if self.path.rstrip("/").endswith("/chat/completions"):
                status, payload, content_type = proxy.handle_chat(raw, headers)
            else:
                status, payload, content_type = proxy.forward("POST", self.path, raw, headers)
            self._send(status, payload, content_type)

        def do_GET(self) -> None:  # noqa: N802
            if self.path in ("/", "/health"):
                info = {"ok": True, "chunks": len(proxy.index), "upstream": proxy.upstream, "top_k": proxy.top_k}
                self._send(200, json.dumps(info).encode("utf-8"), "application/json")
                return
            status, payload, content_type = proxy.forward("GET", self.path, None, dict(self.headers.items()))
            self._send(status, payload, content_type)

        def log_message(self, format: str, *args) -> None:  # quieter than the default
            log.debug("%s - %s", self.address_string(), format % args)

    return Handler


def serve(
    host: str = "127.0.0.1",
    port: int = 11435,
    upstream: str = DEFAULT_OLLAMA_URL,
    index_path: Path = DEFAULT_INDEX_PATH,
    top_k: int = 4,
    max_context_chars: int = 6000,
    embedder: Embedder | None = None,
) -> ThreadingHTTPServer:
    index = DocIndex.load(index_path)
    proxy = RetrievalProxy(
        index,
        embedder or OllamaEmbedder(model=index.model, base_url=upstream),
        upstream=upstream,
        top_k=top_k,
        max_context_chars=max_context_chars,
    )
    server = ThreadingHTTPServer((host, port), make_handler(proxy))
    server.daemon_threads = True
    log.info("docs proxy on http://%s:%d -> %s (%d chunks, top_k=%d)", host, server.server_port, upstream, len(index), top_k)
    return server


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Retrieval proxy between the in-Max chat and Ollama")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=11435)
    parser.add_argument("--upstream", default=DEFAULT_OLLAMA_URL)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX_PATH)
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument("--max-context-chars", type=int, default=6000)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", stream=sys.stderr)
    if not args.index.exists():
        print(f"index not found at {args.index}; run: uv run python -m maxmcp.docsearch build", file=sys.stderr)
        return 1
    server = serve(args.host, args.port, args.upstream, args.index, args.top_k, args.max_context_chars)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
