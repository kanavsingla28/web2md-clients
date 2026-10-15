import { afterEach, describe, expect, it, vi } from "vitest";
import { DEFAULT_BASE_URL, Web2MD, Web2MDError } from "../src/index";

const DOC = {
  url: "https://e.com/", format: "markdown", markdown: "# Hi",
  metadata: { word_count: 1, reading_time_min: 1 },
  word_count: 1, tokens: 2, cached: false, rendered: false,
};

function mockFetch(status: number, body: unknown, raw = false) {
  return vi.fn(async (_url: string | URL | Request, _init?: RequestInit) =>
    new Response(raw ? (body as string) : JSON.stringify(body), { status }));
}

afterEach(() => vi.unstubAllEnvs());

describe("Web2MD", () => {
  it("sends headers and a minimal body", async () => {
    const f = mockFetch(200, DOC);
    const c = new Web2MD({ apiKey: "k", fetch: f });
    const doc = await c.read({ url: "https://e.com/" });
    expect(doc.markdown).toBe("# Hi");
    const [url, init] = f.mock.calls[0];
    expect(url).toBe(`${DEFAULT_BASE_URL}/v1/read`);
    const h = new Headers(init!.headers);
    expect(h.get("X-RapidAPI-Key")).toBe("k");
    expect(h.get("X-RapidAPI-Host")).toBe("web2md-webpage-to-markdown-rag-chunks.p.rapidapi.com");
    expect(h.get("Content-Type")).toBe("application/json");
    expect(JSON.parse(init!.body as string)).toEqual({ url: "https://e.com/" });
  });

  it("posts chunks, convert and metadata to the right paths", async () => {
    const f = mockFetch(200, { chunks: [], total_tokens: 0, cached: false });
    const c = new Web2MD({ apiKey: "k", fetch: f });
    await c.chunks({ html: "<p>x</p>", max_tokens: 128 });
    await c.convert({ html: "<p>x</p>" });
    await c.metadata({ url: "https://e.com/" });
    expect(f.mock.calls.map(([u]) => String(u).replace(DEFAULT_BASE_URL, ""))).toEqual(
      ["/v1/chunks", "/v1/convert", "/v1/metadata"]);
    expect(JSON.parse(f.mock.calls[0][1]!.body as string)).toEqual({ html: "<p>x</p>", max_tokens: 128 });
  });

  it("maps API errors", async () => {
    const c = new Web2MD({ apiKey: "k", fetch: mockFetch(422, { error: { code: "no_content", message: "Short." } }) });
    await expect(c.read({ url: "https://e.com/" })).rejects.toMatchObject({ code: "no_content", status: 422, message: "Short." });
  });

  it("maps gateway errors", async () => {
    const c = new Web2MD({ apiKey: "k", fetch: mockFetch(403, { message: "You are not subscribed to this API." }) });
    const err = await c.read({ url: "https://e.com/" }).catch((e) => e);
    expect(err).toBeInstanceOf(Web2MDError);
    expect(err.code).toBe("rapidapi_auth");
    expect(err.message).toContain("subscribed");
  });

  it("maps non-JSON error bodies and 429 quota", async () => {
    const c1 = new Web2MD({ apiKey: "k", fetch: mockFetch(502, "<html>Bad Gateway</html>", true) });
    await expect(c1.read({ url: "u" })).rejects.toMatchObject({ code: "http_error", status: 502 });
    const c2 = new Web2MD({ apiKey: "k", fetch: mockFetch(429, { message: "quota" }) });
    await expect(c2.read({ url: "u" })).rejects.toMatchObject({ code: "rapidapi_rate_limited" });
  });

  it("maps network failure and timeout", async () => {
    const net = vi.fn(async () => { throw new TypeError("fetch failed"); });
    await expect(new Web2MD({ apiKey: "k", fetch: net }).read({ url: "u" }))
      .rejects.toMatchObject({ code: "network_error", status: null });
    const slow = vi.fn(async () => { throw new DOMException("timed out", "TimeoutError"); });
    await expect(new Web2MD({ apiKey: "k", fetch: slow }).read({ url: "u" }))
      .rejects.toMatchObject({ code: "timeout" });
  });

  it("rejects a non-JSON success body", async () => {
    const c = new Web2MD({ apiKey: "k", fetch: mockFetch(200, "oops", true) });
    await expect(c.read({ url: "u" })).rejects.toMatchObject({ code: "invalid_response" });
  });

  it("reads RAPIDAPI_KEY and fails clearly without it", () => {
    vi.stubEnv("RAPIDAPI_KEY", "");
    expect(() => new Web2MD()).toThrow(/RAPIDAPI_KEY/);
    vi.stubEnv("RAPIDAPI_KEY", "env-secret-123");
    const c = new Web2MD({ fetch: mockFetch(200, DOC) });
    expect(JSON.stringify(c)).not.toContain("env-secret-123");
  });

  it("derives the host header from a custom baseUrl", async () => {
    const f = mockFetch(200, DOC);
    await new Web2MD({ apiKey: "k", baseUrl: "https://api.example.dev/", fetch: f }).read({ url: "u" });
    expect(f.mock.calls[0][0]).toBe("https://api.example.dev/v1/read");
    expect(new Headers(f.mock.calls[0][1]!.headers).get("X-RapidAPI-Host")).toBe("api.example.dev");
  });
});
