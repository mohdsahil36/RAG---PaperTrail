/** One page of extracted text, as returned by `POST /upload-document`. */
export interface ExtractedPage {
  page_number: number;
  text: string;
}

/** Response body of `POST /upload-document`. */
export interface UploadDocumentResponse {
  filename: string;
  pages: ExtractedPage[];
}
