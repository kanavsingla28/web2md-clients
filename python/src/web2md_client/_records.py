from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal

Mode = Literal["chunks", "read"]
Record = tuple[str, dict[str, Any]]
_READ_META = ("author", "published", "description", "language", "site_name")


def check_mode(mode: str) -> Mode:
    if mode not in ("chunks", "read"):
        raise ValueError(f"mode must be 'chunks' or 'read', got {mode!r}")
    return mode  # type: ignore[return-value]


def normalize_urls(urls: str | Sequence[str]) -> list[str]:
    return [urls] if isinstance(urls, str) else list(urls)


def extraction_flags(
    include_links: bool | None, include_images: bool | None, include_tables: bool | None
) -> dict[str, bool]:
    given = {
        "include_links": include_links,
        "include_images": include_images,
        "include_tables": include_tables,
    }
    return {k: v for k, v in given.items() if v is not None}


def _clean(meta: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in meta.items() if v is not None}


def chunk_records(result: Any, url: str) -> list[Record]:
    source = result.url or url
    return [
        (
            c.text,
            _clean(
                {
                    "source": source,
                    "title": result.title,
                    "heading_path": " > ".join(c.heading_path),
                    "chunk_id": c.id,
                    "tokens": c.tokens,
                }
            ),
        )
        for c in result.chunks
    ]


def read_record(doc: Any, url: str) -> Record:
    meta = {
        "source": doc.url or url,
        "title": doc.metadata.title,
        "tokens": doc.tokens,
        "word_count": doc.word_count,
    }
    meta |= {k: getattr(doc.metadata, k) for k in _READ_META}
    return (doc.markdown or doc.text or "", _clean(meta))


def iter_records(
    client: Any,
    url: str,
    mode: Mode,
    max_tokens: int,
    overlap_tokens: int,
    flags: dict[str, bool] | None = None,
) -> list[Record]:
    if mode == "chunks":
        return chunk_records(
            client.chunks(
                url, max_tokens=max_tokens, overlap_tokens=overlap_tokens, **(flags or {})
            ),
            url,
        )
    return [read_record(client.read(url, format="markdown", **(flags or {})), url)]


async def aiter_records(
    client: Any,
    url: str,
    mode: Mode,
    max_tokens: int,
    overlap_tokens: int,
    flags: dict[str, bool] | None = None,
) -> list[Record]:
    if mode == "chunks":
        return chunk_records(
            await client.chunks(
                url, max_tokens=max_tokens, overlap_tokens=overlap_tokens, **(flags or {})
            ),
            url,
        )
    return [read_record(await client.read(url, format="markdown", **(flags or {})), url)]
