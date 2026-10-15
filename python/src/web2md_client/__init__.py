"""Python client for the Web2MD API."""

from web2md_client._errors import Web2MDError
from web2md_client._models import Chunk, ChunksResult, Document, Format, Metadata, MetadataResult

__version__ = "0.1.0"

__all__ = [
    "Chunk",
    "ChunksResult",
    "Document",
    "Format",
    "Metadata",
    "MetadataResult",
    "Web2MDError",
    "__version__",
]
