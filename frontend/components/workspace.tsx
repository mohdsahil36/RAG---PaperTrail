"use client";

import { useRef, useState, type PointerEvent as ReactPointerEvent } from "react";

import { ChatPanel } from "@/components/chat-panel";
import { DocumentPanel } from "@/components/document-panel";
import { useChat } from "@/hooks/use-chat";
import { useDocumentUpload } from "@/hooks/use-document-upload";

const CHAT_MIN_PX = 320;
const CHAT_MAX_PX = 720;
const CHAT_DEFAULT_PX = 416; // ~26rem

function clampChatWidth(value: number, containerWidth: number) {
  // Leave at least 280px for the document panel.
  const maxForLayout = Math.max(CHAT_MIN_PX, containerWidth - 280);
  return Math.min(CHAT_MAX_PX, maxForLayout, Math.max(CHAT_MIN_PX, value));
}

export function Workspace() {
  const { state, upload, cancel } = useDocumentUpload();
  const documentName = state.status === "ready" ? state.document.filename : null;
  const [chatWidth, setChatWidth] = useState(CHAT_DEFAULT_PX);
  const mainRef = useRef<HTMLElement>(null);
  const dragRef = useRef<{ startX: number; startWidth: number } | null>(null);

  function startResize(event: ReactPointerEvent<HTMLButtonElement>) {
    event.preventDefault();
    dragRef.current = { startX: event.clientX, startWidth: chatWidth };
    event.currentTarget.setPointerCapture(event.pointerId);
  }

  function moveResize(event: ReactPointerEvent<HTMLButtonElement>) {
    const drag = dragRef.current;
    const main = mainRef.current;
    if (!drag || !main) return;
    // Drag left → wider chat (handle sits on the left edge of chat)
    const next = drag.startWidth + (drag.startX - event.clientX);
    setChatWidth(clampChatWidth(next, main.clientWidth));
  }

  function endResize(event: ReactPointerEvent<HTMLButtonElement>) {
    if (!dragRef.current) return;
    dragRef.current = null;
    if (event.currentTarget.hasPointerCapture(event.pointerId)) {
      event.currentTarget.releasePointerCapture(event.pointerId);
    }
  }

  return (
    <main
      ref={mainRef}
      className="flex min-h-0 flex-1 flex-col gap-4 p-4 sm:p-5 lg:flex-row lg:gap-0"
    >
      <div className="flex min-h-0 min-w-0 flex-1 flex-col lg:h-full">
        <DocumentPanel state={state} onUpload={upload} onCancel={cancel} />
      </div>

      {/* Desktop: drag to change chat column width */}
      <button
        type="button"
        aria-label="Resize assistant panel"
        onPointerDown={startResize}
        onPointerMove={moveResize}
        onPointerUp={endResize}
        onPointerCancel={endResize}
        className="group relative hidden w-5 shrink-0 cursor-col-resize touch-none items-stretch justify-center self-stretch lg:flex"
      >
        <span className="absolute inset-y-8 left-1/2 w-px -translate-x-1/2 bg-line transition-colors group-hover:bg-accent/50 group-active:bg-accent" />
        <span className="absolute top-1/2 left-1/2 size-8 -translate-x-1/2 -translate-y-1/2 rounded-full border border-line bg-surface opacity-0 shadow-sm transition-opacity group-hover:opacity-100 group-active:opacity-100" />
      </button>

      <div
        className="flex min-h-0 w-full shrink-0 flex-col lg:h-full lg:w-(--chat-width)"
        style={{ ["--chat-width" as string]: `${chatWidth}px` }}
      >
        {/* key remounts chat when the uploaded file changes → fresh messages */}
        <ConnectedChat key={documentName ?? "none"} documentName={documentName} />
      </div>
    </main>
  );
}

function ConnectedChat({ documentName }: { documentName: string | null }) {
  // filename == document_id in Chroma; null = search all docs
  const { messages, isSending, send } = useChat(documentName);

  return (
    <ChatPanel
      documentName={documentName}
      messages={messages}
      onSend={send}
      isSending={isSending}
    />
  );
}
