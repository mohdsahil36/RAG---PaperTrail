import type { UploadDocumentResponse } from "@/types/document";
import type { AskRequest, AskResponse, AskSource } from "@/types/ask";


/** Requests go through the Next.js rewrite in `next.config.ts` to the FastAPI backend. */
const API_PREFIX = "/api";

export class ApiError extends Error {
  constructor(
    message: string,
    /** Extra context, such as the backend's `detail` field. */
    readonly detail?: string,
    readonly status?: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export class UploadAbortedError extends Error {
  constructor() {
    super("Upload cancelled");
    this.name = "UploadAbortedError";
  }
}

interface UploadOptions {
  /** Called with a 0–1 fraction while the file is being sent. */
  onProgress?: (fraction: number) => void;
  signal?: AbortSignal;
}

/**
 * `POST /upload-document` with the PDF in the multipart field `file`.
 * Uses XMLHttpRequest because `fetch` does not report upload progress.
 */
export function uploadDocument(
  file: File,
  { onProgress, signal }: UploadOptions = {},
): Promise<UploadDocumentResponse> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(new UploadAbortedError());
      return;
    }

    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_PREFIX}/upload-document`);
    xhr.responseType = "text";

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress?.(event.loaded / event.total);
    };

    xhr.onload = () => {
      const body = parseJson(xhr.responseText);

      if (xhr.status >= 200 && xhr.status < 300) {
        if (isUploadResponse(body)) resolve(body);
        else reject(new ApiError("The server sent an unexpected response."));
        return;
      }

      reject(toApiError(xhr.status, body));
    };

    xhr.onerror = () =>
      reject(
        new ApiError(
          "Couldn't reach the server.",
          "Check your connection and that the API is running.",
        ),
      );
    xhr.onabort = () => reject(new UploadAbortedError());
    signal?.addEventListener("abort", () => xhr.abort(), { once: true });

    const form = new FormData();
    form.append("file", file);
    xhr.send(form);
  });
}

function toApiError(status: number, body: unknown): ApiError {
  const detail = readDetail(body);

  // A non-JSON 5xx comes from the Next.js proxy, not FastAPI: the backend is down.
  if (status >= 500 && detail === undefined) {
    return new ApiError(
      "Couldn't reach the document service.",
      "Make sure the FastAPI backend is running.",
      status,
    );
  }

  switch (status) {
    case 400:
      return new ApiError("This file can't be processed.", detail, status);
    case 413:
      return new ApiError("This file is too large to upload.", detail, status);
    case 422:
      return new ApiError("The upload was rejected.", detail, status);
    case 500:
      return new ApiError(
        "Text extraction failed.",
        "The file may be damaged, password-protected, or not a valid PDF.",
        status,
      );
    default:
      return new ApiError(`Upload failed (HTTP ${status}).`, detail, status);
  }
}

/** FastAPI returns `detail` as a string, or as a list of validation errors for 422s. */
function readDetail(body: unknown): string | undefined {
  if (!body || typeof body !== "object" || !("detail" in body)) return undefined;
  const { detail } = body as { detail: unknown };
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => (item && typeof item === "object" && "msg" in item ? String(item.msg) : ""))
      .filter(Boolean)
      .join("; ");
  }
  return undefined;
}

function parseJson(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return undefined;
  }
}

function isUploadResponse(body: unknown): body is UploadDocumentResponse {
  if (!body || typeof body !== "object") return false;
  const { filename, pages } = body as Record<string, unknown>;
  return (
    typeof filename === "string" &&
    Array.isArray(pages) &&
    pages.every(
      (page) =>
        page &&
        typeof page === "object" &&
        typeof page.page_number === "number" &&
        typeof page.text === "string",
    )
  );
}

interface StreamCallbacks {
  onToken: (text: string) => void;
  onDone: (found: boolean, sources: AskSource[]) => void;
  onError: (message: string) => void;
}

/**
 * `POST /answer/stream` — SSE stream of token and done events.
 * Calls onToken for each text chunk, onDone when sources arrive, onError on failure.
 */
export async function streamAskQuestion(
  body: AskRequest,
  callbacks: StreamCallbacks,
  options?: { signal?: AbortSignal },
): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${API_PREFIX}/answer/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: options?.signal,
    });
  } catch {
    throw new ApiError(
      "Couldn't reach the server.",
      "Check your connection and that the API is running.",
    );
  }

  if (!response.ok) {
    const raw = await response.text();
    throw toAskApiError(response.status, parseJson(raw));
  }

  const reader = response.body?.getReader();
  if (!reader) throw new ApiError("No stream body from server.");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    // SSE events are separated by \n\n; last slice may be incomplete
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      if (!part.startsWith("data: ")) continue;
      const event = parseJson(part.slice("data: ".length));
      if (!event || typeof event !== "object") continue;
      const e = event as Record<string, unknown>;
      if (e.type === "token" && typeof e.text === "string") {
        callbacks.onToken(e.text);
      } else if (e.type === "done") {
        const found = typeof e.found === "boolean" ? e.found : false;
        const sources = Array.isArray(e.sources) ? (e.sources as AskSource[]) : [];
        callbacks.onDone(found, sources);
      } else if (e.type === "error" && typeof e.message === "string") {
        callbacks.onError(e.message);
      }
    }
  }
}

/**
 * `POST /answer` — grounded reply from retrieved passages.
 */
export async function askQuestion(
  body: AskRequest,
  options?: { signal?: AbortSignal },
): Promise<AskResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_PREFIX}/answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: options?.signal,
    });
  } catch {
    throw new ApiError(
      "Couldn't reach the server.",
      "Check your connection and that the API is running.",
    );
  }

  const raw = await response.text();
  const parsed = parseJson(raw);

  if (!response.ok) {
    throw toAskApiError(response.status, parsed);
  }
  if (!isAskResponse(parsed)) {
    throw new ApiError("The server sent an unexpected response.");
  }
  return parsed;
}

function toAskApiError(status: number, body: unknown): ApiError {
  const detail = readDetail(body);

  if (status >= 500 && detail === undefined) {
    return new ApiError(
      "Couldn't reach the document service.",
      "Make sure the FastAPI backend is running.",
      status,
    );
  }

  switch (status) {
    case 422:
      return new ApiError("The question was rejected.", detail, status);
    case 503:
      return new ApiError(
        "The answer service failed.",
        detail ?? "The model may be unavailable. Try again shortly.",
        status,
      );
    default:
      return new ApiError(`Ask failed (HTTP ${status}).`, detail, status);
  }
}

function isAskResponse(body: unknown): body is AskResponse {
  if (!body || typeof body !== "object") return false;
  const { question, answer, found, sources } = body as Record<string, unknown>;
  return (
    typeof question === "string" &&
    typeof answer === "string" &&
    typeof found === "boolean" &&
    Array.isArray(sources) &&
    sources.every(
      (source) =>
        source &&
        typeof source === "object" &&
        typeof source.heading === "string" &&
        typeof source.page_number === "number" &&
        typeof source.end_page === "number" &&
        typeof source.document_id === "string",
    )
  );
}
