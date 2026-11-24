"use client";

import { ArrowUp, BookOpenText, GripHorizontal, Info } from "lucide-react";
import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
  type PointerEvent as ReactPointerEvent,
} from "react";

import { Button } from "@/components/button";
import { ChatMessage } from "@/components/chat-message";
import type { ChatMessage as ChatMessageData } from "@/types/chat";

const SUGGESTED_QUESTIONS = [
  "Summarize this document",
  "What are the key points?",
  "List any dates or deadlines",
  "Who is this document intended for?",
];

const TEXTAREA_MIN_PX = 40;
const TEXTAREA_MAX_PX = 360;

function clampInputHeight(value: number) {
  return Math.min(TEXTAREA_MAX_PX, Math.max(TEXTAREA_MIN_PX, value));
}

interface ChatPanelProps {
  /** Name of the uploaded document, or null before one is loaded. */
  documentName: string | null;
  messages?: ChatMessageData[];
  /** Omit until a question-answering endpoint exists; the panel then shows as not connected. */
  onSend?: (question: string) => void;
  isSending?: boolean;
}

export function ChatPanel({
  documentName,
  messages = [],
  onSend,
  isSending = false,
}: ChatPanelProps) {
  const [draft, setDraft] = useState("");
  const [inputHeight, setInputHeight] = useState(TEXTAREA_MIN_PX);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const listEndRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<{ startY: number; startHeight: number } | null>(null);

  const isConnected = Boolean(onSend);
  const hasDocument = documentName !== null;
  const canType = hasDocument && !isSending;
  const canSend = isConnected && canType && draft.trim().length > 0;

  useEffect(() => {
    listEndRef.current?.scrollIntoView({ block: "end" });
  }, [messages.length]);

  // Grow with typed text; never shrink below the user’s drag height.
  function growToContent() {
    const el = textareaRef.current;
    if (!el || dragRef.current) return;
    const previous = el.style.height;
    el.style.height = "0px";
    const needed = clampInputHeight(el.scrollHeight);
    el.style.height = previous;
    setInputHeight((current) => Math.max(current, needed));
  }

  function fillDraft(text: string) {
    setDraft(text);
    requestAnimationFrame(() => {
      growToContent();
      textareaRef.current?.focus();
    });
  }

  function submit(event?: FormEvent) {
    event?.preventDefault();
    if (!canSend || !onSend) return;
    onSend(draft.trim());
    setDraft("");
    setInputHeight(TEXTAREA_MIN_PX);
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      submit();
    }
  }

  function startResize(event: ReactPointerEvent<HTMLButtonElement>) {
    event.preventDefault();
    dragRef.current = { startY: event.clientY, startHeight: inputHeight };
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function moveResize(event: ReactPointerEvent<HTMLButtonElement>) {
    const drag = dragRef.current;
    if (!drag) return;
    // Drag up → taller box
    setInputHeight(clampInputHeight(drag.startHeight + (drag.startY - event.clientY)));
  }

  function endResize(event: ReactPointerEvent<HTMLButtonElement>) {
    if (!dragRef.current) return;
    dragRef.current = null;
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
  }

  const status = !isConnected
    ? { label: "Not connected", dot: "bg-ink-subtle/60" }
    : hasDocument
      ? { label: "Ready", dot: "bg-success" }
      : { label: "Waiting for a document", dot: "bg-line-strong" };

  return (
    <section
      aria-labelledby="assistant-heading"
      className="flex h-144 flex-col overflow-hidden rounded-xl border border-line bg-surface shadow-panel lg:h-full lg:min-h-0"
    >
      <header className="flex min-h-14 items-center gap-3 border-b border-line px-4 py-2.5 sm:px-5">
        <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-accent text-white">
          <BookOpenText className="size-4" aria-hidden />
        </div>
        <div className="min-w-0">
          <h2 id="assistant-heading" className="text-sm font-semibold text-ink">
            Document assistant
          </h2>
          <p className="mt-0.5 flex items-center gap-1.5 text-xs text-ink-muted">
            <span className={`size-1.5 rounded-full ${status.dot}`} aria-hidden />
            {status.label}
            {hasDocument && (
              <span className="truncate text-ink-subtle" title={documentName}>
                · {documentName}
              </span>
            )}
          </p>
        </div>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-5 sm:px-5">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <h3 className="text-[15px] font-medium text-ink">Ask about your document</h3>
            <p className="mt-1.5 max-w-xs text-sm text-ink-muted">
              {!hasDocument
                ? "Upload a PDF to get started. Questions are scoped to the document you upload."
                : isConnected
                  ? "Ask a question in plain language about this document."
                  : "You can draft a question now. Answers will appear here once question answering is connected."}
            </p>
            <ul className="mt-5 flex max-w-sm flex-wrap justify-center gap-2" aria-label="Suggested questions">
              {SUGGESTED_QUESTIONS.map((question) => (
                <li key={question}>
                  <button
                    type="button"
                    disabled={!canType}
                    onClick={() => fillDraft(question)}
                    className="rounded-full border border-line-strong bg-surface px-3 py-1.5 text-[13px] text-ink-muted transition-colors hover:border-accent/40 hover:bg-accent-soft hover:text-accent disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:border-line-strong disabled:hover:bg-surface disabled:hover:text-ink-muted"
                  >
                    {question}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <div className="flex flex-col gap-5" aria-live="polite">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            <div ref={listEndRef} />
          </div>
        )}
      </div>

      <div className="border-t border-line bg-sunken">
        <button
          type="button"
          aria-label="Resize chat input"
          onPointerDown={startResize}
          onPointerMove={moveResize}
          onPointerUp={endResize}
          onPointerCancel={endResize}
          className="flex h-5 w-full cursor-row-resize touch-none items-center justify-center text-ink-subtle transition-colors hover:bg-line/50 hover:text-ink-muted"
        >
          <GripHorizontal className="size-3.5" aria-hidden />
        </button>

        <div className="px-3 pb-3 sm:px-4 sm:pb-4">
          {!isConnected && (
            <p className="mb-3 flex gap-2 rounded-lg border border-line bg-surface px-3 py-2.5 text-xs leading-5 text-ink-muted">
              <Info className="mt-0.5 size-3.5 shrink-0 text-accent" aria-hidden />
              Question answering isn&apos;t connected yet. Papertrail currently extracts document
              text only.
            </p>
          )}
          <form
            onSubmit={submit}
            className="flex items-end gap-2 rounded-xl border border-line-strong bg-surface p-2 pl-3.5 shadow-sm transition-colors focus-within:border-accent/60 focus-within:ring-3 focus-within:ring-accent/15 has-[textarea:disabled]:bg-canvas"
          >
            <label htmlFor="chat-input" className="sr-only">
              Ask a question about the document
            </label>
            <textarea
              id="chat-input"
              ref={textareaRef}
              rows={1}
              value={draft}
              disabled={!canType}
              style={{ height: inputHeight }}
              onChange={(event) => {
                setDraft(event.target.value);
                requestAnimationFrame(growToContent);
              }}
              onKeyDown={handleKeyDown}
              placeholder={hasDocument ? "Ask a question…" : "Upload a document to start"}
              className="min-h-10 flex-1 resize-none overflow-y-auto bg-transparent py-2 text-sm leading-6 text-ink placeholder:text-ink-subtle focus:outline-none focus-visible:outline-none disabled:cursor-not-allowed"
            />
            <Button
              type="submit"
              variant="primary"
              size="icon"
              aria-label="Send question"
              disabled={!canSend}
              className="mb-0.5 shrink-0"
            >
              <ArrowUp />
            </Button>
          </form>
          <p className="mt-2 hidden px-1 text-[11px] text-ink-subtle sm:block">
            Enter to send · Shift + Enter for a new line · Drag the handle to resize
          </p>
        </div>
      </div>
    </section>
  );
}
