"""CLI: build the reference index, query it, or run the retrieval proxy.

    uv run python -m maxmcp.docsearch build [--extra DIR_OR_FILE ...] [--model nomic-embed-text]
    uv run python -m maxmcp.docsearch search "extrude a face on an Edit Poly modifier" [--top 4]
    uv run python -m maxmcp.docsearch serve [--port 11435] [--upstream http://localhost:11434]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .index import (
    DEFAULT_EMBED_MODEL,
    DEFAULT_INDEX_PATH,
    DEFAULT_OLLAMA_URL,
    DocIndex,
    OllamaEmbedder,
    build_index,
    default_sources,
    format_context,
)
from .proxy import main as proxy_main


def cmd_build(args: argparse.Namespace) -> int:
    sources = default_sources(args.extra)
    print(f"indexing {len(sources)} files with {args.model} via {args.ollama}")
    embedder = OllamaEmbedder(model=args.model, base_url=args.ollama)
    index = build_index(sources, embedder, model=args.model, max_chars=args.max_chars)
    path = index.save(args.index)
    print(f"wrote {len(index)} chunks -> {path}")
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    if not args.index.exists():
        print(f"index not found at {args.index}; run the build command first", file=sys.stderr)
        return 1
    index = DocIndex.load(args.index)
    embedder = OllamaEmbedder(model=index.model, base_url=args.ollama)
    hits = index.search(embedder([args.query])[0], query_text=args.query, top_k=args.top)
    print(format_context(hits, max_chars=args.max_chars))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="maxmcp.docsearch", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="chunk and embed the reference files")
    build.add_argument("--extra", type=Path, nargs="*", default=[], help="extra .md files or folders")
    build.add_argument("--model", default=DEFAULT_EMBED_MODEL)
    build.add_argument("--ollama", default=DEFAULT_OLLAMA_URL)
    build.add_argument("--index", type=Path, default=DEFAULT_INDEX_PATH)
    build.add_argument("--max-chars", type=int, default=1200)
    build.set_defaults(func=cmd_build)

    search = sub.add_parser("search", help="query the index from the command line")
    search.add_argument("query")
    search.add_argument("--top", type=int, default=4)
    search.add_argument("--max-chars", type=int, default=6000)
    search.add_argument("--ollama", default=DEFAULT_OLLAMA_URL)
    search.add_argument("--index", type=Path, default=DEFAULT_INDEX_PATH)
    search.set_defaults(func=cmd_search)

    serve = sub.add_parser("serve", help="run the retrieval proxy (extra args pass through)")
    serve.set_defaults(func=None)

    args, rest = parser.parse_known_args(argv)
    if args.command == "serve":
        return proxy_main(rest)
    if rest:
        parser.error(f"unrecognized arguments: {' '.join(rest)}")
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
