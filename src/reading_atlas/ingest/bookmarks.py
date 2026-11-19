"""Parse the Netscape bookmark HTML format that Chrome, Safari, Firefox and Edge all export."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path

from ..models import Document

log = logging.getLogger(__name__)


class _BookmarkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.items: list[dict] = []
        self._folders: list[str] = []
        self._pending_folder: str | None = None
        self._in_h3 = False
        self._current: dict | None = None
        self._in_dd = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k.lower(): v for k, v in attrs}
        if tag == "h3":
            self._in_h3 = True
            self._pending_folder = ""
        elif tag == "dl":
            # A <DL> right after an <H3> opens that folder.
            self._folders.append(self._pending_folder or "")
            self._pending_folder = None
        elif tag == "a" and a.get("href"):
            self._current = {
                "url": a["href"],
                "add_date": a.get("add_date"),
                "title": "",
                "folders": [f for f in self._folders if f],
                "description": "",
            }
        elif tag == "dd":
            self._in_dd = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "h3":
            self._in_h3 = False
        elif tag == "dl":
            if self._folders:
                self._folders.pop()
        elif tag == "a" and self._current is not None:
            self.items.append(self._current)
            self._current = None

    def handle_data(self, data: str) -> None:
        if self._in_h3 and self._pending_folder is not None:
            self._pending_folder += data.strip()
        elif self._current is not None:
            self._current["title"] += data
        elif self._in_dd and self.items:
            # Firefox puts a description in <DD> after the link.
            self.items[-1]["description"] += data.strip()
            self._in_dd = False


def _iso(ts: str | None) -> str | None:
    if not ts or not ts.isdigit():
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=UTC).date().isoformat()
    except (OverflowError, ValueError):
        return None


_SEPARATORS = (" - ", " | ", " — ", " – ", " · ")


def _suffix(title: str) -> str | None:
    for sep in _SEPARATORS:
        if sep in title:
            head, _, tail = title.rpartition(sep)
            if head and len(tail.split()) <= 3:
                return sep + tail
    return None


def _repeated_suffixes(titles: list[str], min_count: int = 3) -> set[str]:
    """Site names like ' - Wikipedia' or ' | Medium' that end many titles.

    They add no meaning but make every page from one site look alike to the embedder.
    """
    counts: dict[str, int] = {}
    for t in titles:
        if s := _suffix(t):
            counts[s] = counts.get(s, 0) + 1
    return {s for s, n in counts.items() if n >= min_count}


def _strip_suffix(title: str, suffixes: set[str]) -> str:
    for s in suffixes:
        if title.endswith(s):
            return title[: -len(s)]
    return title


def load_bookmarks(path: str | Path, fetch: bool = False) -> list[Document]:
    """Load bookmarks from an exported HTML file.

    With ``fetch=True`` the page behind each link is downloaded and its main text extracted
    (needs the ``fetch`` extra). Without it, the map is built from titles, folders and
    descriptions, which is fast and works offline.
    """
    parser = _BookmarkParser()
    parser.feed(Path(path).read_text(encoding="utf-8", errors="replace"))

    titles = [" ".join(i["title"].split()) for i in parser.items]
    site_suffixes = _repeated_suffixes(titles)

    docs: list[Document] = []
    seen: set[str] = set()
    for item, title in zip(parser.items, titles, strict=True):
        url = item["url"]
        if not url.startswith(("http://", "https://")) or url in seen:
            continue
        seen.add(url)
        title = _strip_suffix(title, site_suffixes) or url
        text = item["description"]
        if fetch:
            text = _fetch_text(url) or text
        docs.append(
            Document(
                source="bookmark",
                title=title,
                text=text,
                url=url,
                created=_iso(item["add_date"]),
                tags=item["folders"],
            )
        )
    log.info("Loaded %d bookmarks from %s", len(docs), path)
    return docs


def _fetch_text(url: str, max_chars: int = 4000) -> str:
    try:
        import trafilatura
    except ImportError as e:  # pragma: no cover
        raise SystemExit("Fetching pages needs: pip install 'reading-atlas[fetch]'") from e
    try:
        html = trafilatura.fetch_url(url)
        text = trafilatura.extract(html) if html else None
    except Exception as e:  # network errors should never kill a build
        log.warning("Could not fetch %s: %s", url, e)
        return ""
    return (text or "")[:max_chars]
