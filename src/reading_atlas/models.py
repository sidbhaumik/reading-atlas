from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field


@dataclass
class Document:
    """One item on the map: a bookmark, a note, a highlight."""

    source: str  # "bookmark" | "note"
    title: str
    text: str
    url: str | None = None
    path: str | None = None
    created: str | None = None  # ISO-8601 date when known
    tags: list[str] = field(default_factory=list)

    @property
    def id(self) -> str:
        key = self.url or self.path or self.title
        return hashlib.sha1(f"{self.source}:{key}".encode()).hexdigest()[:12]

    @property
    def embed_text(self) -> str:
        """What actually gets embedded: title carries a lot of signal for short items."""
        body = self.text.strip()
        return f"{self.title}\n\n{body}" if body else self.title

    def to_dict(self) -> dict:
        return {"id": self.id, **asdict(self)}
