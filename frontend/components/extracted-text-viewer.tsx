"use client";

import { Check, ChevronLeft, ChevronRight, Copy, TriangleAlert } from "lucide-react";
import { type RefObject, useEffect, useRef, useState } from "react";

import { Button } from "@/components/button";
import type { ExtractedPage } from "@/types/document";

type View = "original" | "text";

export function ExtractedTextViewer({ pages, file }: { pages: ExtractedPage[]; file: File }) {
  const [index, setIndex] = useState(0);
  const [view, setView] = useState<View>("original");
  const [copied, setCopied] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const page = pages[index];
  const text = page?.text.trim() ?? "";
  const wordCount = text ? text.split(/\s+/).length : 0;
  const hasAnyText = pages.some((p) => p.text.trim().length > 0);

  function goTo(nextIndex: number) {
    setIndex(nextIndex);
    setCopied(false);
    scrollRef.current?.scrollTo({ top: 0 });
  }

  async function copyPage() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }

  if (!page) {
    return (
      <p className="px-6 py-10 text-center text-sm text-ink-muted">
        The server returned no pages for this document.
      </p>
    );
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line px-4 py-2.5 sm:px-5">
        <nav aria-label="Pages" className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            aria-label="Previous page"
            disabled={index === 0}
            onClick={() => goTo(index - 1)}
          >
            <ChevronLeft />
          </Button>
          <div className="flex items-center gap-2 text-sm text-ink-muted">
            <span aria-hidden>Page</span>
            <select
              aria-label={`Page, ${pages.length} total`}
              value={index}
              onChange={(event) => goTo(Number(event.target.value))}
              className="h-8 rounded-md border border-line-strong bg-surface pl-2 pr-7 text-sm font-medium text-ink tabular-nums hover:border-ink-subtle/50"
            >
              {pages.map((p, i) => (
                <option key={p.page_number} value={i}>
                  {p.page_number}
                </option>
              ))}
            </select>
            <span className="tabular-nums" aria-hidden>
              of {pages.length}
            </span>
          </div>
          <Button
            variant="ghost"
            size="icon"
            aria-label="Next page"
            disabled={index === pages.length - 1}
            onClick={() => goTo(index + 1)}
          >
            <ChevronRight />
          </Button>
        </nav>

        <div className="flex items-center gap-3">
          <ViewToggle view={view} onChange={setView} />
          {view === "text" && (
            <>
              <span className="text-xs text-ink-subtle tabular-nums">
                {wordCount.toLocaleString()} {wordCount === 1 ? "word" : "words"}
              </span>
              <Button size="sm" onClick={copyPage} disabled={!text}>
                {copied ? <Check className="text-success" /> : <Copy />}
                {copied ? "Copied" : "Copy page"}
              </Button>
            </>
          )}
        </div>
      </div>

      {view === "original" ? (
        <PdfPreview file={file} pageNumber={page.page_number} />
      ) : (
        <ExtractedText page={page} text={text} hasAnyText={hasAnyText} scrollRef={scrollRef} />
      )}
    </div>
  );
}

function ViewToggle({ view, onChange }: { view: View; onChange: (view: View) => void }) {
  const options: { value: View; label: string }[] = [
    { value: "original", label: "Original" },
    { value: "text", label: "Extracted text" },
  ];

  return (
    <div role="group" aria-label="Preview mode" className="flex rounded-md border border-line-strong bg-sunken p-0.5">
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          aria-pressed={view === option.value}
          onClick={() => onChange(option.value)}
          className={`h-7 rounded px-2.5 text-[13px] font-medium transition-colors ${
            view === option.value ? "bg-surface text-ink shadow-sm" : "text-ink-muted hover:text-ink"
          }`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

/** Shows the uploaded PDF in the browser's built-in viewer, so headings and fonts look exactly like the real file. */
function PdfPreview({ file, pageNumber }: { file: File; pageNumber: number }) {
  const frameRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    const url = URL.createObjectURL(file);
    // `#page=` tells the browser's PDF viewer which page to open
    frameRef.current?.setAttribute("src", `${url}#page=${pageNumber}`);
    return () => URL.revokeObjectURL(url);
  }, [file, pageNumber]);

  return (
    <iframe
      ref={frameRef}
      title={`${file.name}, page ${pageNumber}`}
      className="min-h-0 w-full flex-1 border-0 bg-sunken"
    />
  );
}

function ExtractedText({
  page,
  text,
  hasAnyText,
  scrollRef,
}: {
  page: ExtractedPage;
  text: string;
  hasAnyText: boolean;
  scrollRef: RefObject<HTMLDivElement | null>;
}) {
  return (
    <>
      {!hasAnyText && (
        <div className="mx-4 mt-4 flex gap-2.5 rounded-lg border border-warning-line bg-warning-soft px-3.5 py-3 text-sm text-warning sm:mx-5">
          <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
          <p>
            No text was found in this document. It may be a scanned or image-only PDF, which
            needs OCR to extract.
          </p>
        </div>
      )}

      <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto bg-sunken">
        <article
          aria-label={`Page ${page.page_number}`}
          className="mx-auto my-5 max-w-[68ch] rounded-lg border border-line bg-surface px-6 py-7 shadow-panel sm:my-6 sm:px-10 sm:py-9"
        >
          <p className="mb-5 font-mono text-[11px] font-medium tracking-wider text-ink-subtle uppercase">
            Page {page.page_number}
          </p>
          {text ? (
            <p className="font-serif text-[15.5px] leading-7 whitespace-pre-wrap text-ink wrap-anywhere">
              {text}
            </p>
          ) : (
            <p className="text-sm text-ink-muted italic">This page has no extractable text.</p>
          )}
        </article>
      </div>
    </>
  );
}
