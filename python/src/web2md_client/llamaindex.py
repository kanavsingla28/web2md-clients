"""LlamaIndex reader for Web2MD. Install with: pip install "web2md-client[llamaindex]"."""

from __future__ import annotations

import logging
from collections.abc import Iterator, Sequence
from typing import Any

try:
    from llama_index.core.readers.base import BaseReader
    from llama_index.core.schema import Document
except ImportError as exc:  # pragma: no cover - exercised via test_optional_imports
    raise ImportError(
        'web2md_client.llamaindex needs llama-index-core: pip install "web2md-client[llamaindex]"'
    ) from exc

from web2md_client._client import Web2MD
from web2md_client._errors import Web2MDError
from web2md_client._records import Mode, check_mode, extraction_flags, iter_records, normalize_urls

logger = logging.getLogger(__name__)


class Web2MDReader(BaseReader):
    """Read web pages into LlamaIndex Documents: one per heading-aware chunk, or one per page."""

    def __init__(
        self,
        mode: Mode = "chunks",
        max_tokens: int = 512,
        overlap_tokens: int = 50,
        *,
        api_key: str | None = None,
        client: Any = None,
        continue_on_failure: bool = False,
        include_links: bool | None = None,
        include_images: bool | None = None,
        include_tables: bool | None = None,
    ) -> None:
        self.mode = check_mode(mode)
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.continue_on_failure = continue_on_failure
        self._flags = extraction_flags(include_links, include_images, include_tables)
        self._api_key = api_key
        self._client = client

    def lazy_load_data(self, urls: str | Sequence[str]) -> Iterator[Document]:  # type: ignore[override]
        client = self._client or Web2MD(api_key=self._api_key)
        try:
            for url in normalize_urls(urls):
                try:
                    records = iter_records(
                        client, url, self.mode, self.max_tokens, self.overlap_tokens, self._flags
                    )
                except Web2MDError as exc:
                    if not self.continue_on_failure:
                        raise Web2MDError(exc.code, f"{url}: {exc.message}", exc.status) from exc
                    logger.warning("Web2MD skipped %s: %s", url, exc)
                    continue
                for text, meta in records:
                    doc_id = (
                        f"{meta['source']}#{meta['chunk_id']}"
                        if "chunk_id" in meta
                        else meta["source"]
                    )
                    yield Document(
                        text=text,
                        metadata=meta,
                        id_=doc_id,
                        excluded_embed_metadata_keys=["source", "chunk_id", "tokens"],
                        excluded_llm_metadata_keys=["chunk_id", "tokens"],
                    )
        finally:
            if self._client is None:
                client.close()

    def load_data(self, urls: str | Sequence[str]) -> list[Document]:  # type: ignore[override]
        return list(self.lazy_load_data(urls))
