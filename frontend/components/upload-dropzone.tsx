"use client";

import { FileUp } from "lucide-react";
import { useRef, useState, type DragEvent } from "react";

import { Button } from "@/components/button";

export function UploadDropzone({ onFile }: { onFile: (file: File) => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const dragDepth = useRef(0);
  const [isDragging, setIsDragging] = useState(false);

  function handleDragEnter(event: DragEvent) {
    event.preventDefault();
    dragDepth.current++;
    setIsDragging(true);
  }

  function handleDragLeave(event: DragEvent) {
    event.preventDefault();
    dragDepth.current = Math.max(0, dragDepth.current - 1);
    if (dragDepth.current === 0) setIsDragging(false);
  }

  function handleDrop(event: DragEvent) {
    event.preventDefault();
    dragDepth.current = 0;
    setIsDragging(false);
    const file = event.dataTransfer.files[0];
    if (file) onFile(file);
  }

  return (
    <div
      onDragEnter={handleDragEnter}
      onDragOver={(event) => event.preventDefault()}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`flex min-h-72 flex-1 flex-col items-center justify-center rounded-xl border border-dashed px-6 py-14 text-center transition-colors ${
        isDragging
          ? "border-accent bg-accent-soft"
          : "border-line-strong bg-sunken hover:border-ink-subtle/50"
      }`}
    >
      <div
        className={`flex size-12 items-center justify-center rounded-full border transition-colors ${
          isDragging
            ? "border-accent/30 bg-surface text-accent"
            : "border-line bg-surface text-ink-muted"
        }`}
      >
        <FileUp className="size-5" aria-hidden />
      </div>
      <p className="mt-4 text-[15px] font-medium text-ink">
        {isDragging ? "Drop to upload" : "Drop a PDF here"}
      </p>
      <p className="mt-1 text-sm text-ink-muted">
        Papertrail extracts the text page by page so you can review it here.
      </p>
      <Button variant="primary" className="mt-5" onClick={() => inputRef.current?.click()}>
        Browse files
      </Button>
      <p className="mt-3 text-xs text-ink-subtle">PDF files only</p>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,.pdf"
        className="sr-only"
        tabIndex={-1}
        aria-hidden
        onChange={(event) => {
          const file = event.target.files?.[0];
          event.target.value = "";
          if (file) onFile(file);
        }}
      />
    </div>
  );
}
