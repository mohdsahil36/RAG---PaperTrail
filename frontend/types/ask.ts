/** One cited passage in `POST /answer`. */
export interface AskSource {
  heading: string;
  page_number: number;
  end_page: number;
  document_id: string;
}

/** Body of `POST /answer`. */
export interface AskRequest {
  question: string;
  k?: number;
  document_id?: string | null;
}

/** Response body of `POST /answer`. */
export interface AskResponse {
  question: string;
  answer: string;
  found: boolean;
  sources: AskSource[];
}
