from __future__ import annotations

import os
from typing import Any

import httpx

from web2md_client._errors import Web2MDError, error_from_response
from web2md_client._models import ChunksResult, Document, Format, MetadataResult

DEFAULT_BASE_URL = "https://web2md-webpage-to-markdown-rag-chunks.p.rapidapi.com"
_VERSION = "0.1.0"


def _flags(
    include_links: bool | None, include_images: bool | None, include_tables: bool | None
) -> dict[str, bool]:
    raw = {
        "include_links": include_links,
        "include_images": include_images,
        "include_tables": include_tables,
    }
    return {k: v for k, v in raw.items() if v is not None}


def _chunks_body(
    url: str | None,
    html: str | None,
    max_tokens: int,
    overlap_tokens: int,
    flags: dict[str, bool],
) -> dict[str, Any]:
    if (url is None) == (html is None):
        raise ValueError("Pass exactly one of url or html.")
    source = {"url": url} if url is not None else {"html": html}
    return {**source, "max_tokens": max_tokens, "overlap_tokens": overlap_tokens, **flags}


class _Base:
    def __init__(self, api_key: str | None, base_url: str, timeout: float) -> None:
        key = api_key or os.environ.get("RAPIDAPI_KEY")
        if not key:
            raise Web2MDError(
                "missing_api_key",
                "No API key. Pass api_key=... or set the RAPIDAPI_KEY environment variable "
                "(get a free key at "
                "https://rapidapi.com/kanavsingla28/api/web2md-webpage-to-markdown-rag-chunks).",
                None,
            )
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._headers = {
            "X-RapidAPI-Key": key,
            "X-RapidAPI-Host": httpx.URL(self._base_url).host,
            "User-Agent": f"web2md-client-python/{_VERSION}",
        }

    def __repr__(self) -> str:
        return f"{type(self).__name__}(base_url={self._base_url!r})"

    @staticmethod
    def _parse(response: httpx.Response) -> dict[str, Any]:
        if response.status_code >= 400:
            raise error_from_response(response.status_code, response.text)
        try:
            data = response.json()
        except ValueError:
            data = None
        if not isinstance(data, dict):
            raise Web2MDError(
                "invalid_response", "The API returned a non-JSON body.", response.status_code
            )
        return data

    @staticmethod
    def _transport_error(exc: httpx.HTTPError) -> Web2MDError:
        if isinstance(exc, httpx.TimeoutException):
            return Web2MDError("timeout", str(exc) or "The request timed out.", None)
        return Web2MDError("network_error", str(exc) or type(exc).__name__, None)


class Web2MD(_Base):
    """Synchronous Web2MD client."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        super().__init__(api_key, base_url, timeout)
        self._http = http_client or httpx.Client(timeout=timeout)

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self._http.post(self._base_url + path, json=body, headers=self._headers)
        except httpx.HTTPError as exc:
            raise self._transport_error(exc) from exc
        return self._parse(response)

    def read(
        self,
        url: str,
        *,
        format: Format = "markdown",
        include_links: bool | None = None,
        include_images: bool | None = None,
        include_tables: bool | None = None,
    ) -> Document:
        body = {
            "url": url,
            "format": format,
            **_flags(include_links, include_images, include_tables),
        }
        return Document.from_dict(self._post("/v1/read", body))

    def convert(
        self,
        html: str,
        *,
        url: str | None = None,
        format: Format = "markdown",
        include_links: bool | None = None,
        include_images: bool | None = None,
        include_tables: bool | None = None,
    ) -> Document:
        body: dict[str, Any] = {"html": html}
        if url is not None:
            body["url"] = url
        body |= {"format": format, **_flags(include_links, include_images, include_tables)}
        return Document.from_dict(self._post("/v1/convert", body))

    def chunks(
        self,
        url: str | None = None,
        *,
        html: str | None = None,
        max_tokens: int = 512,
        overlap_tokens: int = 50,
        include_links: bool | None = None,
        include_images: bool | None = None,
        include_tables: bool | None = None,
    ) -> ChunksResult:
        body = _chunks_body(
            url,
            html,
            max_tokens,
            overlap_tokens,
            _flags(include_links, include_images, include_tables),
        )
        return ChunksResult.from_dict(self._post("/v1/chunks", body))

    def metadata(self, url: str) -> MetadataResult:
        return MetadataResult.from_dict(self._post("/v1/metadata", {"url": url}))

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> Web2MD:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


class AsyncWeb2MD(_Base):
    """Asynchronous Web2MD client."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 30.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(api_key, base_url, timeout)
        self._http = http_client or httpx.AsyncClient(timeout=timeout)

    async def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        try:
            response = await self._http.post(
                self._base_url + path, json=body, headers=self._headers
            )
        except httpx.HTTPError as exc:
            raise self._transport_error(exc) from exc
        return self._parse(response)

    async def read(
        self,
        url: str,
        *,
        format: Format = "markdown",
        include_links: bool | None = None,
        include_images: bool | None = None,
        include_tables: bool | None = None,
    ) -> Document:
        body = {
            "url": url,
            "format": format,
            **_flags(include_links, include_images, include_tables),
        }
        return Document.from_dict(await self._post("/v1/read", body))

    async def convert(
        self,
        html: str,
        *,
        url: str | None = None,
        format: Format = "markdown",
        include_links: bool | None = None,
        include_images: bool | None = None,
        include_tables: bool | None = None,
    ) -> Document:
        body: dict[str, Any] = {"html": html}
        if url is not None:
            body["url"] = url
        body |= {"format": format, **_flags(include_links, include_images, include_tables)}
        return Document.from_dict(await self._post("/v1/convert", body))

    async def chunks(
        self,
        url: str | None = None,
        *,
        html: str | None = None,
        max_tokens: int = 512,
        overlap_tokens: int = 50,
        include_links: bool | None = None,
        include_images: bool | None = None,
        include_tables: bool | None = None,
    ) -> ChunksResult:
        body = _chunks_body(
            url,
            html,
            max_tokens,
            overlap_tokens,
            _flags(include_links, include_images, include_tables),
        )
        return ChunksResult.from_dict(await self._post("/v1/chunks", body))

    async def metadata(self, url: str) -> MetadataResult:
        return MetadataResult.from_dict(await self._post("/v1/metadata", {"url": url}))

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> AsyncWeb2MD:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()
