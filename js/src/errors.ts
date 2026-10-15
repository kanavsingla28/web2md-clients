export class Web2MDError extends Error {
  readonly code: string;
  readonly status: number | null;

  constructor(code: string, message: string, status: number | null, options?: { cause?: unknown }) {
    super(message, options);
    this.name = "Web2MDError";
    this.code = code;
    this.status = status;
  }
}

function gatewayCode(status: number): string {
  if (status === 401 || status === 403) return "rapidapi_auth";
  if (status === 429) return "rapidapi_rate_limited";
  return "http_error";
}

export function errorFromResponse(status: number, data: unknown, text: string): Web2MDError {
  if (data && typeof data === "object") {
    const err = (data as { error?: unknown }).error;
    if (err && typeof err === "object") {
      const e = err as { code?: unknown; message?: unknown };
      return new Web2MDError(String(e.code ?? "unknown_error"), String(e.message ?? ""), status);
    }
    const msg = (data as { message?: unknown }).message;
    if (typeof msg === "string") return new Web2MDError(gatewayCode(status), msg, status);
  }
  return new Web2MDError(gatewayCode(status), text.trim().slice(0, 300) || `HTTP ${status}`, status);
}
