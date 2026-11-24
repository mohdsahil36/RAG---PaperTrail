import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError, UploadAbortedError, uploadDocument } from "@/lib/api";
import { validatePdf } from "@/lib/files";
import type { UploadDocumentResponse } from "@/types/document";

export type UploadState =
  | { status: "idle" }
  /** `progress` is the sent fraction; 1 means the server is extracting text. */
  | { status: "uploading"; file: File; progress: number }
  | { status: "error"; file: File; title: string; detail?: string }
  | { status: "ready"; file: File; document: UploadDocumentResponse };

export function useDocumentUpload() {
  const [state, setState] = useState<UploadState>({ status: "idle" });
  const controllerRef = useRef<AbortController | null>(null);

  useEffect(() => () => controllerRef.current?.abort(), []);

  const upload = useCallback(async (file: File) => {
    controllerRef.current?.abort();

    const validationError = validatePdf(file);
    if (validationError) {
      setState({ status: "error", file, title: validationError });
      return;
    }

    const controller = new AbortController();
    controllerRef.current = controller;
    setState({ status: "uploading", file, progress: 0 });

    try {
      const document = await uploadDocument(file, {
        signal: controller.signal,
        onProgress: (progress) =>
          setState((current) =>
            current.status === "uploading" && current.file === file
              ? { ...current, progress }
              : current,
          ),
      });
      setState({ status: "ready", file, document });
    } catch (error) {
      if (error instanceof UploadAbortedError) return;
      if (error instanceof ApiError) {
        setState({ status: "error", file, title: error.message, detail: error.detail });
      } else {
        setState({ status: "error", file, title: "Something went wrong while uploading." });
      }
    } finally {
      if (controllerRef.current === controller) controllerRef.current = null;
    }
  }, []);

  const cancel = useCallback(() => {
    controllerRef.current?.abort();
    controllerRef.current = null;
    setState({ status: "idle" });
  }, []);

  return { state, upload, cancel };
}
