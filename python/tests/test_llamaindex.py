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


@pytest.mark.parametrize("mode", ["chunks", "read"])
def test_reader_forwards_only_set_flags(mode):
    fake = FakeClient()
    Web2MDReader(mode=mode, client=fake, include_tables=True, include_images=False).load_data(
        "https://a/"
    )
    assert fake.flags == [{"include_tables": True, "include_images": False}]
    fake = FakeClient()
    Web2MDReader(mode=mode, client=fake).load_data("https://a/")
    assert fake.flags == [{}]


def test_chunk_embed_metadata_excludes_ids():
    from llama_index.core.schema import MetadataMode

    doc = Web2MDReader(client=FakeClient()).load_data("https://a/")[1]
    embed = doc.get_content(metadata_mode=MetadataMode.EMBED)
    assert "A > B" in embed and "chunk_id" not in embed and "source" not in embed
    llm = doc.get_content(metadata_mode=MetadataMode.LLM)
    assert "source" in llm and "chunk_id" not in llm and "tokens" not in llm
