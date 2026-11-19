# Reading Atlas

**Turn your bookmarks and notes into a map you can explore.** Every item becomes a dot; items
that mean similar things land near each other; topics are found and named automatically.

Everything runs locally with an open embedding model: no API keys, and your data never
leaves your machine. The output is a single JSON file plus a static web page you can host
anywhere (GitHub Pages works).

**[▶ Live demo](https://sidbhaumik.github.io/reading-atlas/)** (built from public Wikipedia sample data)

<!-- TODO: add a screenshot / GIF of the live demo here -->

## How it works

```
 bookmarks.html ─┐
                 ├─► ingest ─► embed ─► layout ─► label ─► atlas.json ─► web viewer
 notes/*.md ─────┘    │          │         │         │
                 Document    bge-small  UMAP 2D   c-TF-IDF
                 records     (local,    + HDBSCAN topic names
                             cached)    on UMAP 5D
```

| Stage | What it does | Why this choice |
|---|---|---|
| **Ingest** | Parses browser bookmark exports (Chrome, Safari, Firefox, Edge) and folders of Markdown notes (Obsidian-friendly: front matter, `#tags`, `[[wikilinks]]`). | Stdlib parsers, no lock-in to one app. |
| **Embed** | Encodes each item with [`BAAI/bge-small-en-v1.5`](https://huggingface.co/BAAI/bge-small-en-v1.5) via sentence-transformers. Vectors are cached by content hash. | Small, fast on a laptop CPU, strong retrieval quality. Re-runs only embed what's new. |
| **Layout** | UMAP to 2D for the picture; a separate UMAP to 5D feeds HDBSCAN for clustering. | Clustering in 5D keeps topics faithful to the embedding space instead of to on-screen distortions. HDBSCAN picks the number of topics and leaves outliers unclustered. |
| **Label** | Class-based TF-IDF picks the words that best distinguish each cluster. | Interpretable and free. An LLM labeller is on the roadmap. |
| **Viewer** | Dependency-free canvas app: zoom, pan, search, filters, a details panel and "closest in meaning" neighbours. | Static files only, loads instantly. |

## Quick start

```bash
git clone https://github.com/sidbhaumik/reading-atlas.git
cd reading-atlas
uv venv && uv pip install -e .        # or: python -m venv .venv && pip install -e .

# Build the demo map from the bundled sample data
atlas build --notes data/sample/notes --bookmarks data/sample/sample-bookmarks.html

# View it
python -m http.server -d web 8000     # open http://localhost:8000
```

## Map your own reading

1. **Export your bookmarks.** Chrome: *Bookmarks → Bookmark manager → ⋮ → Export bookmarks*.
   Safari: *File → Export → Bookmarks*. Firefox: *Bookmarks → Manage → Import and Backup → Export*.
2. **Put private files in `data/private/`.** This folder is git-ignored.
3. Build:

```bash
atlas build \
  --bookmarks data/private/bookmarks.html \
  --notes ~/path/to/obsidian-vault \
  --out out/atlas.json
```

Add `--fetch` (after `pip install -e ".[fetch]"`) to download each bookmarked page and embed
its article text instead of just the title. It's slower, but produces much richer maps.

> **Privacy:** `web/data/atlas.json` is committed so the public demo works. Write your
> personal atlas to `out/` (git-ignored) and preview it locally by copying it into `web/data/`
> without committing.

## Project layout

```
src/reading_atlas/
  ingest/        bookmarks.py, markdown_notes.py
  embed.py       local embeddings + cache
  layout.py      UMAP + HDBSCAN
  label.py       c-TF-IDF cluster names
  export.py      atlas.json + nearest neighbours
  cli.py         `atlas build`
web/             static viewer (index.html, app.js, style.css)
scripts/         build_sample.py: regenerates the public demo data
tests/
```

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).

## Development

```bash
uv pip install -e ".[dev]"
pytest
ruff check .
```

## License

Code: MIT. Sample notes in `data/sample/` are summaries from Wikipedia, licensed
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/); each note links its source article.
