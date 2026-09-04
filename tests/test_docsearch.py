"""Reference index, retrieval proxy, and docs search tool."""

from __future__ import annotations

import json
import re
import threading
import unittest
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory

from maxmcp.docsearch.index import Chunk, DocIndex, build_index, chunk_markdown, format_context
from maxmcp.docsearch.proxy import (
    CONTEXT_HEADER,
    RetrievalProxy,
    augment_request,
    build_query,
    inject_context,
    make_handler,
)

SAMPLE_MD = """# Mesh and poly ops

Intro paragraph.

## Extrude faces

Use polyop.extrudeFaces on an Editable_Poly. With an Edit_Poly modifier call
SetOperation #ExtrudeFace then Commit.

```maxscript
# not a heading inside a fence
polyop.extrudeFaces $ faces 5.0
```

## Bevel

Use polyop.bevelFaces for bevels.
"""

VOCAB = ("extrude", "bevel", "material", "spline", "poly", "vray")


def fake_embed(texts):
    """Deterministic bag-of-words vectors so ranking is predictable."""
    vectors = []
    for text in texts:
        lowered = text.lower()
        vectors.append([float(lowered.count(word)) for word in VOCAB] + [1.0])
    return vectors


class ChunkingTests(unittest.TestCase):
    def test_chunks_follow_headings_and_ignore_fenced_hashes(self) -> None:
        chunks = chunk_markdown(SAMPLE_MD, "mesh.md")
        titles = [chunk.title for chunk in chunks]
        self.assertEqual(
            titles,
            [
                "mesh > Mesh and poly ops",
                "mesh > Mesh and poly ops > Extrude faces",
                "mesh > Mesh and poly ops > Bevel",
            ],
        )
        self.assertIn("polyop.extrudeFaces $ faces 5.0", chunks[1].text)
        self.assertTrue(all(chunk.id.startswith("mesh#") for chunk in chunks))

    def test_long_sections_split_under_the_limit(self) -> None:
        text = "# T\n\n" + "\n\n".join(f"paragraph {i} " + "x" * 300 for i in range(10))
        chunks = chunk_markdown(text, "long.md", max_chars=700)
        self.assertGreater(len(chunks), 3)
        self.assertTrue(all(len(chunk.text) <= 700 for chunk in chunks))
        self.assertTrue(all(chunk.title == "long > T" for chunk in chunks))


class IndexTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        source = Path(self.tmp.name) / "mesh.md"
        source.write_text(SAMPLE_MD, encoding="utf-8")
        self.index = build_index([source], fake_embed, model="fake")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_search_ranks_matching_chunk_first(self) -> None:
        query = "how do I bevel faces"
        hits = self.index.search(fake_embed([query])[0], query_text=query, top_k=2)
        self.assertEqual(hits[0][1].title, "mesh > Mesh and poly ops > Bevel")

    def test_identifier_bonus_prefers_exact_api_names(self) -> None:
        # Both chunks mention "poly"; the exact identifier should decide.
        query = "polyop.extrudeFaces signature"
        hits = self.index.search(fake_embed([query])[0], query_text=query, top_k=1)
        self.assertIn("Extrude faces", hits[0][1].title)

    def test_save_and_load_round_trip(self) -> None:
        path = Path(self.tmp.name) / "index.json"
        self.index.save(path)
        loaded = DocIndex.load(path)
        self.assertEqual(len(loaded), len(self.index))
        self.assertEqual(loaded.model, "fake")
        self.assertEqual([c.title for c in loaded.chunks], [c.title for c in self.index.chunks])

    def test_format_context_respects_budget(self) -> None:
        hits = [(0.9, Chunk("a#0", "a.md", "A", "x" * 500)), (0.8, Chunk("a#1", "a.md", "B", "y" * 500))]
        text = format_context(hits, max_chars=600)
        self.assertIn("### A", text)
        self.assertNotIn("### B", text)


class QueryAndInjectionTests(unittest.TestCase):
    def test_build_query_uses_last_user_message(self) -> None:
        messages = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "old"},
            {"role": "assistant", "content": "ok"},
            {"role": "user", "content": "extrude the current face by 5"},
        ]
        self.assertEqual(build_query(messages), "extrude the current face by 5")

    def test_build_query_adds_failed_script_and_error(self) -> None:
        messages = [
            {"role": "user", "content": "extrude the current face by 5"},
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "1",
                        "type": "function",
                        "function": {"name": "execute_maxscript", "arguments": json.dumps({"code": "$.selectionLevel = #face"})},
                    }
                ],
            },
            {"role": "tool", "tool_call_id": "1", "content": '__MCP_MS_ERR__:-- Unknown property: "selectionLevel"'},
        ]
        query = build_query(messages)
        self.assertIn("extrude the current face by 5", query)
        self.assertIn("$.selectionLevel = #face", query)
        self.assertIn("Unknown property", query)

    def test_inject_context_appends_to_system_or_creates_one(self) -> None:
        with_system = inject_context([{"role": "system", "content": "base"}, {"role": "user", "content": "q"}], "CTX")
        self.assertTrue(with_system[0]["content"].startswith("base"))
        self.assertIn(CONTEXT_HEADER, with_system[0]["content"])
        self.assertIn("CTX", with_system[0]["content"])

        without = inject_context([{"role": "user", "content": "q"}], "CTX")
        self.assertEqual(without[0]["role"], "system")
        self.assertEqual(without[1]["role"], "user")

        self.assertEqual(inject_context([{"role": "user", "content": "q"}], ""), [{"role": "user", "content": "q"}])

    def test_augment_request_leaves_other_fields_alone(self) -> None:
        index = build_index([_write_sample()], fake_embed, model="fake")
        body = {"model": "m", "temperature": 0.2, "tools": [{"x": 1}], "messages": [{"role": "user", "content": "bevel faces"}]}
        augmented, hits = augment_request(body, index, fake_embed, top_k=1)
        self.assertEqual(augmented["model"], "m")
        self.assertEqual(augmented["tools"], [{"x": 1}])
        self.assertEqual(len(hits), 1)
        self.assertIn("Bevel", augmented["messages"][0]["content"])
        self.assertEqual(body["messages"][0]["role"], "user")  # input not mutated


def _write_sample() -> Path:
    tmp = TemporaryDirectory()
    path = Path(tmp.name) / "mesh.md"
    path.write_text(SAMPLE_MD, encoding="utf-8")
    _write_sample.keep = getattr(_write_sample, "keep", []) + [tmp]  # type: ignore[attr-defined]
    return path


class _EchoUpstream(BaseHTTPRequestHandler):
    """Fake Ollama: records the request body and returns a canned completion."""

    received: list[dict] = []

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(length).decode("utf-8"))
        _EchoUpstream.received.append({"path": self.path, "body": body, "auth": self.headers.get("Authorization")})
        payload = json.dumps({"choices": [{"message": {"role": "assistant", "content": "echo"}}]}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        payload = b'{"data": []}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args) -> None:
        pass


class ProxyEndToEndTests(unittest.TestCase):
    def setUp(self) -> None:
        _EchoUpstream.received = []
        self.upstream = HTTPServer(("127.0.0.1", 0), _EchoUpstream)
        threading.Thread(target=self.upstream.serve_forever, daemon=True).start()
        index = build_index([_write_sample()], fake_embed, model="fake")
        proxy = RetrievalProxy(index, fake_embed, upstream=f"http://127.0.0.1:{self.upstream.server_port}", top_k=1)
        self.proxy = HTTPServer(("127.0.0.1", 0), make_handler(proxy))
        threading.Thread(target=self.proxy.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.proxy.server_port}"

    def tearDown(self) -> None:
        self.proxy.shutdown()
        self.proxy.server_close()
        self.upstream.shutdown()
        self.upstream.server_close()

    def _post(self, path: str, body: dict) -> dict:
        request = urllib.request.Request(
            self.base + path,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": "Bearer ollama"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))

    def test_chat_completion_is_augmented_and_forwarded(self) -> None:
        reply = self._post(
            "/v1/chat/completions",
            {"model": "m", "messages": [{"role": "system", "content": "base"}, {"role": "user", "content": "extrude faces"}]},
        )
        self.assertEqual(reply["choices"][0]["message"]["content"], "echo")
        seen = _EchoUpstream.received[-1]
        self.assertEqual(seen["path"], "/v1/chat/completions")
        self.assertEqual(seen["auth"], "Bearer ollama")
        system = seen["body"]["messages"][0]["content"]
        self.assertTrue(system.startswith("base"))
        self.assertIn(CONTEXT_HEADER, system)
        self.assertIn("polyop.extrudeFaces", system)

    def test_health_and_passthrough(self) -> None:
        with urllib.request.urlopen(self.base + "/health", timeout=10) as response:
            health = json.loads(response.read().decode("utf-8"))
        self.assertTrue(health["ok"])
        self.assertGreater(health["chunks"], 0)
        with urllib.request.urlopen(self.base + "/v1/models", timeout=10) as response:
            self.assertEqual(json.loads(response.read().decode("utf-8")), {"data": []})


class HintRuleTests(unittest.TestCase):
    def test_poly_operations_suggest_docs_search(self) -> None:
        from maxmcp.helpers.error_hints import suggest_tools_for_maxscript

        for script in (
            "$.selectionLevel = #face",
            "subobjectLevel = 4",
            "polyop.extrudeFaces $ #{1} 5.0",
            "$.modifiers[#Edit_Poly].SetOperation #ExtrudeFace",
        ):
            with self.subTest(script=script):
                self.assertIn("search_maxscript_docs", suggest_tools_for_maxscript(script))


class RegistryTests(unittest.TestCase):
    def test_docs_search_is_a_core_module_everywhere(self) -> None:
        import maxmcp.server as server
        from maxmcp.tool_discovery import TOOLSET_SPECS

        self.assertIn("docs_search", server.CORE_TOOL_MODULES)
        self.assertTrue(any("docs_search" in spec.modules for spec in TOOLSET_SPECS))
        source = (Path(__file__).resolve().parent.parent / "maxscript" / "mcp_settings.ms").read_text(encoding="utf-8")
        self.assertIn('#("docs_search",', source)


if __name__ == "__main__":
    unittest.main()
