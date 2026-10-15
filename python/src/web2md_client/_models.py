from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any, Literal

Format = Literal["markdown", "text", "json"]


def _known(cls: type, data: dict[str, Any]) -> dict[str, Any]:
    names = {f.name for f in fields(cls)}
    return {k: v for k, v in data.items() if k in names}


@dataclass(frozen=True)
class Metadata:
    word_count: int = 0
    reading_time_min: int = 0
    title: str | None = None
    author: str | None = None
    published: str | None = None
    description: str | None = None
    site_name: str | None = None
    language: str | None = None
    canonical_url: str | None = None
    image: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Metadata:
        return cls(**_known(cls, data))


@dataclass(frozen=True)
class MetadataResult(Metadata):
    url: str = ""
    cached: bool = False
    raw: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MetadataResult:
        return cls(**{**_known(cls, data), "raw": data})


@dataclass(frozen=True)
class Document:
    format: str
    metadata: Metadata
    word_count: int
    tokens: int
    cached: bool
    rendered: bool
    url: str | None = None
    markdown: str | None = None
    text: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Document:
        kw = _known(cls, data)
        kw["metadata"] = Metadata.from_dict(data.get("metadata") or {})
        return cls(**{**kw, "raw": data})


@dataclass(frozen=True)
class Chunk:
    id: int
    heading_path: list[str]
    text: str
    tokens: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Chunk:
        return cls(**_known(cls, data))


@dataclass(frozen=True)
class ChunksResult:
    chunks: list[Chunk]
    total_tokens: int
    cached: bool
    url: str | None = None
    title: str | None = None
    lang: str | None = None
    published: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChunksResult:
        kw = _known(cls, data)
        kw["chunks"] = [Chunk.from_dict(c) for c in data.get("chunks") or []]
        return cls(**{**kw, "raw": data})
