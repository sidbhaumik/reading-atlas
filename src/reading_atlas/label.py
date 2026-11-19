"""Name each cluster with its most distinctive terms (class-based TF-IDF)."""

from __future__ import annotations

import numpy as np

from .models import Document


def label_clusters(docs: list[Document], labels: np.ndarray, top_n: int = 3) -> dict[int, str]:
    """Treat each cluster as one big document and pick the terms that set it apart.

    This is the c-TF-IDF trick popularised by BERTopic: a term scores high when it is
    frequent inside the cluster and rare across the others. No API key needed; an LLM
    labeller can be layered on later for nicer names.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer

    cluster_ids = sorted(c for c in set(labels.tolist()) if c != -1)
    if not cluster_ids:
        return {}

    corpus = [
        " ".join(docs[i].embed_text for i in np.flatnonzero(labels == c)) for c in cluster_ids
    ]
    vec = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        max_df=0.8 if len(corpus) > 2 else 1.0,
        sublinear_tf=True,
        token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z-]{2,}\b",
    )
    matrix = vec.fit_transform(corpus)
    terms = np.array(vec.get_feature_names_out())

    out: dict[int, str] = {}
    for row, c in enumerate(cluster_ids):
        scores = matrix[row].toarray().ravel()
        picked: list[str] = []
        for t in terms[np.argsort(scores)[::-1]]:
            # Skip a unigram already covered by a chosen bigram (and vice versa) and
            # near-duplicates like "consistent" / "consistency".
            if any(t in p or p in t or t[:6] == p[:6] for p in picked):
                continue
            picked.append(t)
            if len(picked) == top_n:
                break
        out[c] = " · ".join(picked)
    return out
