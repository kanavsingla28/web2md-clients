import pytest

from web2md_client import ChunksResult, Document
from web2md_client._records import check_mode, iter_records, normalize_urls


class FakeClient:
    def __init__(self):
        self.calls = []
        self.flags = []

    def chunks(self, url, *, max_tokens, overlap_tokens, **flags):
        self.calls.append(("chunks", url, max_tokens, overlap_tokens))
        self.flags.append(flags)
        return ChunksResult.from_dict(
            {
                "url": url + "final",
                "title": "Page",
                "chunks": [
                    {"id": 0, "heading_path": [], "text": "intro", "tokens": 2},
                    {"id": 1, "heading_path": ["A", "B"], "text": "body", "tokens": 3},
                ],
                "total_tokens": 5,
                "cached": False,
            }
        )

    def read(self, url, *, format, **flags):
        self.calls.append(("read", url, format))
        self.flags.append(flags)
        return Document.from_dict(
            {
                "url": url,
                "format": "markdown",
                "markdown": "# Page",
                "metadata": {
                    "title": "Page",
                    "language": "en",
                    "word_count": 1,
                    "reading_time_min": 1,
                },
                "word_count": 1,
                "tokens": 3,
                "cached": False,
                "rendered": False,
            }
        )


def test_chunk_records_flat_metadata():
    recs = iter_records(FakeClient(), "https://e.com/", "chunks", 256, 20)
    assert [t for t, _ in recs] == ["intro", "body"]
    assert recs[1][1] == {
        "source": "https://e.com/final",
        "title": "Page",
        "heading_path": "A > B",
        "chunk_id": 1,
        "tokens": 3,
    }
    assert recs[0][1]["heading_path"] == ""
    for _, meta in recs:
        assert all(isinstance(v, (str, int, float)) for v in meta.values())


def test_read_record_drops_none():
    ((text, meta),) = iter_records(FakeClient(), "https://e.com/", "read", 512, 50)
    assert text == "# Page"
    assert meta == {
        "source": "https://e.com/",
        "title": "Page",
        "tokens": 3,
        "word_count": 1,
        "language": "en",
    }


def test_title_none_dropped_from_chunks():
    class NoTitle(FakeClient):
        def chunks(self, url, *, max_tokens, overlap_tokens, **flags):
            return ChunksResult.from_dict(
                {
                    "chunks": [{"id": 0, "heading_path": [], "text": "x", "tokens": 1}],
                    "total_tokens": 1,
                    "cached": False,
                }
            )

    ((_, meta),) = iter_records(NoTitle(), "https://e.com/", "chunks", 512, 50)
    assert "title" not in meta and meta["source"] == "https://e.com/"


def test_normalize_and_mode():
    assert normalize_urls("https://a") == ["https://a"]
    assert normalize_urls(("https://a", "https://b")) == ["https://a", "https://b"]
    assert check_mode("read") == "read"
    with pytest.raises(ValueError):
        check_mode("markdown")
