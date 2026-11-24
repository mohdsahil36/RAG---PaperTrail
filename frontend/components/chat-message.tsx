import { BookOpenText, CircleAlert, LoaderCircle } from "lucide-react";
import { Fragment, type ReactNode } from "react";

import type { AskSource } from "@/types/ask";
import type { ChatMessage as ChatMessageData } from "@/types/chat";

export function ChatMessage({ message }: { message: ChatMessageData }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <p className="max-w-[85%] rounded-2xl rounded-br-md bg-accent px-3.5 py-2.5 text-sm leading-6 whitespace-pre-wrap text-white wrap-anywhere">
          {message.content}
        </p>
      </div>
    );
  }

  return (
    <div className="flex gap-3">
      <div className="flex size-7 shrink-0 items-center justify-center rounded-full border border-line bg-sunken text-accent">
        <BookOpenText className="size-3.5" aria-hidden />
      </div>
      <div className="min-w-0 flex-1 pt-0.5 text-sm leading-6">
        {message.status === "pending" ? (
          <p className="flex items-center gap-2 text-ink-muted">
            <LoaderCircle className="size-4 animate-spin" aria-hidden />
            Reading the document…
          </p>
        ) : message.status === "error" ? (
          <p className="flex gap-2 text-danger">
            <CircleAlert className="mt-1 size-4 shrink-0" aria-hidden />
            <span className="wrap-anywhere">{message.content}</span>
          </p>
        ) : (
          <div className="space-y-3">
            <AnswerBody text={message.content} />
            {message.sources && message.sources.length > 0 ? (
              <SourcesList sources={message.sources} />
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}

/** Split answer into paragraphs; style [n] citation markers. */
function AnswerBody({ text }: { text: string }) {
  const paragraphs = text
    .trim()
    .split(/\n{2,}/)
    .map((block) => block.trim())
    .filter(Boolean);

  if (paragraphs.length === 0) {
    return <p className="text-ink-muted">No answer returned.</p>;
  }

  return (
    <div className="space-y-3 text-ink">
      {paragraphs.map((paragraph, index) => (
        <p key={index} className="leading-7 wrap-anywhere">
          {renderInline(paragraph)}
        </p>
      ))}
    </div>
  );
}

function renderInline(text: string): ReactNode[] {
  const parts = text.split(/(\[\d+\])/g);
  return parts.map((part, index) => {
    const match = /^\[(\d+)\]$/.exec(part);
    if (!match) {
      return (
        <Fragment key={index}>
          {part.split("\n").map((line, lineIndex, lines) => (
            <Fragment key={lineIndex}>
              {line}
              {lineIndex < lines.length - 1 ? <br /> : null}
            </Fragment>
          ))}
        </Fragment>
      );
    }
    return (
      <sup
        key={index}
        className="ml-0.5 inline-flex translate-y-[-0.1em] items-center rounded bg-accent-soft px-1 py-px text-[10px] font-semibold text-accent"
      >
        {match[1]}
      </sup>
    );
  });
}

function SourcesList({ sources }: { sources: AskSource[] }) {
  return (
    <div className="rounded-lg border border-line bg-sunken/80 px-3 py-2.5">
      <p className="text-[11px] font-medium tracking-wide text-ink-subtle uppercase">
        Sources
      </p>
      <ol className="mt-1.5 space-y-1">
        {sources.map((source, index) => {
          const pages =
            source.end_page !== source.page_number
              ? `pp. ${source.page_number}–${source.end_page}`
              : `p. ${source.page_number}`;
          return (
            <li
              key={`${source.document_id}-${source.heading}-${source.page_number}-${index}`}
              className="flex gap-2 text-xs leading-5 text-ink-muted"
            >
              <span className="w-4 shrink-0 font-medium text-accent">{index + 1}.</span>
              <span className="min-w-0 wrap-anywhere">
                <span className="text-ink">{source.heading || "Untitled section"}</span>
                <span className="text-ink-subtle"> · {pages}</span>
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
