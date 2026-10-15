import pytest
from llama_index.core.readers.base import BaseReader
from llama_index.core.schema import Document

from tests.test_records import FakeClient
from web2md_client import Web2MDError
from web2md_client.llamaindex import Web2MDReader


def test_reader_chunks():
    reader = Web2MDReader(max_tokens=200, client=FakeClient())
    assert isinstance(reader, BaseReader)
    docs = reader.load_data(["https://a/"])
    assert all(isinstance(d, Document) for d in docs)
    assert [d.text for d in docs] == ["intro", "body"]
    assert docs[1].metadata["heading_path"] == "A > B"
    assert docs[1].id_ == "https://a/final#1"


def test_reader_read_mode_and_string_url():
    docs = Web2MDReader(mode="read", client=FakeClient()).load_data("https://a/")
    assert len(docs) == 1 and docs[0].id_ == "https://a/"
    assert docs[0].metadata["language"] == "en"


def test_reader_failure_modes():
    class Failing(FakeClient):
        def chunks(self, url, **kw):
            raise Web2MDError("target_blocked", "Bot wall.", 502)

    with pytest.raises(Web2MDError, match="https://a/"):
        Web2MDReader(client=Failing()).load_data(["https://a/"])
    assert Web2MDReader(client=Failing(), continue_on_failure=True).load_data(["https://a/"]) == []
