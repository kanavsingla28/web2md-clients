import { describe, expect, it } from "vitest";
import { Web2MD } from "../src/index";

const live = process.env.WEB2MD_LIVE === "1" && !!process.env.RAPIDAPI_KEY;
const URL = "https://en.wikipedia.org/wiki/Retrieval-augmented_generation";

describe.skipIf(!live)("live API", () => {
  it("reads and chunks", async () => {
    const w = new Web2MD();
    const doc = await w.read({ url: URL });
    expect(doc.word_count).toBeGreaterThan(200);
    const { chunks } = await w.chunks({ url: URL, max_tokens: 256, overlap_tokens: 0 });
    expect(chunks.length).toBeGreaterThan(0);
    expect(chunks.every((c) => c.tokens <= 256)).toBe(true);
  }, 60_000);
});
