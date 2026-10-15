import { Web2MDError, errorFromResponse } from "./errors";
import type {
  ChunksParams, ChunksResult, ConvertParams, Document, MetadataParams, MetadataResult, ReadParams,
} from "./types";

export * from "./types";
export { Web2MDError } from "./errors";

export const DEFAULT_BASE_URL = "https://web2md-webpage-to-markdown-rag-chunks.p.rapidapi.com";

export interface Web2MDOptions {
  /** Your RapidAPI key. Defaults to process.env.RAPIDAPI_KEY. Keep it server-side. */
  apiKey?: string;
  baseUrl?: string;
  /** Per-request timeout in milliseconds (default 30000). */
  timeoutMs?: number;
  fetch?: typeof globalThis.fetch;
}

function envKey(): string | undefined {
  return typeof process !== "undefined" ? process.env?.RAPIDAPI_KEY : undefined;
}

export class Web2MD {
  readonly #key: string;
  readonly #base: string;
  readonly #host: string;
  readonly #timeoutMs: number;
  readonly #fetch: typeof globalThis.fetch;

  constructor(options: Web2MDOptions = {}) {
    const key = options.apiKey || envKey();
    if (!key) {
      throw new Web2MDError(
        "missing_api_key",
        "No API key. Pass { apiKey } or set the RAPIDAPI_KEY environment variable " +
          "(get a free key at https://rapidapi.com/kanavsingla28/api/web2md-webpage-to-markdown-rag-chunks).",
        null,
      );
    }
    this.#key = key;
    this.#base = (options.baseUrl ?? DEFAULT_BASE_URL).replace(/\/+$/, "");
    this.#host = new URL(this.#base).host;
    this.#timeoutMs = options.timeoutMs ?? 30_000;
    this.#fetch = options.fetch ?? globalThis.fetch.bind(globalThis);
  }

  read(params: ReadParams): Promise<Document> { return this.#post("/v1/read", params); }
  convert(params: ConvertParams): Promise<Document> { return this.#post("/v1/convert", params); }
  chunks(params: ChunksParams): Promise<ChunksResult> { return this.#post("/v1/chunks", params); }
  metadata(params: MetadataParams): Promise<MetadataResult> { return this.#post("/v1/metadata", params); }

  async #post<T>(path: string, body: object): Promise<T> {
    let res: Response;
    try {
      res = await this.#fetch(this.#base + path, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-RapidAPI-Key": this.#key,
          "X-RapidAPI-Host": this.#host,
        },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(this.#timeoutMs),
      });
    } catch (e) {
      const name = (e as { name?: string })?.name;
      if (name === "TimeoutError" || name === "AbortError") {
        throw new Web2MDError("timeout", `Request timed out after ${this.#timeoutMs} ms.`, null);
      }
      throw new Web2MDError("network_error", (e as Error)?.message ?? String(e), null);
    }
    const text = await res.text();
    let data: unknown;
    try { data = text ? JSON.parse(text) : undefined; } catch { data = undefined; }
    if (!res.ok) throw errorFromResponse(res.status, data, text);
    if (!data || typeof data !== "object") {
      throw new Web2MDError("invalid_response", "The API returned a non-JSON body.", res.status);
    }
    return data as T;
  }
}
