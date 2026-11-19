"""Build the public demo dataset from Wikipedia summaries.

Creates:
  data/sample/notes/*.md          one note per article (summary text, CC BY-SA 4.0)
  data/sample/sample-bookmarks.html  a browser-style bookmarks export (titles + folders only)

Usage:  python scripts/build_sample.py
"""

from __future__ import annotations

import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "sample"
API = "https://en.wikipedia.org/api/rest_v1/page/summary/"
UA = "reading-atlas-sample-builder/0.1 (open-source demo)"

# Notes: full summaries. Several themes so the map has visible structure.
NOTES = {
    "space": ["Voyager_1", "James_Webb_Space_Telescope", "Exoplanet", "Apollo_11",
              "Dark_matter", "Mars_rover", "Black_hole", "International_Space_Station"],
    "food": ["Fermentation_in_food_processing", "Sourdough", "Kimchi", "Maillard_reaction",
             "Umami", "Miso", "Coffee_roasting", "Sous_vide"],
    "music": ["Circle_of_fifths", "Counterpoint", "Jazz_improvisation", "Blues_scale",
              "Raga", "Polyrhythm", "Twelve-tone_technique", "Syncopation"],
    "systems": ["CAP_theorem", "Raft_(algorithm)", "Consistent_hashing", "MapReduce",
                "Apache_Kafka", "Vector_database", "Bloom_filter", "Eventual_consistency"],
    "nature": ["Bird_migration", "Mycorrhiza", "Coral_reef", "Keystone_species",
               "Rewilding", "Monarch_butterfly", "Old-growth_forest", "Pollinator_decline"],
    "mind": ["Stoicism", "Flow_(psychology)", "Cognitive_bias", "Deliberate_practice",
             "Zettelkasten", "Spaced_repetition", "Philosophy_of_mind", "Growth_mindset"],
}

# Bookmarks: just titles in folders, like a real export without --fetch.
BOOKMARKS = {
    "Space": ["Hubble_Space_Telescope", "Kuiper_belt", "Gravitational_wave", "SpaceX_Starship"],
    "Cooking": ["Kombucha", "Ramen", "Smoking_(cooking)", "Tempering_(spices)"],
    "Music": ["Modal_jazz", "Gamelan", "Music_theory", "Chord_progression"],
    "Engineering": ["Paxos_(computer_science)", "Apache_Spark", "Data_lake",
                    "Embedding_(machine_learning)"],
    "Outdoors": ["Leave_No_Trace", "Wetland", "Birdwatching", "Lichen"],
    "Learning": ["Metacognition", "Mental_model", "Commonplace_book", "Memory_palace"],
}


def summary(title: str, retries: int = 6) -> dict:
    req = urllib.request.Request(API + urllib.parse.quote(title), headers={"User-Agent": UA})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == retries - 1:
                raise
            wait = int(e.headers.get("Retry-After") or 0) or 2 ** (attempt + 1)
            print(f"  rate limited, waiting {wait}s")
            time.sleep(wait)
    raise RuntimeError("unreachable")


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def main() -> None:
    notes_dir = OUT / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    for old in notes_dir.glob("*.md"):
        old.unlink()

    for theme, titles in NOTES.items():
        for t in titles:
            s = summary(t)
            url = s["content_urls"]["desktop"]["page"]
            body = (
                f"---\ntitle: {s['title']}\ntags: [{theme}]\nsource: {url}\n---\n\n"
                f"# {s['title']}\n\n{s.get('extract', '').strip()}\n"
            )
            (notes_dir / f"{slug(s['title'])}.md").write_text(body, encoding="utf-8")
            print(f"note      {s['title']}")
            time.sleep(0.6)

    lines = [
        "<!DOCTYPE NETSCAPE-Bookmark-file-1>",
        '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
        "<TITLE>Bookmarks</TITLE>", "<H1>Bookmarks</H1>", "<DL><p>",
    ]
    ts = 1700000000
    for folder, titles in BOOKMARKS.items():
        lines += [f"    <DT><H3>{html.escape(folder)}</H3>", "    <DL><p>"]
        for t in titles:
            s = summary(t)
            url = s["content_urls"]["desktop"]["page"]
            desc = s.get("description", "")
            label = f"{s['title']} - Wikipedia"
            lines.append(f'        <DT><A HREF="{html.escape(url)}" ADD_DATE="{ts}">'
                         f"{html.escape(label)}</A>")
            if desc:
                lines.append(f"        <DD>{html.escape(desc)}")
            ts += 86400 * 3
            print(f"bookmark  {s['title']}")
            time.sleep(0.6)
        lines.append("    </DL><p>")
    lines.append("</DL><p>")
    (OUT / "sample-bookmarks.html").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nWrote sample data to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
