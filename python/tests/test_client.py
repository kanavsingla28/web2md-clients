import json

import httpx
import pytest
import respx

from web2md_client import (
    DEFAULT_BASE_URL,
    ChunksResult,
    Document,
    MetadataResult,
    Web2MD,
    Web2MDError,
)

DOC = {
    "url": "https://e.com/",
    "format": "markdown",
    "markdown": "# Hi",
    "metadata": {"word_count": 1, "reading_time_min": 1},
    "word_count": 1,
    "tokens": 2,
    "cached": False,
    "rendered": False,
}
HOST = "web2md-webpage-to-markdown-rag-chunks.p.rapidapi.com"


@pytest.fixture
def client():
    with Web2MD(api_key="test-key") as c:
        yield c


@respx.mock
def test_read_sends_headers_and_minimal_body(client):
    route = respx.post(f"{DEFAULT_BASE_URL}/v1/read").mock(
        return_value=httpx.Response(200, json=DOC)
    )
    doc = client.read("https://e.com/")
    assert isinstance(doc, Document) and doc.markdown == "# Hi"
    req = route.calls.last.request
    assert req.headers["X-RapidAPI-Key"] == "test-key"
    assert req.headers["X-RapidAPI-Host"] == HOST
    assert req.headers["User-Agent"].startswith("web2md-client-python/")
    assert json.loads(req.content) == {"url": "https://e.com/", "format": "markdown"}


@respx.mock
def test_flags_sent_only_when_set(client):
    route = respx.post(f"{DEFAULT_BASE_URL}/v1/read").mock(
        return_value=httpx.Response(200, json=DOC)
    )
    client.read("https://e.com/", format="text", include_images=True, include_links=False)
    assert json.loads(route.calls.last.request.content) == {
        "url": "https://e.com/",
        "format": "text",
        "include_images": True,
        "include_links": False,
    }


@respx.mock
def test_convert_body(client):
    route = respx.post(f"{DEFAULT_BASE_URL}/v1/convert").mock(
        return_value=httpx.Response(200, json=DOC)
    )
    client.convert("<p>hi</p>", url="https://e.com/")
    assert json.loads(route.calls.last.request.content) == {
        "html": "<p>hi</p>",
        "url": "https://e.com/",
        "format": "markdown",
    }


@respx.mock
def test_chunks_body_and_result(client):
    body = {
        "chunks": [{"id": 0, "heading_path": [], "text": "x", "tokens": 1}],
        "total_tokens": 1,
        "cached": False,
    }
    route = respx.post(f"{DEFAULT_BASE_URL}/v1/chunks").mock(
        return_value=httpx.Response(200, json=body)
    )
    r = client.chunks("https://e.com/", max_tokens=256, overlap_tokens=0)
    assert json.loads(route.calls.last.request.content) == {
        "url": "https://e.com/",
        "max_tokens": 256,
        "overlap_tokens": 0,
    }
    assert isinstance(r, ChunksResult) and r.chunks[0].text == "x"


def test_chunks_needs_exactly_one_source(client):
    with pytest.raises(ValueError):
        client.chunks()
    with pytest.raises(ValueError):
        client.chunks("https://e.com/", html="<p>x</p>")


@respx.mock
def test_metadata(client):
    respx.post(f"{DEFAULT_BASE_URL}/v1/metadata").mock(
        return_value=httpx.Response(
            200,
            json={"url": "https://e.com/", "cached": False, "word_count": 3, "reading_time_min": 1},
        )
    )
    assert isinstance(client.metadata("https://e.com/"), MetadataResult)


@respx.mock
def test_api_error_raised(client):
    respx.post(f"{DEFAULT_BASE_URL}/v1/read").mock(
        return_value=httpx.Response(
            422, json={"error": {"code": "no_content", "message": "Too short."}}
        )
    )
    with pytest.raises(Web2MDError) as ei:
        client.read("https://e.com/")
    assert (ei.value.code, ei.value.status) == ("no_content", 422)


@respx.mock
def test_gateway_error_raised(client):
    respx.post(f"{DEFAULT_BASE_URL}/v1/read").mock(
        return_value=httpx.Response(403, json={"message": "You are not subscribed to this API."})
    )
    with pytest.raises(Web2MDError) as ei:
        client.read("https://e.com/")
    assert ei.value.code == "rapidapi_auth"
    assert "subscribed" in ei.value.message


@respx.mock
def test_timeout_and_network_errors(client):
    respx.post(f"{DEFAULT_BASE_URL}/v1/read").mock(side_effect=httpx.ReadTimeout("slow"))
    with pytest.raises(Web2MDError) as ei:
        client.read("https://e.com/")
    assert ei.value.code == "timeout" and ei.value.status is None
    respx.post(f"{DEFAULT_BASE_URL}/v1/read").mock(side_effect=httpx.ConnectError("refused"))
    with pytest.raises(Web2MDError) as ei:
        client.read("https://e.com/")
    assert ei.value.code == "network_error"


@respx.mock
def test_non_json_success_raises(client):
    respx.post(f"{DEFAULT_BASE_URL}/v1/read").mock(return_value=httpx.Response(200, text="oops"))
    with pytest.raises(Web2MDError) as ei:
        client.read("https://e.com/")
    assert ei.value.code == "invalid_response"


def test_missing_key_names_env_var(monkeypatch):
    monkeypatch.delenv("RAPIDAPI_KEY", raising=False)
    with pytest.raises(Web2MDError) as ei:
        Web2MD()
    assert ei.value.code == "missing_api_key"
    assert "RAPIDAPI_KEY" in ei.value.message


def test_key_from_env_and_not_in_repr(monkeypatch):
    monkeypatch.setenv("RAPIDAPI_KEY", "env-secret-123")
    c = Web2MD()
    assert "env-secret-123" not in repr(c)
    assert "env-secret-123" not in repr(c.__dict__.get("_http"))
    c.close()


@respx.mock
def test_custom_base_url_sets_host_header():
    route = respx.post("https://api.example.dev/v1/read").mock(
        return_value=httpx.Response(200, json=DOC)
    )
    with Web2MD(api_key="k", base_url="https://api.example.dev/") as c:
        c.read("https://e.com/")
    assert route.calls.last.request.headers["X-RapidAPI-Host"] == "api.example.dev"


def test_error_is_picklable():
    import pickle

    from web2md_client import Web2MDError

    for e in (
        Web2MDError("target_blocked", "Bot wall.", 502),
        Web2MDError("timeout", "slow", None),
    ):
        r = pickle.loads(pickle.dumps(e))
        assert (r.code, r.message, r.status, str(r)) == (e.code, e.message, e.status, str(e))
