// useChat — first-time map
//
// Who calls this: Workspace uses the hook, then passes send / messages / isSending
// into ChatPanel. The user never calls this file directly.
//
// Where the runtime flow STARTS: the function `send` (search for "const send").
// ChatPanel calls send(question) when the user hits send.
//
// What each piece is for:
//   messages      — chat bubbles on screen (user + assistant rows)
//   isSending     — true while waiting on the API; ChatPanel disables the input
//   sendingRef    — same "busy" flag, but readable immediately (React state lags)
//   controllerRef — AbortController for the current /answer; only aborted on unmount
//   documentId    — optional filter for one uploaded doc (null = search all)
//
// What send does, in order:
//   1. Ignore empty text or a second send while busy
//   2. Add user row + pending assistant row ("Reading…")
//   3. POST /answer/stream via streamAskQuestion in lib/api.ts
//   4. Append each token live; set sources on done; set error on failure
//   5. Clear busy flags so the next question can run
import { useCallback, useEffect, useRef, useState } from "react";
import { flushSync } from "react-dom";

import { ApiError, streamAskQuestion } from "@/lib/api";
import type { ChatMessage } from "@/types/chat";

function newId(): string {
  return crypto.randomUUID();
}

export function useChat(documentId?: string | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSending, setIsSending] = useState(false);
  const controllerRef = useRef<AbortController | null>(null);
  const sendingRef = useRef(false);

  // only if the chat UI unmounts — not when the user asks another question
  useEffect(() => () => controllerRef.current?.abort(), []);

  // --- runtime flow starts here ---
  const send = useCallback(
    async (question: string) => {
      const trimmed = question.trim();
      if (!trimmed || sendingRef.current) return;

      const controller = new AbortController();
      controllerRef.current = controller;

      const userId = newId();
      const pendingId = newId();

      sendingRef.current = true;
      setIsSending(true);
      setMessages((current) => [
        ...current,
        { id: userId, role: "user", content: trimmed },
        { id: pendingId, role: "assistant", content: "", status: "pending" },
      ]);

      try {
        await streamAskQuestion(
          { question: trimmed, document_id: documentId ?? null },
          {
            onToken: (text) => {
              flushSync(() => {
                setMessages((current) =>
                  current.map((msg) =>
                    msg.id === pendingId ? { ...msg, content: msg.content + text } : msg,
                  ),
                );
              });
            },
            onDone: (_found, sources) => {
              setMessages((current) =>
                current.map((msg) =>
                  msg.id === pendingId ? { ...msg, sources, status: undefined } : msg,
                ),
              );
            },
            onError: (message) => {
              setMessages((current) =>
                current.map((msg) =>
                  msg.id === pendingId
                    ? { ...msg, content: message, status: "error" }
                    : msg,
                ),
              );
            },
          },
          { signal: controller.signal },
        );
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") return;
        const content =
          error instanceof ApiError
            ? [error.message, error.detail].filter(Boolean).join(" — ")
            : "Something went wrong while answering.";
        setMessages((current) =>
          current.map((message) =>
            message.id === pendingId
              ? { id: pendingId, role: "assistant", content, status: "error" }
              : message,
          ),
        );
      } finally {
        if (controllerRef.current === controller) controllerRef.current = null;
        sendingRef.current = false;
        setIsSending(false);
      }
    },
    [documentId],
  );

  return { messages, isSending, send };
}
