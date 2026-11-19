"""`atlas build` — ingest, embed, lay out, label, export."""

from __future__ import annotations

import argparse
import logging
import sys

from .embed import DEFAULT_MODEL


def _build(args: argparse.Namespace) -> int:
    from .embed import embed
    from .export import export_atlas, nearest_neighbors
    from .ingest import load_bookmarks, load_notes
    from .label import label_clusters
    from .layout import build_layout

    docs = []
    for path in args.bookmarks or []:
        docs += load_bookmarks(path, fetch=args.fetch)
    for path in args.notes or []:
        docs += load_notes(path)
    if not docs:
        print("Nothing to map: pass --bookmarks and/or --notes.", file=sys.stderr)
        return 1

    vectors = embed(docs, model_name=args.model, cache_dir=args.cache)
    layout = build_layout(vectors, min_cluster_size=args.min_cluster_size, seed=args.seed)
    names = label_clusters(docs, layout.labels)
    atlas = export_atlas(docs, layout, names, args.out, args.model, nearest_neighbors(vectors))

    print(f"Mapped {atlas['meta']['count']} documents into {len(atlas['clusters'])} clusters")
    for c in sorted(atlas["clusters"], key=lambda c: -c["size"]):
        print(f"  [{c['size']:>3}] {c['label']}")
    print(f"Wrote {args.out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="atlas", description=__doc__)
    p.add_argument("-v", "--verbose", action="store_true")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="Build the atlas JSON from your sources")
    b.add_argument("--bookmarks", nargs="*", help="Exported bookmarks .html file(s)")
    b.add_argument("--notes", nargs="*", help="Folder(s) of Markdown notes")
    b.add_argument("--fetch", action="store_true", help="Download page text for bookmarks")
    b.add_argument("--out", default="web/data/atlas.json")
    b.add_argument("--model", default=DEFAULT_MODEL)
    b.add_argument("--cache", default=".cache")
    b.add_argument("--min-cluster-size", type=int, default=4)
    b.add_argument("--seed", type=int, default=42)
    b.set_defaults(func=_build)

    args = p.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
