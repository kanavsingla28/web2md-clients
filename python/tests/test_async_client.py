import json

import httpx
import pytest
import respx

from web2md_client import DEFAULT_BASE_URL, AsyncWeb2MD, Web2MDError

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


@respx.mock
async def test_async_read_and_chunks():
    respx.post(f"{DEFAULT_BASE_URL}/v1/read").mock(return_value=httpx.Response(200, json=DOC))
    route = respx.post(f"{DEFAULT_BASE_URL}/v1/chunks").mock(
        return_value=httpx.Response(200, json={"chunks": [], "total_tokens": 0, "cached": False})
    )
    async with AsyncWeb2MD(api_key="k") as c:
        assert (await c.read("https://e.com/")).markdown == "# Hi"
        await c.chunks(html="<p>x</p>")
    assert json.loads(route.calls.last.request.content) == {
        "html": "<p>x</p>",
        "max_tokens": 512,
        "overlap_tokens": 50,
    }


@respx.mock
async def test_async_error():
    respx.post(f"{DEFAULT_BASE_URL}/v1/metadata").mock(
        return_value=httpx.Response(429, json={"message": "You have exceeded the MONTHLY quota"})
    )
    async with AsyncWeb2MD(api_key="k") as c:
        with pytest.raises(Web2MDError) as ei:
            await c.metadata("https://e.com/")
    assert ei.value.code == "rapidapi_rate_limited"
