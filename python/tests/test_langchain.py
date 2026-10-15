import logging

import pytest
from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document as LCDocument

from tests.test_records import FakeClient
from web2md_client import Web2MDError
from web2md_client.langchain import Web2MDLoader


def test_is_base_loader_and_loads_chunks():
    fake = FakeClient()
    loader = Web2MDLoader(["https://a/", "https://b/"], max_tokens=300, client=fake)
    assert isinstance(loader, BaseLoader)
    docs = loader.load()
    assert len(docs) == 4 and all(isinstance(d, LCDocument) for d in docs)
    assert docs[1].metadata["heading_path"] == "A > B"
    assert fake.calls[0] == ("chunks", "https://a/", 300, 50)


def test_read_mode_one_doc_per_url():
    docs = Web2MDLoader("https://a/", mode="read", client=FakeClient()).load()
    assert len(docs) == 1 and docs[0].page_content == "# Page"


def test_bad_mode():
    with pytest.raises(ValueError):
        Web2MDLoader("https://a/", mode="markdown", client=FakeClient())


class Failing(FakeClient):
    def chunks(self, url, **kw):
        if "bad" in url:
            raise Web2MDError("robots_disallowed", "Disallowed.", 403)
        return super().chunks(url, **kw)


def test_failure_raises_naming_url():
    with pytest.raises(Web2MDError) as ei:
        Web2MDLoader(["https://bad/", "https://a/"], client=Failing()).load()
    assert "https://bad/" in str(ei.value)


def test_continue_on_failure_skips(caplog):
    with caplog.at_level(logging.WARNING):
        docs = Web2MDLoader(
            ["https://bad/", "https://a/"], client=Failing(), continue_on_failure=True
        ).load()
    assert len(docs) == 2
    assert "https://bad/" in caplog.text


async def test_alazy_load_uses_async_client():
    class AsyncFake:
        async def chunks(self, url, *, max_tokens, overlap_tokens):
            return FakeClient().chunks(url, max_tokens=max_tokens, overlap_tokens=overlap_tokens)

    docs = [d async for d in Web2MDLoader("https://a/", async_client=AsyncFake()).alazy_load()]
    assert [d.page_content for d in docs] == ["intro", "body"]
