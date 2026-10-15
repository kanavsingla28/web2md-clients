import os
import runpy
from pathlib import Path

import pytest

from web2md_client import Web2MD

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(not os.environ.get("RAPIDAPI_KEY"), reason="RAPIDAPI_KEY not set"),
]
URL = "https://en.wikipedia.org/wiki/Retrieval-augmented_generation"


def test_read_markdown():
    with Web2MD() as w:
        doc = w.read(URL)
    assert doc.markdown and doc.word_count > 200 and doc.metadata.title


def test_chunks_respect_max_tokens():
    with Web2MD() as w:
        result = w.chunks(URL, max_tokens=256, overlap_tokens=0)
    assert len(result.chunks) > 3
    assert all(c.tokens <= 256 for c in result.chunks)


def test_langchain_loader():
    from web2md_client.langchain import Web2MDLoader

    docs = Web2MDLoader(URL, max_tokens=400).load()
    assert docs and docs[0].metadata["source"].startswith("https://en.wikipedia.org/")


def test_readme_example_runs(capsys):
    pytest.importorskip("fastembed")
    runpy.run_path(str(Path(__file__).parents[2] / "examples" / "rag_in_10_lines.py"))
    assert "[" in capsys.readouterr().out


def test_llamaindex_example_runs(capsys):
    pytest.importorskip("llama_index.embeddings.fastembed")
    runpy.run_path(str(Path(__file__).parents[2] / "examples" / "llamaindex_retriever.py"))
    assert capsys.readouterr().out.strip()
