"use client";

import { CircleAlert, CircleCheck, FileText, LoaderCircle, RefreshCw, X } from "lucide-react";
import { useRef } from "react";

import { Button } from "@/components/button";
import { ExtractedTextViewer } from "@/components/extracted-text-viewer";
import { UploadDropzone } from "@/components/upload-dropzone";
import type { UploadState } from "@/hooks/use-document-upload";
import { formatBytes, validatePdf } from "@/lib/files";

interface DocumentPanelProps {
  state: UploadState;
  onUpload: (file: File) => void;
  onCancel: () => void;
}

export function DocumentPanel({ state, onUpload, onCancel }: DocumentPanelProps) {
  const replaceInputRef = useRef<HTMLInputElement>(null);

  return (
    <section
      aria-labelledby="document-heading"
      className="flex min-h-128 flex-col overflow-hidden rounded-xl border border-line bg-surface shadow-panel lg:h-full lg:min-h-0"
    >
      <header className="flex min-h-14 items-center justify-between gap-3 border-b border-line px-4 py-2.5 sm:px-5">
        <div className="min-w-0">
          <h2 id="document-heading" className="text-sm font-semibold text-ink">
            Document
          </h2>
          {state.status === "ready" ? (
            <p className="mt-0.5 flex items-center gap-1.5 text-xs text-ink-muted">
              <CircleCheck className="size-3.5 shrink-0 text-success" aria-hidden />
              <span className="truncate">
                {state.document.pages.length}{" "}
                {state.document.pages.length === 1 ? "page" : "pages"} extracted
              </span>
            </p>
          ) : (
            <p className="mt-0.5 text-xs text-ink-muted">Upload a PDF to review its text.</p>
          )}
        </div>
        {state.status === "ready" && (
          <>
            <Button size="sm" onClick={() => replaceInputRef.current?.click()}>
              <RefreshCw />
              Replace
            </Button>
            <input
              ref={replaceInputRef}
              type="file"
              accept="application/pdf,.pdf"
              className="sr-only"
              tabIndex={-1}
              aria-hidden
              onChange={(event) => {
                const file = event.target.files?.[0];
                event.target.value = "";
                if (file) onUpload(file);
              }}
            />
          </>
        )}
      </header>

      <p role="status" className="sr-only">
        {statusMessage(state)}
      </p>

      {state.status === "ready" ? (
        <>
          <FileSummary file={state.file} name={state.document.filename} />
          <ExtractedTextViewer
            key={`${state.file.name}-${state.file.size}-${state.file.lastModified}`}
            pages={state.document.pages}
            file={state.file}
          />
        </>
      ) : (
        <div className="flex flex-1 flex-col gap-4 overflow-y-auto p-4 sm:p-5">
          {state.status === "uploading" && <UploadProgress state={state} onCancel={onCancel} />}
          {state.status === "error" && (
            <UploadError
              state={state}
              onRetry={validatePdf(state.file) ? undefined : () => onUpload(state.file)}
              onDismiss={onCancel}
            />
          )}
          {state.status !== "uploading" && <UploadDropzone onFile={onUpload} />}
        </div>
      )}
    </section>
  );
}

function FileSummary({ file, name }: { file: File; name: string }) {
  return (
    <div className="flex items-center gap-3 border-b border-line bg-sunken px-4 py-3 sm:px-5">
      <FileIcon />
      <div className="min-w-0">
        <p className="truncate text-sm font-medium text-ink" title={name}>
          {name}
        </p>
        <p className="text-xs text-ink-subtle">{formatBytes(file.size)}</p>
      </div>
    </div>
  );
}

function UploadProgress({
  state,
  onCancel,
}: {
  state: Extract<UploadState, { status: "uploading" }>;
  onCancel: () => void;
}) {
  const extracting = state.progress >= 1;
  const percent = Math.round(state.progress * 100);

  return (
    <div className="rounded-xl border border-line bg-surface p-4">
      <div className="flex items-center gap-3">
        <FileIcon />
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-ink" title={state.file.name}>
            {state.file.name}
          </p>
          <p className="flex items-center gap-1.5 text-xs text-ink-muted">
            <LoaderCircle className="size-3.5 animate-spin" aria-hidden />
            {extracting
              ? "Extracting text…"
              : `Uploading · ${formatBytes(state.file.size)} · ${percent}%`}
          </p>
        </div>
        <Button variant="ghost" size="icon" aria-label="Cancel upload" onClick={onCancel}>
          <X />
        </Button>
      </div>
      <div
        role="progressbar"
        aria-label="Upload progress"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={extracting ? undefined : percent}
        className="mt-4 h-1.5 overflow-hidden rounded-full bg-canvas"
      >
        <div
          className={`h-full rounded-full bg-accent transition-[width] duration-300 ${
            extracting ? "animate-pulse" : ""
          }`}
          style={{ width: `${extracting ? 100 : Math.max(percent, 2)}%` }}
        />
      </div>
    </div>
  );
}

function UploadError({
  state,
  onRetry,
  onDismiss,
}: {
  state: Extract<UploadState, { status: "error" }>;
  onRetry?: () => void;
  onDismiss: () => void;
}) {
  return (
    <div role="alert" className="rounded-xl border border-danger-line bg-danger-soft p-4">
      <div className="flex gap-3">
        <CircleAlert className="mt-0.5 size-5 shrink-0 text-danger" aria-hidden />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-danger">{state.title}</p>
          {state.detail && (
            <p className="mt-1 text-sm text-ink-muted wrap-anywhere">{state.detail}</p>
          )}
          <p className="mt-2 truncate text-xs text-ink-subtle" title={state.file.name}>
            {state.file.name} · {formatBytes(state.file.size)}
          </p>
          {onRetry && (
            <Button size="sm" className="mt-3" onClick={onRetry}>
              <RefreshCw />
              Try again
            </Button>
          )}
        </div>
        <Button variant="ghost" size="icon" aria-label="Dismiss error" onClick={onDismiss}>
          <X />
        </Button>
      </div>
    </div>
  );
}

function FileIcon() {
  return (
    <div className="flex size-9 shrink-0 items-center justify-center rounded-lg border border-line bg-surface text-accent">
      <FileText className="size-4.5" aria-hidden />
    </div>
  );
}

function statusMessage(state: UploadState): string {
  switch (state.status) {
    case "uploading":
      return state.progress >= 1 ? "Extracting text" : "Uploading document";
    case "ready":
      return `${state.document.filename} uploaded. ${state.document.pages.length} pages extracted.`;
    default:
      return "";
  }
}
