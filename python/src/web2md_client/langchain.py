"""LangChain document loader for Web2MD. Install with: pip install "web2md-client[langchain]"."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Iterator, Sequence
from typing import Any

try:
    from langchain_core.document_loaders import BaseLoader
    from langchain_core.documents import Document
except ImportError as exc:  # pragma: no cover - exercised via test_optional_imports
    raise ImportError(
        'web2md_client.langchain needs langchain-core: pip install "web2md-client[langchain]"'
    ) from exc

from web2md_client._client import AsyncWeb2MD, Web2MD
from web2md_client._errors import Web2MDError
from web2md_client._records import (
    Mode,
    aiter_records,
    check_mode,
    extraction_flags,
    iter_records,
    normalize_urls,
)

logger = logging.getLogger(__name__)


class Web2MDLoader(BaseLoader):
    """Load web pages as LangChain Documents: one per heading-aware chunk, or one per page."""

    def __init__(
        self,
        urls: str | Sequence[str],
        mode: Mode = "chunks",
        max_tokens: int = 512,
        overlap_tokens: int = 50,
        *,
        api_key: str | None = None,
        client: Any = None,
        async_client: Any = None,
        continue_on_failure: bool = False,
        include_links: bool | None = None,
        include_images: bool | None = None,
        include_tables: bool | None = None,
    ) -> None:
        self.urls = normalize_urls(urls)
        self.mode = check_mode(mode)
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        self.continue_on_failure = continue_on_failure
        self._flags = extraction_flags(include_links, include_images, include_tables)
        self._api_key = api_key
        self._client = client
        self._async_client = async_client

    def _failed(self, url: str, exc: Web2MDError) -> None:
        if not self.continue_on_failure:
            raise Web2MDError(exc.code, f"{url}: {exc.message}", exc.status) from exc
        logger.warning("Web2MD skipped %s: %s", url, exc)

    def lazy_load(self) -> Iterator[Document]:
        client = self._client or Web2MD(api_key=self._api_key)
        try:
            for url in self.urls:
                try:
                    records = iter_records(
                        client, url, self.mode, self.max_tokens, self.overlap_tokens, self._flags
                    )
                except Web2MDError as exc:
                    self._failed(url, exc)
                    continue
                for text, meta in records:
                    yield Document(page_content=text, metadata=meta)
        finally:
            if self._client is None:
                client.close()

    async def alazy_load(self) -> AsyncIterator[Document]:
        client = self._async_client or AsyncWeb2MD(api_key=self._api_key)
        try:
            for url in self.urls:
                try:
                    records = await aiter_records(
                        client, url, self.mode, self.max_tokens, self.overlap_tokens, self._flags
                    )
                except Web2MDError as exc:
                    self._failed(url, exc)
                    continue
                for text, meta in records:
                    yield Document(page_content=text, metadata=meta)
        finally:
            if self._async_client is None:
                await client.aclose()
