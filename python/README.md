# web2md-client (Python)

Turn any web page into clean Markdown and heading-aware RAG chunks with the [Web2MD API](https://rapidapi.com/kanavsingla28/api/web2md-webpage-to-markdown-rag-chunks). The free BASIC plan allows 500 requests/month; PRO is $9/month for 10,000.

## Install

```bash
pip install web2md-client
pip install "web2md-client[langchain]"    # LangChain document loader
pip install "web2md-client[llamaindex]"   # LlamaIndex reader
```

Requires Python 3.10+. Get a key from the RapidAPI listing above and export it as `RAPIDAPI_KEY`.

## Quickstart

```python
from web2md_client import Web2MD

with Web2MD() as w:  # reads RAPIDAPI_KEY
    doc = w.read("https://example.com")
    print(doc.metadata.title, doc.tokens)
    print(doc.markdown)
    for chunk in w.chunks("https://example.com", max_tokens=512).chunks:
        print(chunk.heading_path, chunk.tokens)
```

Other methods: `convert(html, url=None)` for HTML you already have, and `metadata(url)` for page metadata only.

Async:

```py
import asyncio
from web2md_client import AsyncWeb2MD


async def main():
    async with AsyncWeb2MD() as w:
        doc = await w.read("https://example.com")
        print(doc.markdown)


asyncio.run(main())
```

## RAG over any website in 10 lines

No LLM key needed; embeddings run locally with FastEmbed.

```python
# pip install "web2md-client[langchain]" langchain-community fastembed
# export RAPIDAPI_KEY=...  (free key: https://rapidapi.com/kanavsingla28/api/web2md-webpage-to-markdown-rag-chunks)
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore

from web2md_client.langchain import Web2MDLoader

docs = Web2MDLoader(["https://en.wikipedia.org/wiki/Retrieval-augmented_generation"], max_tokens=400).load()
store = InMemoryVectorStore.from_documents(docs, FastEmbedEmbeddings())
for hit in store.similarity_search("What problem does RAG solve?", k=3):
    print(f"[{hit.metadata['heading_path'] or hit.metadata.get('title', '')}]", hit.page_content[:300], "\n")
```

## LlamaIndex

```py
from llama_index.core import VectorStoreIndex
from web2md_client.llamaindex import Web2MDReader

docs = Web2MDReader(mode="chunks", max_tokens=400).load_data(["https://example.com"])
index = VectorStoreIndex.from_documents(docs)
print(index.as_query_engine().query("What is this page about?"))
```

## Loader metadata

In `chunks` mode (the default), every LangChain `Document` / LlamaIndex node carries:

| Key | Meaning |
| --- | --- |
| `source` | The page URL |
| `title` | Page title |
| `heading_path` | Heading trail of the chunk, joined with `" > "` |
| `chunk_id` | Chunk identifier |
| `tokens` | Token count of the chunk |

In `read` mode the keys are `source`, `title`, `tokens`, `word_count`, `author`, `published`, `description`, `language` and `site_name`. Keys with no value are omitted.

## Errors

Every failure raises `Web2MDError` with `.code`, `.message` and `.status` (HTTP status, or `None` for client-side failures).

```py
from web2md_client import Web2MD, Web2MDError

try:
    Web2MD().read("https://example.com")
except Web2MDError as e:
    print(e.code, e.status, e.message)
```

| Code | Status | Meaning |
| --- | --- | --- |
| `invalid_url` | 4xx | The URL is malformed or not http(s) |
| `blocked_destination` | 4xx | The URL points to a disallowed destination |
| `dns_error` | 4xx | The host could not be resolved |
| `robots_disallowed` | 403 | The site's robots.txt forbids fetching |
| `page_too_large` | 413 | The page exceeds the size limit |
| `unsupported_content_type` | 415 | The URL is not an HTML page |
| `invalid_request` | 422 | The request parameters are invalid |
| `no_content` | 422 | No readable content could be extracted |
| `host_rate_limited` | 429 | The target host is rate limiting us |
| `target_blocked` | 502 | The target site refused the fetch |
| `target_error` | 502 | The target site returned an error |
| `fetch_failed` | 502 | The page could not be fetched |
| `too_many_redirects` | 502 | Redirect limit exceeded |
| `fetch_timeout` | 504 | The target site took too long |
| `rapidapi_auth` | 401/403 | Gateway rejected the key or you are not subscribed |
| `rapidapi_rate_limited` | 429 | Your plan's quota or rate limit is used up |
| `missing_api_key` | none | No `api_key` argument and `RAPIDAPI_KEY` is not set |
| `timeout` | none | The request exceeded the client timeout |
| `network_error` | none | Connection failed |
| `http_error` | any | Unexpected HTTP error |
| `invalid_response` | any | The response could not be parsed |

Loaders (`Web2MDLoader`, `Web2MDReader`) raise on the first failure by default. Pass `continue_on_failure=True` to skip failing URLs and keep loading the rest.

## Licence

MIT
