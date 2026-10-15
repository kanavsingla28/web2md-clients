# web2md-clients

Official Python and TypeScript clients for the [Web2MD API](https://rapidapi.com/kanavsingla28/api/web2md-webpage-to-markdown-rag-chunks): turn any web page into clean Markdown and heading-aware RAG chunks. The free BASIC plan allows 500 requests/month; PRO is $9/month for 10,000.

| Package | Registry | Docs |
| --- | --- | --- |
| [`python/`](python/) | PyPI `web2md-client` (import `web2md_client`) | [python/README.md](python/README.md) |
| [`js/`](js/) | npm `web2md-client` | [js/README.md](js/README.md) |

Both include typed responses. The LangChain and LlamaIndex integrations are Python-only (there are none in the TypeScript package). Get an API key from the [RapidAPI listing](https://rapidapi.com/kanavsingla28/api/web2md-webpage-to-markdown-rag-chunks).

## Development

```bash
# Python
cd python && uv sync --group dev && uv run pytest -q && uv run ruff check . && uv run ruff format --check .

# TypeScript
cd js && npm ci && npm run typecheck && npm test && npm run build

# Repo hygiene (no addresses or backend secrets in tracked files)
bash scripts/check-leaks.sh
```

## Licence

MIT
