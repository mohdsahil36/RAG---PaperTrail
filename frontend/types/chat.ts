import type { AskSource } from "@/types/ask";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  status?: "pending" | "error";
  sources?: AskSource[];
}
