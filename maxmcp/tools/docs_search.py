"""Local MAXScript reference search for external MCP clients.

Python-only (no native handler), so the in-Max chat window cannot call it; that window
gets the same knowledge through the retrieval proxy in maxmcp.docsearch.proxy.
"""

import json
from pathlib import Path

from ..docsearch import DEFAULT_INDEX_PATH, DocIndex, OllamaEmbedder, format_context
from ..server import mcp

_index_cache: dict[str, DocIndex] = {}


def _load_index(path: Path) -> DocIndex:
    key = str(path)
    if key not in _index_cache:
        _index_cache[key] = DocIndex.load(path)
    return _index_cache[key]


@mcp.tool()
def search_maxscript_docs(query: str, top_k: int = 4, max_chars: int = 6000) -> str:
    """Search the local MAXScript / 3ds Max reference index for API names, signatures, and patterns.

    Use when: about to write execute_maxscript for an unfamiliar API (Edit Poly, materials,
    controllers, rendering), or right after a MAXScript error names an unknown property or function.
    Not when: the live scene can answer — introspect_class / inspect_object read the real API surface
    of your exact 3ds Max version and plugins.
    """
    query = (query or "").strip()
    if not query:
        return json.dumps({"status": "error", "error": "provide a query"})
    index_path = DEFAULT_INDEX_PATH
    if not index_path.exists():
        return json.dumps(
            {
                "status": "error",
                "error": f"reference index not built at {index_path}",
                "hint": {"message": "Run: uv run python -m maxmcp.docsearch build"},
            }
        )
    try:
        index = _load_index(index_path)
        embedder = OllamaEmbedder(model=index.model)
        hits = index.search(embedder([query])[0], query_text=query, top_k=max(1, min(top_k, 10)))
    except Exception as exc:  # Ollama down, corrupt index, ...
        return json.dumps({"status": "error", "error": str(exc)})
    return json.dumps(
        {
            "status": "ok",
            "query": query,
            "hits": [
                {"title": chunk.title, "source": chunk.source, "score": round(score, 3)}
                for score, chunk in hits
            ],
            "context": format_context(hits, max_chars=max_chars),
        }
    )
