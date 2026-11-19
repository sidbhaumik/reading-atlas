"""Project embeddings to 2D for display and find topic clusters."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

log = logging.getLogger(__name__)


@dataclass
class Layout:
    xy: np.ndarray  # (n, 2), scaled to [0, 1]
    labels: np.ndarray  # (n,), -1 = noise / unclustered


def _umap(vectors: np.ndarray, dims: int, seed: int, min_dist: float):
    import umap

    n = len(vectors)
    return umap.UMAP(
        n_components=dims,
        n_neighbors=max(2, min(15, n - 1)),
        min_dist=min_dist,
        metric="cosine",
        random_state=seed,
    ).fit_transform(vectors)


def build_layout(vectors: np.ndarray, min_cluster_size: int = 4, seed: int = 42) -> Layout:
    """Two UMAP runs: a 2D one for the picture and a denser 5D one for clustering.

    Clustering in 5D rather than on the 2D picture keeps clusters faithful to the embedding
    space instead of to whatever UMAP happened to squash together on screen.
    """
    from sklearn.cluster import HDBSCAN

    n = len(vectors)
    if n < 5:
        raise ValueError(f"Need at least 5 documents to build a map, got {n}")

    xy = _umap(vectors, dims=2, seed=seed, min_dist=0.1)
    xy = (xy - xy.min(0)) / np.ptp(xy, axis=0).clip(min=1e-9)

    dense = _umap(vectors, dims=min(5, n - 2), seed=seed, min_dist=0.0)
    labels = HDBSCAN(
        min_cluster_size=max(2, min(min_cluster_size, n // 2)),
        min_samples=2,
    ).fit_predict(dense)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    log.info("Found %d clusters, %d unclustered points", n_clusters, int((labels == -1).sum()))
    return Layout(xy=xy.astype(np.float32), labels=labels)
