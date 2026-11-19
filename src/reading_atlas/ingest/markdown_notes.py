"""Load a folder of Markdown notes (an Obsidian vault, a Zettelkasten, a docs folder)."""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from pathlib import Path

from ..models import Document

log = logging.getLogger(__name__)

_FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_H1 = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_TAG = re.compile(r"(?<![\w#])#([A-Za-z][\w/-]+)")
_WIKILINK = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
_MDLINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_SKIP_DIRS = {".obsidian", ".trash", ".git", "node_modules"}


def _parse_frontmatter(block: str) -> dict[str, str | list[str]]:
    """Tiny YAML subset: `key: value` and `key: [a, b]`. Enough for title/tags/date."""
    out: dict[str, str | list[str]] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            out[key.strip()] = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
        else:
            out[key.strip()] = val.strip("'\"")
    return out


def _clean(text: str) -> str:
    text = _WIKILINK.sub(lambda m: m.group(2) or m.group(1), text)
    text = _MDLINK.sub(r"\1", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def load_notes(root: str | Path, max_chars: int = 4000) -> list[Document]:
    root = Path(root)
    docs: list[Document] = []
    for path in sorted(root.rglob("*.md")):
        if any(part in _SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        meta: dict = {}
        if m := _FRONTMATTER.match(raw):
            meta = _parse_frontmatter(m.group(1))
            raw = raw[m.end():]

        title = meta.get("title") or ((h := _H1.search(raw)) and h.group(1).strip()) or path.stem
        body = _clean(raw)
        if not body:
            continue

        tags = meta.get("tags") or []
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]
        tags = sorted(set(tags) | set(_TAG.findall(body)))

        created = meta.get("date") or meta.get("created")
        if not created:
            created = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).date().isoformat()

        docs.append(
            Document(
                source="note",
                title=str(title),
                text=body[:max_chars],
                url=meta.get("source") or meta.get("url") or None,
                path=str(path.relative_to(root)),
                created=str(created),
                tags=tags,
            )
        )
    log.info("Loaded %d notes from %s", len(docs), root)
    return docs
