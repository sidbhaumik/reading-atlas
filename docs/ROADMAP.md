# Roadmap

## v0.1: the map (this release)
- [x] Ingest browser bookmarks and Markdown notes
- [x] Local embeddings with content-hash cache
- [x] UMAP layout + HDBSCAN topics + c-TF-IDF labels
- [x] Static canvas viewer: zoom, pan, search, filters, neighbours
- [x] Public demo dataset built from Wikipedia

## v0.2: publish the demo
- [ ] GitHub Pages deploy workflow for `web/`
- [ ] Screenshot / GIF in the README
- [ ] `--fetch` with concurrency + per-domain politeness + on-disk page cache

## v0.3: richer meaning
- [ ] Chunk long notes; one dot per note, chunks used for search
- [ ] LLM cluster labels and one-paragraph cluster summaries (optional, API-key gated)
- [ ] Hierarchical topics: zoom in to see sub-topics appear
- [ ] Timeline slider: watch how your interests drift over the years

## v0.4: ask your library
- [ ] Semantic search box (embed the query in-browser with transformers.js)
- [ ] "Ask my library": RAG answers with citations that light up on the map
- [ ] Gap finder: surface sparse regions between dense topics

## More sources
- [ ] Kindle `My Clippings.txt`
- [ ] Readwise / Pocket / Raindrop exports
- [ ] Podcast transcripts
