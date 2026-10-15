from web2md_client import ChunksResult, Document, MetadataResult, Web2MDError
from web2md_client._errors import error_from_response

DOC = {
    "url": "https://example.com/post",
    "format": "markdown",
    "markdown": "# T\n\nbody",
    "metadata": {"title": "T", "word_count": 2, "reading_time_min": 1},
    "word_count": 2,
    "tokens": 5,
    "cached": False,
    "rendered": False,
}


def test_document_from_dict_reads_known_fields():
    d = Document.from_dict(DOC)
    assert d.markdown == "# T\n\nbody"
    assert d.text is None
    assert d.metadata.title == "T"
    assert d.metadata.author is None
    assert d.tokens == 5


def test_unknown_fields_are_ignored_but_kept_in_raw():
    data = {**DOC, "token_estimates": {"cl100k": 6}, "metadata": {**DOC["metadata"], "new": 1}}
    d = Document.from_dict(data)
    assert d.raw["token_estimates"] == {"cl100k": 6}


def test_chunks_result_from_dict():
    r = ChunksResult.from_dict(
        {
            "url": "https://e.com",
            "title": "T",
            "chunks": [{"id": 0, "heading_path": ["A", "B"], "text": "x", "tokens": 3, "extra": 1}],
            "total_tokens": 3,
            "cached": True,
        }
    )
    assert r.chunks[0].heading_path == ["A", "B"]
    assert r.chunks[0].tokens == 3
    assert r.lang is None
    assert r.cached is True


def test_metadata_result_from_dict():
    m = MetadataResult.from_dict(
        {
            "url": "https://e.com",
            "cached": False,
            "title": "T",
            "word_count": 9,
            "reading_time_min": 1,
        }
    )
    assert (m.url, m.title, m.word_count) == ("https://e.com", "T", 9)


def test_error_from_api_shape():
    e = error_from_response(403, '{"error": {"code": "robots_disallowed", "message": "No."}}')
    assert (e.code, e.message, e.status) == ("robots_disallowed", "No.", 403)
    assert "robots_disallowed" in str(e)


def test_error_from_gateway_shape():
    e = error_from_response(403, '{"message": "You are not subscribed to this API."}')
    assert e.code == "rapidapi_auth"
    assert e.message == "You are not subscribed to this API."
    assert error_from_response(429, '{"message": "quota"}').code == "rapidapi_rate_limited"


def test_error_from_non_json_body():
    e = error_from_response(502, "<html>Bad Gateway</html>")
    assert e.code == "http_error"
    assert e.status == 502
    assert "Bad Gateway" in e.message


def test_error_from_empty_body():
    assert error_from_response(500, "").message == "HTTP 500"


def test_web2md_error_is_exception():
    assert isinstance(Web2MDError("x", "y", None), Exception)
