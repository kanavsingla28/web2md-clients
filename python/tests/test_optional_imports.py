import importlib
import subprocess
import sys

import pytest


def test_core_import_does_not_pull_frameworks():
    code = (
        "import sys, web2md_client; "
        "assert 'langchain_core' not in sys.modules; "
        "assert 'llama_index' not in sys.modules"
    )
    subprocess.run([sys.executable, "-c", code], check=True)


@pytest.mark.parametrize(
    "module,blocked,extra",
    [
        ("web2md_client.langchain", "langchain_core", "langchain"),
        ("web2md_client.llamaindex", "llama_index", "llamaindex"),
    ],
)
def test_missing_extra_gives_install_hint(monkeypatch, module, blocked, extra):
    for name in list(sys.modules):
        if name == blocked or name.startswith(blocked + ".") or name == module:
            monkeypatch.delitem(sys.modules, name)
    monkeypatch.setitem(sys.modules, blocked, None)
    with pytest.raises(ImportError, match=rf"web2md-client\[{extra}\]"):
        importlib.import_module(module)
