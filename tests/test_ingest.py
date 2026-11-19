from pathlib import Path

from reading_atlas.ingest import load_bookmarks, load_notes

FIXTURES = Path(__file__).parent / "fixtures"


def test_bookmarks_parse_folders_dates_and_descriptions():
    docs = load_bookmarks(FIXTURES / "bookmarks.html")
    by_url = {d.url: d for d in docs}

    assert set(by_url) == {"https://example.com/top", "https://example.com/a",
                           "https://example.com/b"}
    assert by_url["https://example.com/top"].title == "Top level & loose"
    assert by_url["https://example.com/top"].tags == []
    assert by_url["https://example.com/a"].tags == ["Reading"]
    assert by_url["https://example.com/a"].text == "A short description of A"
    assert by_url["https://example.com/a"].created == "2023-11-15"
    assert by_url["https://example.com/b"].tags == ["Reading", "Deep"]


def test_bookmarks_skip_duplicates_and_non_http():
    docs = load_bookmarks(FIXTURES / "bookmarks.html")
    assert [d.title for d in docs].count("Article A") == 1
    assert not any(d.url.startswith("javascript:") for d in docs)


def test_bookmarks_strip_repeated_site_suffixes(tmp_path: Path):
    links = [("a", "Kombucha - Wikipedia"), ("b", "Ramen - Wikipedia"),
             ("c", "Lichen - Wikipedia"), ("d", "Cats - Part 2")]
    body = "".join(f'<DT><A HREF="https://x.org/{u}">{t}</A>\n' for u, t in links)
    f = tmp_path / "b.html"
    f.write_text(f"<DL><p>\n{body}</DL>")
    titles = [d.title for d in load_bookmarks(f)]
    assert titles == ["Kombucha", "Ramen", "Lichen", "Cats - Part 2"]


def test_notes_frontmatter_tags_links_and_skips(tmp_path: Path):
    (tmp_path / "a.md").write_text(
        "---\ntitle: Custom Title\ntags: [ideas, reading]\ndate: 2024-01-02\n---\n"
        "# Ignored H1\nSee [[Other Note|the other]] and [a link](https://x.y). #inline-tag\n"
    )
    (tmp_path / "plain.md").write_text("# From Heading\n\nBody text.\n")
    (tmp_path / "empty.md").write_text("   \n")
    (tmp_path / ".obsidian").mkdir()
    (tmp_path / ".obsidian" / "config.md").write_text("# should be skipped\n")

    docs = {d.path: d for d in load_notes(tmp_path)}
    assert set(docs) == {"a.md", "plain.md"}

    a = docs["a.md"]
    assert a.title == "Custom Title"
    assert a.created == "2024-01-02"
    assert a.tags == ["ideas", "inline-tag", "reading"]
    assert "the other" in a.text and "[[" not in a.text
    assert "a link" in a.text and "https://x.y" not in a.text

    assert docs["plain.md"].title == "From Heading"


def test_document_ids_are_stable():
    first = load_bookmarks(FIXTURES / "bookmarks.html")
    second = load_bookmarks(FIXTURES / "bookmarks.html")
    assert [d.id for d in first] == [d.id for d in second]
    assert len({d.id for d in first}) == len(first)
