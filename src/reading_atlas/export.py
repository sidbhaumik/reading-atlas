"""Write the atlas JSON that the static web viewer loads."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from .layout import Layout
from .models import Document


def _snippet(text: str, n: int = 280) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1].rsplit(" ", 1)[0] + "…"


def export_atlas(
    docs: list[Document],
    layout: Layout,
    cluster_names: dict[int, str],
    out_path: str | Path,
    model_name: str,
    neighbors: np.ndarray | None = None,
) -> dict:
    points = []
    for i, d in enumerate(docs):
        points.append(
            {
                "id": d.id,
                "x": round(float(layout.xy[i, 0]), 4),
                "y": round(float(layout.xy[i, 1]), 4),
                "c": int(layout.labels[i]),
                "title": d.title,
                "source": d.source,
                "url": d.url,
                "path": d.path,
                "created": d.created,
                "tags": d.tags,
                "snippet": _snippet(d.text),
                "nn": [int(j) for j in neighbors[i]] if neighbors is not None else [],
            }
        )

    clusters = []
    for c, name in sorted(cluster_names.items()):
        idx = np.flatnonzero(layout.labels == c)
        cx, cy = layout.xy[idx].mean(0)
        clusters.append(
            {"id": c, "label": name, "x": round(float(cx), 4), "y": round(float(cy), 4),
             "size": int(len(idx))}
        )

    atlas = {
        "meta": {
            "generated": datetime.now(UTC).isoformat(timespec="seconds"),
            "model": model_name,
            "count": len(points),
        },
        "clusters": clusters,
        "points": points,
    }
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(atlas, ensure_ascii=False, separators=(",", ":")))
    return atlas


def nearest_neighbors(vectors: np.ndarray, k: int = 5) -> np.ndarray:
    """Top-k cosine neighbours per point (vectors are already normalised)."""
    sims = vectors @ vectors.T
    np.fill_diagonal(sims, -np.inf)
    k = min(k, len(vectors) - 1)
    return np.argsort(-sims, axis=1)[:, :k]
