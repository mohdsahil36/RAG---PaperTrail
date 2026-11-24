# Design Notes: RAG Document Assistant

Revision notes on **why** the application works the way it does, part by part.
Use them to revise, and to answer "why did you do it this way?" in code review.

**Last updated:** 2026-11-23 (Part H: streaming path). These notes are updated whenever the code or its tests change, or when a new "why" question comes up. If the code and these notes disagree, the code is the truth: fix the notes.

## Parts

| Part | Status | Code |
|---|---|---|
| [A. Upload API](#part-a-upload-api) | Built | `backend/src/rag_assistant/routes/`, `controller/`, `services/` |
| [B. Document ingestion and chunking](#part-b-document-ingestion-and-chunking) | Built, called from the upload API | `backend/src/rag_assistant/ingestion/` |
| [C. Embeddings](#part-c-embeddings) | Built, called from the upload API | `backend/src/rag_assistant/ingestion/embeddings.py` |
| D. Vector database | Built and tested (`tests/test_vector_store.py`); notes not written yet, see [pipeline-walkthrough.md](pipeline-walkthrough.md) stage 8 | `backend/src/rag_assistant/storage/vector_store.py` |
| [E. Retrieval](#part-e-retrieval) | Built: hybrid + gated rewrite + cross-encoder rerank on `/retrieve` | `search_documents_service.py`, `retrieval/query_rewrite.py`, `bm25.py`, `rrf.py`, `rerank.py` |
| [F. Answer generation (RAG)](#part-f-answer-generation-rag) | Built: `POST /answer` with Gemini, structured output and citation checks; offline ask-service tests | `generation/`, `services/ask_service.py`, `schemas/ask_schema.py`, `controller/`, `routes/` |
| [G. Frontend](#part-g-frontend) | Built: upload, preview, chat → `/answer` with sources | `frontend/` |
| [H. Streaming answer path](#part-h-streaming-answer-path) | Built: `POST /answer/stream` SSE twin; plain-text tokens; `_citations_from_answer`; frontend consumes stream | `generation/prompt_builder.py`, `generation/llm_client.py`, `services/ask_service.py`, `routes/`, `frontend/` |

New parts get their own `# Part X` heading with a short cheat sheet, as in Part B.

---

# Part A: Upload API

**Flow:** `POST /upload-document` → route → controller → service → `load_file_from_path` → `build_sections` → `split_sections_into_chunks` → response `{"filename", "pages", "chunks"}`.

| Decision | Why |
|---|---|
| Route, controller, and service in separate files | Route = HTTP shape; controller = request handling and errors; service = business logic. Each can change or be tested on its own |
| One `api_router` collects all route modules | `main.py` only includes one router; new routes are registered in `routes/router.py` |
| `UploadFile` with `File(...)` | Streams the file instead of loading it all into memory; `...` makes the file required |
| Save the upload to a temporary file | PyMuPDF opens files by path, and the upload is only a stream |
| `delete=False`, removed in `finally` | The file must still exist after the `with` block closes it, while the loader reads it; `finally` removes it even when an error happens |
| Three PDF checks: extension, `%PDF-` header, `document.is_pdf` | The extension can be faked; the header proves the content starts like a PDF; `is_pdf` catches files PyMuPDF can open as another format |
| `HTTPException` 400 for a wrong format, 500 for anything else | The client gets a clear error for its own mistake; unexpected errors are logged with `logger.exception` and hidden behind a generic message |
| Return `chunks` next to `pages` | The frontend reads only `filename` and `pages` (`frontend/lib/api.ts`), so the extra field does not break it; chunks are visible in Swagger and ready for embeddings |
| Service uses the default chunk settings (1000 / 200) | Test values like 100 / 20 give only one or two sentences per chunk on real documents |

---

# Part B: Document ingestion and chunking

Code: `backend/src/rag_assistant/ingestion/pdf_loader.py`, `chunking.py`. Tests: `backend/tests/test_chunking.py`, `test_ingestion_pipeline.py`, `test_pdf_loader.py`, `test_loader.py`.

**The one rule to remember:**

> Sections keep topics together. Chunks keep sizes small. Metadata keeps the source.

## Cheat sheet

| Question | Short answer | Section |
|---|---|---|
| What is the pipeline order? | Pages → spans → sections → chunks | [1](#1-the-pipeline) |
| Page or span: which one to use? | Page for *where* (page number), span for *what* and *how it looks* (text, font size) | [2](#2-pages-vs-spans) |
| How is a heading detected? | Font size of 13 or more | [3](#3-heading-detection) |
| Why chunk sections, not spans? | Spans are fragments of lines; sections are whole topics | [4](#4-sections) |
| Is the heading inside the chunk text? | No. Text is body only; the heading is metadata | [4](#4-sections) |
| What kind of chunking is this? | Structure-aware (sections) + recursive splitting (LangChain) | [5](#5-chunking-strategy) |
| Is it fixed-size chunking? | No. Size is a maximum and cuts happen at natural boundaries | [5](#5-chunking-strategy) |
| What is overlap for? | So text near a cut appears in both chunks and keeps its context | [6](#6-chunk-size-and-overlap) |
| Why must overlap be smaller than chunk size? | Otherwise the splitter can never move forward | [6](#6-chunk-size-and-overlap) |
| What happens to heading-only sections? | Skipped at chunking: no empty chunks | [7](#7-empty-and-heading-only-sections) |
| Why `{**section, "text": text}`? | Each chunk is a new dict with the section's metadata; the section is not changed | [8](#8-building-chunk-dictionaries) |
| What does LangChain do vs our code? | LangChain cuts text; our code validates, skips empty sections, attaches metadata | [9](#9-what-langchain-does-vs-our-code) |
| Unit test or integration test? | Unit: one function with hand-made input. Integration: real PDF through the whole flow | [10](#10-testing) |

---

## 1. The pipeline

```
PDF ──load_data_from_pdf──▶ pages (with spans) ──build_sections──▶ sections ──split_sections_into_chunks──▶ chunks
```

| Stage | Breaks the document by | Why |
|---|---|---|
| Pages | Physical page | Page numbers; the frontend text view |
| Spans | Line and font change (PyMuPDF) | Font size tells headings from body text |
| Sections | Meaning: heading to heading | Keep one topic together |
| Chunks | Size | Small enough to embed and to match a question precisely |

**Order matters:** pages and spans come from the PDF; sections and chunks are built by our code from them. It is never pages → sections → spans.

### Data shapes

```python
# Page (load_data_from_pdf)
{"page_number": 3, "text": "Leave Policy\nEmployees get...", "spans": [...]}

# Span (extract_pdf_spans): one piece of a line in one font
{"text": "Leave Policy", "size": 16.0, "page_number": 3, "block_number": 0, "font": "Helvetica-Bold", "flags": 16}

# Section and chunk (DocumentSection): same shape
{"heading": "Leave Policy", "text": "Employees get 20 days...", "page_number": 3, "end_page": 4}
```

### Worked example

```
Page 1:  Leave Policy                                   (16pt → heading)
         Employees get 20 days of paid leave per year.  (11pt → body)
Page 2:  Unused leave can be carried forward.           (11pt → body, no new heading)
```

→ one section: heading "Leave Policy", text from both pages, `page_number` 1, `end_page` 2.
Page 2 has no heading, so its text **continues the current section**.

---

## 2. Pages vs spans

| Need | Use | Why |
|---|---|---|
| Page number | `page["page_number"]` | The page is the container; one source of truth |
| Text of a piece | `span["text"]` | Only spans hold individual pieces of text |
| Heading or body | `span["size"]` via `is_heading` | Font size belongs to each piece |
| Bold or italic | `span["flags"]` | Collected, not used yet |
| Which paragraph | `span["block_number"]` | PyMuPDF block on the page (starts at 0 on every page). Lets `build_sections` keep paragraph breaks |

**Why record blocks and not lines?** In a PDF, a "line" is only where text wrapped on the page, often mid-sentence. Keeping line breaks would make the splitter cut mid-sentence (it prefers `"\n"` over `". "`). Blocks are roughly paragraphs: real breaks worth keeping as `"\n\n"`. Wrapped lines inside a block stay joined with a space.

**Why do spans also have `page_number`?** A convenience copy for when spans are flattened into one list (`get_spans_from_pages_directory`) and the page is no longer around.

**Rule:** looping page → span (nested, as in `build_sections`)? Page number from the page, everything else from the span.

---

## 3. Heading detection

- `is_heading(span)` returns `True` when `span["size"] >= 13.0`.
- **Why 13:** font-size analysis of the real employee handbook showed body text at 12 and headings at 14 and above.
- **Limitation:** large body text (a pull-quote, a big note) is wrongly treated as a heading and splits a section.
- **Possible improvements:** also check bold (`flags`), short length, no ending full stop, or exact heading sizes found in the analysis.

---

## 4. Sections

### What `build_sections` guarantees

| Behaviour | Why |
|---|---|
| A heading starts a new section with empty text | The heading is metadata, not body content (fixed bug: heading was copied into text) |
| Same block (paragraph) → joined with `" "`; new block or new page → joined with `"\n\n"` | Wrapped lines stay one paragraph; real paragraph breaks are kept so the splitter cuts at paragraphs first |
| First body text after a heading is set, not appended | No leading space |
| Text before the first heading gets `heading: None` | Intro text is not lost |
| `page_number` set once, when the section is created | It is the start page |
| `end_page` updated every time body text is added | Records the page range for citations |
| Empty and whitespace-only spans are skipped | No blank content or stray spaces |

### Why chunk sections and not spans?

Spans are pieces of lines. One sentence is often 3–4 spans (`"RAG retrieves relevant"`, `"information from"`, `"documents."`). Chunking spans would give cut-off fragments. Sections are whole topics in reading order: the right input for a splitter.

### Is the heading in the chunk text?

No. `text` is body only; `heading` is separate metadata. Keep `text` clean for display and citations.
**At embedding time** (next step), embed `heading + "\n" + text` so a chunk like "They must apply 2 weeks in advance." still matches a question about leave. This is called a *contextual chunk header*.

### Do chunks need to make sense on their own?

**Yes.** Each chunk is retrieved and sent to the LLM on its own. That is why we cut at sentence boundaries, add overlap, and copy heading and pages onto every chunk.

### Known limitations

- A new page always starts a new paragraph (`"\n\n"`), even when a sentence continues across the page break.
- A chunk's pages are the **section's** range. A chunk only on page 4 of a page 3–5 section still says 3–5.
- A heading-only parent heading (e.g. "Chapter 3") is dropped. Future fix: a *heading path* such as "Chapter 3 > Leave Policy".

---

## 5. Chunking strategy

**Two stages:**

| Stage | Function | Type | Divides by |
|---|---|---|---|
| 1 | `build_sections` | Structure-aware chunking | Meaning (headings) |
| 2 | `split_sections_into_chunks` | Recursive character splitting (LangChain) | Size, at natural boundaries |

Together this is sometimes called *hierarchical chunking*: a solid default for structured documents.

### Why stage 2 is not fixed-size chunking

Both use `chunk_size` and `chunk_overlap`. The difference is **where they cut**.

| | Fixed-size | Recursive (ours) |
|---|---|---|
| `chunk_size=100` | Exactly 100 characters per chunk | **At most** 100 characters |
| Cut point | Character 100, 180, 260… wherever it lands | Last paragraph, line, sentence, or word boundary before the limit |
| Result | Mid-word cuts: `"...paid leave per year. Leav"` | Clean ends: `"...paid leave per year."` |
| Chunk sizes | All equal | Vary (our test: 99, 99, 81, 83, 83) |

### Splitter settings

```python
RecursiveCharacterTextSplitter(
    chunk_size=max_chunk_size,                 # maximum, default 1000
    chunk_overlap=chunk_overlap,               # default 200
    separators=["\n\n", "\n", ". ", " ", ""],  # paragraph, line, sentence, word, character
    keep_separator="end",
)
```

| Setting | Why |
|---|---|
| `separators` with `". "` | The default list has no sentence level and would jump from lines to words |
| `keep_separator="end"` | The `.` stays with its sentence. With the default, chunks start with a stray `". "` |
| Order of separators | Try the biggest natural break first; go smaller only for pieces still too long |

---

## 6. Chunk size and overlap

### What overlap is

The end of one chunk is **repeated** at the start of the next:

```
Chunk 1: "This is sentence 0. ... This is sentence 4."
Chunk 2: "This is sentence 4. This is sentence 5. ..."
          └── overlap: in both chunks ──┘
```

### Why

A cut can fall in the middle of an idea. Without overlap, chunk 2 may start with "This applies to all annual leave." and nobody knows what "this" is. With overlap, a fact near the cut appears whole in at least one chunk.

### Overlap vs clean cuts: two different guarantees

| Guarantee | Done by |
|---|---|
| Cuts happen at sentence boundaries | `separators` and `keep_separator` |
| Context carries across the cut | `chunk_overlap` |

The splitter does not "check" if a chunk makes sense. It always repeats the end; the test checks that it happened.

### Things to know

- **Overlap uses whole pieces only.** If a sentence is longer than `chunk_overlap`, that boundary gets no overlap. (In our test, sentences 10+ are 21 characters with the space, overlap is 20 → no overlap there.)
- **Cost:** overlapping text is stored, embedded, and sent to the LLM twice. Keep it around 10–20% of chunk size.

### Validation (raises `ValueError`)

| Rule | Why |
|---|---|
| `max_chunk_size > 0` | A chunk must hold something |
| `chunk_overlap >= 0` | Negative overlap is meaningless |
| `chunk_overlap < max_chunk_size` | Each new chunk starts `size − overlap` after the previous one. At 0 the splitter stays in place forever; below 0 it goes backwards |

The check runs **once**, at the start of the function, before any work.

---

## 7. Empty and heading-only sections

- **What:** a section with a heading but no text, e.g. "Chapter 3" directly followed by "Leave Policy".
- **What we do:** skip it in `split_sections_into_chunks` with `if not section["text"].strip(): continue`.
- **Why skip in chunking, not in `build_sections`:** `build_sections` cannot know a section will stay empty. It creates the section when it sees the heading, before body text arrives (possibly on the next page).
- **Why `.strip()`:** `"   "` is not `""` but is still empty.
- **Why `continue`, not `break`:** `break` would stop the loop and silently drop every section after the first empty one.
- **Is the check needed?** LangChain's `split_text("")` and `split_text("   ")` already return `[]`. The check makes the intent explicit and does not depend on library behaviour. The **test** is what really protects the behaviour.

---

## 8. Building chunk dictionaries

```python
chunks.append({**section, "text": text})
```

- `**section` copies all keys of the section; `"text": text` comes after and replaces the text with this chunk's piece.
- **Order matters:** `{"text": text, **section}` would overwrite the piece with the full section text.

| Alternative | Problem |
|---|---|
| `chunks.append(section)` | Every chunk has the full section text; nothing is split |
| `section["text"] = text` then `append(section)` | `append` stores a reference: all chunks are the **same dict** holding the last piece, and the original section is changed |

---

## 9. What LangChain does vs our code

We use only the small `langchain-text-splitters` package, not full LangChain.

| Part | Done by |
|---|---|
| Validate settings, raise `ValueError` | Our code |
| Skip empty and whitespace-only sections | Our code |
| Cut text at paragraph / line / sentence / word, keep size limit, add overlap | LangChain `RecursiveCharacterTextSplitter` |
| Attach heading and pages to every chunk | Our code |

**Do we need to learn full LangChain now?** No. Concepts first (embeddings, vector stores, retrieval). LangChain wraps those steps; learn it later.

---

## 10. Testing

### Unit tests vs integration test

| | Unit tests (`test_chunking.py`) | Integration test (`test_ingestion_pipeline.py`) |
|---|---|---|
| Input | Hand-made dicts | A real PDF created with PyMuPDF |
| Checks | One function at a time | `load_data_from_pdf` → `build_sections` → `split_sections_into_chunks` |
| Catches | Logic bugs inside a function | Shape mismatches between stages, real font sizes, real PyMuPDF text |

### What each splitter test protects

| Test | Protects against |
|---|---|
| Empty input and empty section | Crashes or empty chunks when there is nothing to chunk |
| Shorter / equal to chunk size | Text that fits being split or changed; the "at most" boundary |
| Longer than chunk size | Chunks over the size limit |
| Overlap | Overlap silently disappearing (setting changed, splitter swapped) |
| Metadata preserved | Chunks losing heading or pages, or gaining/losing keys |
| Multiple sections independent | Text or pages leaking between sections; wrong order |
| Heading-only section | Empty chunks; `break` instead of `continue` |
| Whitespace-only section | Whitespace producing a chunk |
| Invalid settings | Bad settings not being rejected |

### What the integration test protects

A 2-page PDF: page 1 has "Leave Policy" at 16pt and body text at 11pt; page 2 has body text only.

| Assert | Protects against |
|---|---|
| Every chunk's heading is "Leave Policy" | Real PyMuPDF font sizes not being recognised by `is_heading` |
| `page_number` 1, `end_page` 2 | Page numbers lost between loader and sections; page break splitting the section |
| Page 1 and page 2 text both in the chunks | Text lost across the page break |
| "Leave Policy" not in the chunk text | Heading copied into the body (an earlier bug) |
| No empty chunks | Empty spans or sections producing chunks |

Checked that it can fail: with the heading at 11pt, the heading assert fails (`None == 'Leave Policy'`).

### Test-writing rules learned

- **A test without `assert` always passes.** It proves nothing.
- **Make sure a test can fail:** temporarily break the code (e.g. overlap 0, `continue` → `break`) and see it fail.
- **Use unusual values** (pages 3–5, not 1) so a default value cannot pass by accident.
- **Check every chunk**, not just `result[0]`.
- **Don't assert exact counts** that depend on library packing; assert the rules (`> 1`, all `<= limit`).
- **Use distinct words** per section ("First"/"Second") so mixing is detectable.
- **Feed related sections in one call**; separate calls can never mix.
- **Read a failing assert:** in `assert A == B`, `A` is what the code produced. If `A` is correct, the test is wrong.
- **Annotate test input** as `list[DocumentSection]`, otherwise the type checker sees a plain `dict` and reports an error.

### pytest tools used

| Tool | Use |
|---|---|
| `@pytest.mark.parametrize("a, b", [(1, 2), ...], ids=[...])` | Run one test with several inputs. Names in **one** string; pytest matches values to parameters by name; `ids` are labels matched by position |
| `with pytest.raises(ValueError):` | The code inside must raise that error; no `assert` needed |
| `tmp_path` | A temporary folder, deleted after the test |
| `all(cond for x in items)` | One-line "every item passes" check |
| `[x for x in items if cond]` | Filter a list (e.g. chunks of one section) |
| Function names start with `test_` | Otherwise pytest does not run them (`python_functions = ["test_*"]`) |

### Loader tests

`load_file_from_path` accepts only PDFs: it reads the first 5 bytes and requires `%PDF-`. Non-PDF and empty files raise `ValueError`; missing files raise `FileNotFoundError`.

---

## 11. Next steps

- Call chunking from the upload pipeline; inspect chunks from the real handbook.
- Later: heading path for nested headings; better heading detection (bold, length); exact per-chunk pages if needed.

---

# Part C: Embeddings

Code: `backend/src/rag_assistant/ingestion/embeddings.py`. Tests: `backend/tests/test_embeddings.py`.

**The one rule to remember:**

> One model, normalised vectors, heading for context, text kept clean.

## Cheat sheet

| Question | Short answer |
|---|---|
| What is an embedding? | 384 numbers describing a text's meaning; similar meanings → similar vectors |
| Which model and why? | `all-MiniLM-L6-v2` (`sentence-transformers`): small, fast, local, no API key |
| Why one model constant? | Vectors from different models can't be compared; changing the model means re-embedding everything |
| Why `@lru_cache` on the model loader? | Loading takes seconds; the model loads once per server run and is reused |
| What text is embedded? | `heading + "\n" + text` (contextual chunk header); the stored `text` stays clean |
| Why one `encode` call for all chunks? | Batching: overhead paid once, maths done in parallel |
| Why `normalize_embeddings=True`? | Vectors get length 1, so dot product = cosine similarity |
| Why `.tolist()`? | Chroma and JSON need plain lists, not NumPy arrays |
| Who tokenizes? | The model, inside `encode`; we only check chunks fit its limit |
| Do our chunks fit the 256-token limit? | Yes. Handbook: 100 chunks, max 235 tokens, average 128 (about 5 characters per token) |
| What do the functions return? | `embed_chunks` → chunks with an `"embedding"` field; `embed_user_query` → the bare vector |

## Testing

| Test | Protects against |
|---|---|
| Heading combined with text / no heading | Losing the contextual header; `None` heading crashing |
| Every chunk gets a vector | Wrong vector size, metadata lost, stored `text` replaced by the combined string |
| Vector length ≈ 1 (`pytest.approx`) | `normalize_embeddings` removed, silently breaking similarity scores |
| Leave question scores higher with the leave chunk | Embeddings not capturing meaning |
| Empty input → `[]` | Crashes or loading the model for nothing |

**Lesson:** a test that always passes protects nothing. The similarity test once added the office score to `leave_score`, so it passed even without real comparison.

## Known limitations

- Token counts were measured on the handbook only. Text heavy with numbers or codes uses about 2 characters per token and could exceed 256 tokens at 1000 characters.

---

# Part E: Retrieval

Code: `schemas/search_schema.py`, `routes/search_documents_route.py`, `controller/search_documents_controller.py`, `services/search_documents_service.py`, `storage/vector_store.py` → `search_chunks`. Full flow: [pipeline-walkthrough.md](pipeline-walkthrough.md) stage 10.

**The one rule to remember:**

> Top-K finds the closest chunks; the minimum score decides whether any of them are relevant at all.

## Cheat sheet

| Question | Short answer |
|---|---|
| What does `POST /retrieve` accept? | `{"question", "k", "document_id"}`, described by `SearchRequest`; FastAPI and Pydantic validate it before our code runs |
| Why `/retrieve` not `/search`? | Outcome name: return passages. Internal helpers still say `search_documents` |
| What happens with bad input? | 422 naming the field: empty `question`, `k` not a whole number from 1 to 20. `"5"` is converted to 5 |
| Why cap `k` at 20? | Every chunk returned is later sent to the LLM: more tokens, cost and noise |
| Why `k = 5` by default? | The smallest k that found the correct section for all 8 test questions; PTO ranked 4th for "annual leave" |
| Why a minimum score? | Top-K always returns k chunks, even for "What is the capital of France?" (best 0.039). Below the minimum, search returns `[]` |
| Why 0.25? | Unrelated questions topped at 0.091, correct answers started at 0.385; 0.25 leaves margin on both sides. 0.3 dropped relevant chunks |
| Why return `[]` instead of weak chunks? | Code, not the LLM, decides there is no evidence: answer "not found" without calling the LLM, so it cannot invent an answer |
| Why a separate `SearchResultItem`? | The API is a promise to the frontend; storage's `SearchResult` can change without breaking it |
| Why is the threshold in the service, not the request? | One tuned value for every caller; the generation step will call the same service |
| Why a plain `def` route? | Embedding the question is CPU work; FastAPI runs plain `def` routes in a worker thread so other requests are not blocked |
| Why a generic 500 message? | `str(e)` would show internal paths and errors to clients; the full error goes to the server log |

## Measured on the handbook (2026-11-10)

8 questions with a known correct section, 3 unrelated questions:

| Measure | Value |
|---|---|
| Correct section at rank 1 / top 3 / top 5 | 6 / 7 / 8 of 8 |
| MRR | 0.84 |
| Lowest correct-answer score | 0.385 (Overtime, rank 2) |
| Highest unrelated score | 0.091 |

## Known limitations

- **Different words for the same idea:** "annual leave" used to rank Sick leave above Paid time off (PTO); "How many leaves can I take?" used to top out ~0.152 and return empty. Hybrid puts **PTO in top 5**; cross-encoder rerank improved MRR but leaves can still sit at **PTO@2**, not always @1. Larger retrieve pool (e.g. 20 → rerank → 5) is still open.
- **One section, several chunks:** a long section split by the splitter can fill several of the 5 places with overlapping text.
- **General chunks appear often:** short or general chunks ("Time", "Tuition or relocation reimbursement") show up for many questions.
- **Small sample:** the threshold comes from 11 questions; re-check it when documents or the model change.

## Decision (2026-11-16): first Advanced RAG fix

**First:** document-agnostic query rewriting via a small LLM call (rewrite for search; do not answer; no hardcoded section names), only when the first search is weak (`[]` after `MIN_SCORE`). Optional in-memory cache later. **Next (only after measuring rewrite):** hybrid search (BM25 + dense, fused with RRF). **Later:** cross-encoder rerank on the top candidates. One lever at a time so `scripts/eval_baseline.py` shows what moved the needle. **Success for rewrite:** "How many leaves can I take?" goes from rank miss / top score ~0.152 to **Paid time off (PTO) in top 5**, score preferably **≥ MIN_SCORE 0.25**. Cost: at most one extra Gemini call when search is already weak (strong hits skip rewrite).

## Built (2026-11-17): gated rewrite — measured, leaves still miss

Code: `generation/llm_client.py` (`rewrite_userQuery` + `LLMRewriteResponse`), `services/retrieval/query_rewrite.py` (`rewrite_query`), gate in `search_documents` (strong skip; weak → rewrite once → second search; rewrite `None` → `[]`). Tests: `tests/test_search_documents.py` (3 offline). Eval via gated `search_documents`: hit@5 **7/8**, MRR **0.66** (unchanged vs Monday); leaves rewrite runs (e.g. leave-days phrasing) but **PTO still not in top 5** (other leave-ish sections win).

## Built (2026-11-17): BM25 + RRF helpers

| Piece | Code | Status |
|---|---|---|
| Sparse BM25 | `services/retrieval/bm25.py` (`_tokenize`, `bm25_search`); dep `rank-bm25` | Built + `tests/test_bm25.py` |
| BM25 smoke | `scripts/smoke_bm25.py` on real Chroma texts | Leaves-style Q → **Paid time off (PTO) at BM25 rank 4** |
| RRF | `services/retrieval/rrf.py` (`reciprocal_rank_fusion`, `RRF_K=60`) | Built + `tests/test_rrf.py` |

## Built (2026-11-18): hybrid wired into `/retrieve` — leaves fixed

**Why:** rewrite alone left leaves empty; BM25 already saw PTO at rank 4. Fuse ranks, do not add raw BM25 scores to cosine (different scales). RRF uses `1/(k+rank)` with `k=60`.

**Code:** `_hybrid_once` in `search_documents_service.py` runs dense `search_chunks` + corpus BM25 → `reciprocal_rank_fusion`, rebuilds top-k from `chunks_by_id`. Gate in `search_documents`:

| Signal | Meaning |
|---|---|
| `best_dense_score >= MIN_SCORE` (0.25) | Strong dense → return fused list; skip rewrite |
| `bm25_found` | BM25 had hits **and** dense ≥ `WEAK_DENSE_FLOOR` (0.12) → return fused list without rewrite |
| Else | Rewrite once → hybrid again; **ignore** `bm25_found` after rewrite (stops France/cake junk); only dense ≥ 0.25 may return |

**Eval (`scripts/eval_baseline.py` via gated hybrid search):** hit@5 **8/8**, MRR **0.69** (was Tue 7/8 / 0.66). Leaves → **PTO in top 5**. France / cake stay `[]`. Suite 67 passed. Gate tests mock `_hybrid_once` (tuple of chunks, best dense, `bm25_found`), not `search_chunks`.

## Built (2026-11-19): cross-encoder rerank after gate

**Why:** hybrid already put the right chunk in top-k often; order inside that list was still weak. A cross-encoder scores `(question, chunk text)` jointly and reorders. Dense `.score` on the API stays cosine (gate language + client honesty); cross logits are sort keys only.

**Code:** `services/retrieval/rerank.py` — `get_cross_encoder` / `cross_encoder_score` / `rerank(question, chunks, score_fn=None)`. Default scorer: `cross-encoder/ms-marco-MiniLM-L6-v2`. Empty → `[]`. Injectable `score_fn` for offline tests. Wired in `search_documents` on both success returns (after rewrite, score with `rewritten`). Pool = same **k=5** (no 20→5 yet).

**Tests:** `tests/test_rerank.py` (fake `score_fn`: reorder, empty, dense score kept). Gate tests mock `rerank` as identity so CI does not load the model.

**Eval:** hit@5 **8/8**, MRR **0.73** (Wed hybrid 0.69). Same hits, better average rank → higher MRR. Leaves still often **PTO@2**. France / cake stay `[]`.

## Tried (2026-11-19): larger retrieve pool — regressed, reverted

**Idea:** hybrid depth `RETRIEVE_POOL` (20 or 10) → cross-encoder rerank → return API `k` (5).

**Measured:** pool 20 → hit@5 **7/8**, MRR **0.65**; pool 10 → **7/8**, **0.66**. Missed “Employee relationships”; leaves PTO fell to @5 at pool 20. Wider list added distractors; this MS MARCO cross-encoder promoted noise into the final 5.

**Decision:** keep hybrid depth = API `k`, then rerank. Best config stays **8/8 / 0.73**. Revisit pool only with a stronger/domain reranker or more labelled cases.

## Compare + latency (2026-11-19)

**Script:** `scripts/eval_baseline.py` times `search_documents` with `time.perf_counter`. Eval must pass `document_id="employee_handbook.pdf"` — with `None`, other uploaded PDFs pollute ranks (hit fell to 7/8).

**Quality compare (same `CASES`, k=5):**

| Config | hit@5 | MRR | Keep? |
|---|---|---|---|
| Hybrid only (Wed) | 8/8 | 0.69 | baseline |
| + cross-encoder rerank | 8/8 | **0.73** | **yes** |
| pool 10/20 → rerank → 5 | 7/8 | 0.65–0.66 | **no** |

**Latency (2026-11-19 run, handbook scoped):**

| Measure | Time |
|---|---|
| First question (model load) | ~2.9 s |
| Avg after that, all cases (includes France/cake rewrite) | ~0.77 s |
| Avg handbook labelled asks (no rewrite) | **~26 ms** |

**Read:** rerank is cheap on k=5 once models are warm. Rewrite + Gemini dominates unrelated asks. Do not quote the “all questions” average as typical retrieve.

**Known UI limit:** meta asks like “summarize this document” score ~0.01 dense → gate returns `[]` → not found. Need a later whole-doc path; concrete questions on the same PDF work.

---

# Part F: Answer generation (RAG)

Code: `generation/prompt_builder.py` (`NOT_FOUND_ANSWER`, `SYSTEM_PROMPT`, `format_chunks`, `build_prompt`), `generation/llm_client.py` (`LLMResponse`, `LLMError`, `generate_answer`, `rewrite_userQuery`), `services/ask_service.py` (`ask_question`), `schemas/ask_schema.py`, `controller/ask_questions_controller.py`, `routes/ask_questions_route.py`; tests: `tests/test_prompt_builder.py`, `tests/test_ask_service.py` (6 offline tests including `LLMError` → 503). Full flow: [pipeline-walkthrough.md](pipeline-walkthrough.md) stage 11. Retrieval rewrite: see Part E (2026-11-17).

**The one rule to remember:**

> The prompt asks; code enforces.

## Cheat sheet

| Question | Short answer |
|---|---|
| What does `build_prompt` return? | `(SYSTEM_PROMPT, user_prompt)`: the fixed rules, and `Context:` + numbered passages + `Question:` |
| Why two strings? | The rules never change; the passages and question change per request. The Gemini API takes the system instruction in a separate field |
| Why are the chunks in the user message? | The system prompt holds trusted rules; document text is untrusted data |
| Why does the question come last? | Models attend most to the start and end of a prompt; the question is read right before the answer. Checked by `test_question_comes_after_context` |
| Why number passages from 1? | A citation `[n]` maps to `chunks[n - 1]`. Starting at 0 gives `chunks[-1]`, the last chunk: the wrong page with no error |
| Why is the label `[1] Resignation` with no pages? | Code takes the page from `chunks[n - 1]` metadata; the model only picks the passage. A page in the prompt adds tokens and can be copied wrongly into the answer text. Test 1 asserts `"(pages" not in user_prompt` |
| Why hide `score` and `document_id`? | The score measures similarity, not truth; the model could ignore a low-score passage that holds the answer. Fewer tokens |
| Why structured output (JSON)? | Free text forced code to guess: match an exact sentence for "not found" and tell `[1]` citations apart from `[ two weeks ]` placeholders. Gemini now fills `LLMResponse`: `found`, `answer`, `citations`; code reads the fields |
| Where is `NOT_FOUND_ANSWER` used now? | Only by the service, as the user-facing text for every "not found" case. It is no longer in the prompt (`test_system_prompt_has_found_rule` checks that) |
| Why a separate `LLMResponse` and `AskResponse`? | `LLMResponse` is what Gemini returns (passage numbers); `AskResponse` is what the user gets (headings and pages). The service converts one into the other |
| Why three "not found" paths? | Search `[]` (France, no Gemini call); `found: false` (pet dog: chunks pass the score but do not answer, only the LLM can tell); `found: true` with no valid citation (an untraceable answer is not shown) |
| Why check the citation numbers? | The model can cite a number that was never sent; `chunks[n - 1]` would crash or point to the wrong chunk. Numbers outside `1..len(chunks)` and repeats are dropped, order kept |
| What is in a `Source`? | `heading`, `page_number`, `end_page`, `document_id`: what the user needs to find the passage. No `text` (large) and no `score` (internal) |
| Why `found: bool` in `AskResponse`? | The frontend checks one field instead of comparing the answer with a sentence |
| Why 503 for `LLMError` and 500 for the rest? | 503: a service we depend on is down, try again later. 500: a bug in our code. `except LLMError` comes first because it is also an `Exception` |
| Why 15 s × 2 attempts? | Choose the user's waiting budget first (~30 s), then split it. 30 s × 3 would be ~95 s. A normal reply takes 1–3 s |
| Why is 429 not retried? | The SDK retries 408, 429 and 5xx by default. A free-tier daily limit does not fix itself, so retrying only keeps the user waiting |
| Why create the client on first use (`lru_cache`)? | `genai.Client()` raises `ValueError` without a key. Created at import, every file that imports `llm_client` (including tests with a fake) would need a real key |
| Why `GEMINI_MODEL` in `.env` but temperature in code? | Google retires model names (`gemini-2.5-flash-lite` returned 404 "no longer available to new users" on 2026-11-13); changing `.env` needs no code change. Temperature and token limits are design decisions tied to the prompt |
| Why `load_dotenv(ENV_PATH)` with a full path? | Without it, `.env` is searched in the working folder; running from the project root gave "No API key was provided" |
| Why does `build_prompt([])` raise `ValueError`? | The service returns "not found" before calling it. The error is a safety net: an empty context invites an answer from training memory |
| Is the "passages are data" rule a guarantee? | No, it is a request. Enforcement is in code: citation checks, structured output, and an LLM with no tools |

## Known limitations

- **Grounding is requested, not enforced:** code can check that a cited number was sent, not that the passage supports the sentence (needs evaluation, Phase 14).
- **JSON mode drops placeholder brackets:** the handbook's `[ two weeks ]` template value came back as "two weeks'" stated as a fact; in free-text mode the brackets were kept.
- **Temperature 0.3 on a Gemini 3.x model:** Google recommends the default 1.0 for these models; watch for repeated or cut-off answers.
- **A wrong `GEMINI_MODEL` is found only at the first question** (no startup check yet).
- Offline ask-service tests mock Gemini; there is no live HTTP e2e for `POST /answer` yet.

---

# Part G: Frontend

Code: `frontend/hooks/use-document-upload.ts`, `hooks/use-chat.ts`, `lib/api.ts` (`uploadDocument`, `askQuestion`), `components/workspace.tsx`, `chat-panel.tsx`, `chat-message.tsx`; types: `types/ask.ts`, `types/chat.ts`, `types/document.ts`. Full ask path: [pipeline-walkthrough.md](pipeline-walkthrough.md) §13.5.

**The one rule to remember:**

> Upload filename is `document_id`. Chat must send it, or search hits every PDF in Chroma.

## Cheat sheet

| Question | Short answer |
|---|---|
| How does the browser reach FastAPI? | `fetch('/api/...')` → Next rewrite → `127.0.0.1:8000` (`next.config.ts`) |
| What does upload keep for chat? | Ready state holds `UploadDocumentResponse.filename` (and pages for the text view) |
| Why pass `filename` into `useChat`? | Backend stores chunks under `document_id = file_name` in `add_chunk_to_db`. Same string filters `/answer` |
| What if `document_id` is null? | Backend searches **all** documents; an older handbook can win over a new PDF |
| Why remount chat with `key={documentName}`? | Fresh message list when the uploaded file changes; remount alone does **not** scope retrieval |
| What does `askQuestion` send? | `{ question, document_id }` (optional `k`); expects `{ question, answer, found, sources }` |
| Where do sources show? | `useChat` stores `response.sources` on the assistant row; `chat-message` lists heading + pages; `[n]` in the answer text is styled |
| Why abort only on unmount? | Cancelling mid-flight on every new send is easy to get wrong; one in-flight ask is enough for now (`sendingRef`) |
| Why not call `/retrieve` from the UI yet? | Chat needs a grounded reply + citations; `/answer` already runs the same search inside the service |

## Known limitations

- **Filename as id:** two different PDFs with the same name replace each other in Chroma; different names accumulate until deleted by re-upload of that name.
- **No `/retrieve` panel:** passages are not shown as a separate debug list in the UI.
- **Sources omit passage text:** matches `AskResponse` (heading/pages only); the answer body carries the cited facts.

---

# Part H: Streaming answer path

Code: `generation/prompt_builder.py` (`STREAM_SYSTEM_PROMPT`, `build_stream_prompt`), `generation/llm_client.py` (`stream_answer`), `services/ask_service.py` (`stream_ask_question_events`), `controller/ask_questions_controller.py` (`ask_stream_controller`), `routes/ask_questions_route.py` (`POST /answer/stream`), `frontend/app/api/answer/stream/route.ts`, `frontend/lib/api.ts` (`streamAskQuestion`), `frontend/hooks/use-chat.ts`. Tests: `backend/tests/test_ask_service.py` (3 stream generator tests). Full flow: [pipeline-walkthrough.md](pipeline-walkthrough.md) stage 12.

**The one rule to remember:**

> JSON `/answer` has a schema; the stream does not. Code parses `[n]` from the plain-text answer to find citations.

## Cheat sheet

| Question | Short answer |
|---|---|
| Why keep JSON `/answer` and add `/answer/stream` as a twin? | The JSON path is already used and tested; the stream path is additive. One LLM call per request, one endpoint per use case |
| Why plain-text tokens on the stream, not streamed JSON? | Streaming JSON is not safe: a half-received JSON object is unparseable. Plain text arrives immediately; the final `done` event carries sources as a complete JSON payload |
| Why does the stream need `_citations_from_answer` when JSON has `citations`? | The JSON path uses `response_schema` so Gemini returns a structured `{"found", "answer", "citations"}` object. The stream path uses `generate_content_stream` with no schema; the model generates free text with `[n]` markers. `_citations_from_answer` reads those markers from the accumulated answer string after all tokens arrive |
| Why accumulate `full_answer` while streaming tokens? | Each token is yielded live; citations can only be parsed after the last token. `full_answer` holds the joined text for `_citations_from_answer` to run on |
| Why does the `done` event carry `found` and `sources`? | The frontend needs to know whether to show the sources panel. A single final event avoids a separate sources request |
| Why is `error` a separate event type, not an HTTP error? | Once `StreamingResponse` starts writing, the HTTP status is already 200. Errors inside the generator must be carried as SSE events |
| Why does the controller have no try/except? | Errors are `{"type":"error"}` SSE events emitted inside the generator. The route layer never sees them as Python exceptions |
| Why a Route Handler (`app/api/answer/stream/route.ts`) instead of the Next.js rewrite? | The rewrite in `next.config.ts` collects the full response before forwarding it. A Route Handler returns `response.body` (a `ReadableStream`) directly, so tokens reach the browser as they arrive |
| Why split the SSE buffer on `\n\n`? | Network chunks do not align with SSE events. Each event ends with `\n\n`; splitting there gives complete events. The last incomplete fragment is saved in `buffer` for the next read |

## Locked design decisions

- `GROUNDING_RULES` is shared between both paths. `SYSTEM_PROMPT` + `response_schema` for JSON; `STREAM_SYSTEM_PROMPT` (plain text, same exact not-found sentence) for stream. Same `_user_prompt` format for both.
- Sources always come from chunk metadata (`heading`, pages, `document_id`). The model never chooses page numbers on the stream path any more than on the JSON path.
- The stream path does **not** have a `citations` field in the response; it has a `done` event with `sources` derived from `_citations_from_answer`.
- If `_citations_from_answer` returns `[]` (no valid `[n]` in the answer), the `done` event has `found: false` and `sources: []`. Same "not found" outcome as the JSON path.

## Known limitations

- **Streaming visual effect deferred:** backend streams correctly (confirmed in EventStream tab); text appears all at once in the browser. Root cause: likely Next.js dev server (Turbopack) buffering. `flushSync` added to `onToken` in `use-chat.ts` did not resolve it. Revisit: disable `cacheComponents` in `next.config.ts`, or test in production build (`npm run build && npm start`).
- **No abort mid-stream from the client:** `AbortController` is wired but only fires on chat unmount, not on a new question while one is in flight.
