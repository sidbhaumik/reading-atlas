"""Embed documents with a local sentence-transformers model, caching by content hash."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

import numpy as np

from .models import Document

log = logging.getLogger(__name__)

DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"


def _key(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()


def embed(
    docs: list[Document],
    model_name: str = DEFAULT_MODEL,
    cache_dir: str | Path = ".cache",
    batch_size: int = 32,
) -> np.ndarray:
    """Return an (n_docs, dim) array of L2-normalised embeddings.

    Only texts not already in the cache are sent to the model, so re-running after adding a
    few bookmarks is nearly instant.
    """
    cache_path = Path(cache_dir) / f"embeddings-{model_name.replace('/', '__')}.npz"
    cache: dict[str, np.ndarray] = {}
    if cache_path.exists():
        with np.load(cache_path) as z:
            keys = json.loads(str(z["keys"]))
            cache = dict(zip(keys, z["vectors"], strict=True))

    texts = [d.embed_text for d in docs]
    keys = [_key(t) for t in texts]
    missing = [i for i, k in enumerate(keys) if k not in cache]

    if missing:
        from sentence_transformers import SentenceTransformer

        log.info("Embedding %d new documents with %s (%d cached)", len(missing),
                 model_name, len(docs) - len(missing))
        model = SentenceTransformer(model_name)
        vectors = model.encode(
            [texts[i] for i in missing],
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=len(missing) > 64,
        )
        for i, v in zip(missing, vectors, strict=True):
            cache[keys[i]] = v.astype(np.float32)

        cache_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            cache_path,
            keys=json.dumps(list(cache)),
            vectors=np.stack(list(cache.values())),
        )
    else:
        log.info("All %d embeddings served from cache", len(docs))

    return np.stack([cache[k] for k in keys])
