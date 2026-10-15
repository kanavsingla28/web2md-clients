# web2md-client (TypeScript)

Turn any web page into clean Markdown and heading-aware RAG chunks with the [Web2MD API](https://rapidapi.com/kanavsingla28/api/web2md-webpage-to-markdown-rag-chunks). The free BASIC plan allows 500 requests/month; PRO is $9/month for 10,000.

## Install

```bash
npm install web2md-client
```

Works in Node 20+ and any runtime with `fetch`. ESM and CommonJS builds are included.

## Quickstart

```ts
import { Web2MD } from "web2md-client";

const w = new Web2MD(); // reads RAPIDAPI_KEY, or pass { apiKey }
const doc = await w.read({ url: "https://example.com" });
console.log(doc.metadata.title, doc.tokens);
console.log(doc.markdown);

const { chunks } = await w.chunks({ url: "https://example.com", max_tokens: 512 });
for (const c of chunks) console.log(c.heading_path, c.tokens);
```

Also available: `convert({ html, url? })` and `metadata({ url })`. Field names are snake_case, as in the API. Options: `new Web2MD({ apiKey, baseUrl, timeoutMs, fetch })`.

## Error handling

```ts
import { Web2MD, Web2MDError } from "web2md-client";

try {
  await new Web2MD().read({ url: "https://example.com" });
} catch (err) {
  if (err instanceof Web2MDError) {
    console.error(err.code, err.status, err.message);
  } else {
    throw err;
  }
}
```

Common codes: `invalid_url`, `robots_disallowed`, `page_too_large`, `no_content`, `host_rate_limited`, `fetch_failed`, `fetch_timeout`, plus client-side `rapidapi_auth`, `rapidapi_rate_limited`, `timeout`, `network_error` and `missing_api_key`.

## Keep your key server-side

Your RapidAPI key is a secret. Call Web2MD from your backend or a serverless function, never from browser code, or anyone can read the key from your bundle and spend your quota.

Get a key from the [RapidAPI listing](https://rapidapi.com/kanavsingla28/api/web2md-webpage-to-markdown-rag-chunks).

## Licence

MIT
