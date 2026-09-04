"""Local retrieval over the bundled MAXScript references.

Two consumers share one index:

- ``search_maxscript_docs`` MCP tool (external clients such as Claude Code).
- ``maxmcp.docsearch.proxy`` — an OpenAI-compatible proxy that sits between the in-Max
  chat window and Ollama and prepends retrieved reference chunks to the system prompt.

Build the index once with ``uv run python -m maxmcp.docsearch build``.
"""

from .index import (
    DEFAULT_EMBED_MODEL,
    DEFAULT_INDEX_PATH,
    DEFAULT_OLLAMA_URL,
    DocIndex,
    OllamaEmbedder,
    build_index,
    chunk_markdown,
    default_sources,
    format_context,
)

__all__ = [
    "DEFAULT_EMBED_MODEL",
    "DEFAULT_INDEX_PATH",
    "DEFAULT_OLLAMA_URL",
    "DocIndex",
    "OllamaEmbedder",
    "build_index",
    "chunk_markdown",
    "default_sources",
    "format_context",
]
