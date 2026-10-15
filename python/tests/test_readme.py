import re
from pathlib import Path

import web2md_client
from web2md_client import _client

ROOT = Path(__file__).resolve().parents[1]


def _python_blocks(text: str) -> list[str]:
    return re.findall(r"```python\n(.*?)```", text, flags=re.S)


def test_readme_rag_example_matches_examples_file():
    example = (ROOT / "examples" / "rag_in_10_lines.py").read_text()
    assert example in _python_blocks((ROOT / "README.md").read_text())
    code_lines = [ln for ln in example.splitlines() if ln.strip() and not ln.startswith("#")]
    assert len(code_lines) <= 10


def test_versions_agree():
    assert _client._VERSION == web2md_client.__version__
    assert f'version = "{web2md_client.__version__}"' in (ROOT / "pyproject.toml").read_text()


def test_readme_llamaindex_example_matches_examples_file():
    example = (ROOT / "examples" / "llamaindex_retriever.py").read_text()
    assert example in re.findall(r"```py\n(.*?)```", (ROOT / "README.md").read_text(), flags=re.S)
