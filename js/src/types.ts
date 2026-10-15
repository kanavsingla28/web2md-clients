export type Format = "markdown" | "text" | "json";

export interface ExtractFlags {
  include_links?: boolean;
  include_images?: boolean;
  include_tables?: boolean;
}

export interface ReadParams extends ExtractFlags { url: string; format?: Format }
export interface ConvertParams extends ExtractFlags { html: string; url?: string; format?: Format }
export type ChunksParams = ExtractFlags & { max_tokens?: number; overlap_tokens?: number } &
  ({ url: string; html?: never } | { html: string; url?: never });
export interface MetadataParams { url: string }

export interface Metadata {
  title?: string; author?: string; published?: string; description?: string;
  site_name?: string; language?: string; canonical_url?: string; image?: string;
  word_count: number; reading_time_min: number;
}

export interface Document {
  url?: string; format: Format; markdown?: string; text?: string; metadata: Metadata;
  word_count: number; tokens: number; cached: boolean; rendered: boolean;
}

export interface Chunk { id: number; heading_path: string[]; text: string; tokens: number }

export interface ChunksResult {
  url?: string; title?: string; lang?: string; published?: string;
  chunks: Chunk[]; total_tokens: number; cached: boolean;
}

export interface MetadataResult extends Metadata { url: string; cached: boolean }
