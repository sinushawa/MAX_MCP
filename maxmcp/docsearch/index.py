"""Chunk, embed, store, and search Markdown references with Ollama embeddings.

Pure standard library on purpose: the index is a few hundred chunks, so cosine
similarity in plain Python is instant and there is nothing new to install.
"""

from __future__ import annotations

import json
import math
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_SOURCE_DIR = ROOT / "skills" / "3dsmax-mcp-dev"
DEFAULT_EMBED_MODEL = os.environ.get("MAXMCP_EMBED_MODEL", "nomic-embed-text")
DEFAULT_OLLAMA_URL = os.environ.get("MAXMCP_OLLAMA_URL", "http://localhost:11434").rstrip("/")
DEFAULT_INDEX_PATH = (
    Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "3dsmax-mcp" / "docs_index.json"
)

Embedder = Callable[[Sequence[str]], list[list[float]]]

_HEADING_RE = re.compile(r"^(#{1,4})\s+(.*)$")
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.]{3,}")


@dataclass(frozen=True)
class Chunk:
    id: str
    source: str
    title: str
    text: str

    def to_dict(self) -> dict:
        return {"id": self.id, "source": self.source, "title": self.title, "text": self.text}


def default_sources(extra: Iterable[Path] = ()) -> list[Path]:
    """Bundled reference files plus any extra Markdown files or directories."""
    files = sorted(DEFAULT_SOURCE_DIR.glob("*.md"))
    for path in extra:
        path = Path(path)
        if path.is_dir():
            files.extend(sorted(path.rglob("*.md")))
        elif path.is_file():
            files.append(path)
    seen: set[Path] = set()
    unique: list[Path] = []
    for file in files:
        resolved = file.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(file)
    return unique


def _split_long(text: str, max_chars: int) -> list[str]:
    """Split on blank lines, then hard-wrap any paragraph still over the limit."""
    parts: list[str] = []
    current = ""
    for paragraph in re.split(r"\n\s*\n", text):
        paragraph = paragraph.strip("\n")
        if not paragraph.strip():
            continue
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            parts.append(current)
            current = ""
        while len(paragraph) > max_chars:
            cut = paragraph.rfind("\n", 0, max_chars)
            if cut <= 0:
                cut = max_chars
            parts.append(paragraph[:cut])
            paragraph = paragraph[cut:].lstrip("\n")
        current = paragraph
    if current:
        parts.append(current)
    return parts


def chunk_markdown(text: str, source: str, max_chars: int = 1200) -> list[Chunk]:
    """Split a Markdown document into heading-scoped chunks no longer than max_chars.

    Every chunk keeps its heading path as a title so a retrieved fragment still reads
    as "materials-textures > VRayMtl" rather than as loose text.
    """
    sections: list[tuple[list[str], list[str]]] = []
    heading_path: list[str] = []
    body: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
        match = None if in_fence else _HEADING_RE.match(line)
        if match:
            if body and any(part.strip() for part in body):
                sections.append((list(heading_path), body))
            level = len(match.group(1))
            heading_path = heading_path[: level - 1] + [match.group(2).strip()]
            body = []
        else:
            body.append(line)
    if body and any(part.strip() for part in body):
        sections.append((list(heading_path), body))

    chunks: list[Chunk] = []
    stem = Path(source).stem
    for path, lines in sections:
        title = " > ".join([stem, *path]) if path else stem
        for piece in _split_long("\n".join(lines).strip(), max_chars):
            index = len(chunks)
            chunks.append(Chunk(id=f"{stem}#{index}", source=source, title=title, text=piece))
    return chunks


class OllamaEmbedder:
    """Embed texts through Ollama's /api/embed endpoint."""

    def __init__(
        self,
        model: str = DEFAULT_EMBED_MODEL,
        base_url: str = DEFAULT_OLLAMA_URL,
        batch_size: int = 32,
        timeout: float = 120.0,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.batch_size = batch_size
        self.timeout = timeout

    def __call__(self, texts: Sequence[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self.batch_size):
            batch = list(texts[start : start + self.batch_size])
            payload = json.dumps({"model": self.model, "input": batch}).encode("utf-8")
            request = urllib.request.Request(
                f"{self.base_url}/api/embed",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    data = json.loads(response.read().decode("utf-8"))
            except urllib.error.URLError as exc:
                raise RuntimeError(
                    f"Ollama embeddings unavailable at {self.base_url} "
                    f"(model {self.model}): {exc}"
                ) from exc
            embeddings = data.get("embeddings")
            if not isinstance(embeddings, list) or len(embeddings) != len(batch):
                raise RuntimeError(f"Unexpected embed response from Ollama: {str(data)[:200]}")
            vectors.extend([float(x) for x in vector] for vector in embeddings)
        return vectors


def _normalize(vector: Sequence[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vector)) or 1.0
    return [x / norm for x in vector]


def _identifiers(text: str) -> set[str]:
    return {token.lower() for token in _IDENT_RE.findall(text)}


class DocIndex:
    """In-memory vector index with a small exact-identifier bonus.

    Embeddings capture intent ("extrude a face"), while the identifier bonus keeps
    exact API names such as ``polyop.extrudeFaces`` from being outranked by prose.
    """

    def __init__(self, chunks: Sequence[Chunk], vectors: Sequence[Sequence[float]], model: str) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors differ in length")
        self.chunks = list(chunks)
        self.vectors = [_normalize(vector) for vector in vectors]
        self.model = model
        self._chunk_idents = [_identifiers(chunk.text + " " + chunk.title) for chunk in self.chunks]

    def __len__(self) -> int:
        return len(self.chunks)

    @classmethod
    def load(cls, path: Path = DEFAULT_INDEX_PATH) -> "DocIndex":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        chunks = [Chunk(**{k: item[k] for k in ("id", "source", "title", "text")}) for item in data["chunks"]]
        vectors = [item["vector"] for item in data["chunks"]]
        return cls(chunks, vectors, data.get("model", DEFAULT_EMBED_MODEL))

    def save(self, path: Path = DEFAULT_INDEX_PATH) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "model": self.model,
            "dims": len(self.vectors[0]) if self.vectors else 0,
            "built_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "chunks": [
                {**chunk.to_dict(), "vector": [round(x, 5) for x in vector]}
                for chunk, vector in zip(self.chunks, self.vectors)
            ],
        }
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def search(
        self,
        query_vector: Sequence[float],
        query_text: str = "",
        top_k: int = 4,
        identifier_bonus: float = 0.04,
    ) -> list[tuple[float, Chunk]]:
        query = _normalize(query_vector)
        query_idents = _identifiers(query_text) if query_text else set()
        scored: list[tuple[float, int]] = []
        for index, vector in enumerate(self.vectors):
            score = sum(a * b for a, b in zip(query, vector))
            if query_idents:
                overlap = len(query_idents & self._chunk_idents[index])
                score += identifier_bonus * min(overlap, 5)
            scored.append((score, index))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [(score, self.chunks[index]) for score, index in scored[:top_k]]


def build_index(
    sources: Sequence[Path],
    embedder: Embedder,
    model: str = DEFAULT_EMBED_MODEL,
    max_chars: int = 1200,
) -> DocIndex:
    chunks: list[Chunk] = []
    for path in sources:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
        chunks.extend(chunk_markdown(text, Path(path).name, max_chars=max_chars))
    if not chunks:
        raise ValueError("no chunks produced from sources")
    vectors = embedder([f"{chunk.title}\n{chunk.text}" for chunk in chunks])
    return DocIndex(chunks, vectors, model)


def format_context(hits: Sequence[tuple[float, Chunk]], max_chars: int = 6000) -> str:
    """Render hits as a compact reference block for a system prompt or tool result."""
    parts: list[str] = []
    used = 0
    for score, chunk in hits:
        block = f"### {chunk.title}  ({chunk.source}, score {score:.2f})\n{chunk.text.strip()}\n"
        if used + len(block) > max_chars and parts:
            break
        parts.append(block)
        used += len(block)
    return "\n".join(parts).strip()
