# Papertrail frontend

Next.js (App Router, TypeScript, Tailwind CSS) UI for the RAG Document Assistant FastAPI backend.

## Running locally

Start the backend from the repository root:

```bash
source .venv/bin/activate
cd backend
uvicorn rag_assistant.main:app --reload --port 8000
```

Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000.

## Configuration

| Variable       | Default                 | Purpose                                       |
| -------------- | ----------------------- | --------------------------------------------- |
| `API_BASE_URL` | `http://127.0.0.1:8000` | FastAPI backend that `/api/*` is proxied to. |

The browser calls `/api/...` on the Next.js server, which rewrites to `API_BASE_URL` (see `next.config.ts`), so the backend does not need CORS. The value is read when `next dev` / `next build` starts.

## Structure

- `app/page.tsx` — page shell and header
- `components/workspace.tsx` — holds upload state and lays out both panels
- `components/document-panel.tsx`, `upload-dropzone.tsx`, `extracted-text-viewer.tsx` — upload and extracted text
- `components/chat-panel.tsx`, `chat-message.tsx` — assistant UI (pass `messages` / `onSend` to connect it)
- `hooks/use-document-upload.ts` — upload state machine
- `lib/api.ts` — typed calls to the backend and error mapping
- `types/` — response and message types

## Scripts

- `npm run dev` — development server
- `npm run lint` — ESLint
- `npx tsc --noEmit` — type-check
- `npm run build` — production build
