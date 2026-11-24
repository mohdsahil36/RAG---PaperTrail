# Daily Plan and Study Queue

The day's build plan and study topics. Unfinished **build** items move to the next day.  
`[x]` on the roadmap only if theory **and** code exist (for pure theory: explain without notes + a tiny example / project link).

**Current phase:** Evolve the app on Part 2 (track 7 prompts → streaming next → memory → agents → …). **In parallel**, keep working earlier unchecked topics (NN, loss, backprop, Python/backend gaps, …) in theory and code as they connect to what we build. Only `git init` waits until the end.

**Two living docs (keep current after each build slice):**
- Project understanding: `docs/design-notes.md` + `docs/pipeline-walkthrough.md`
- Interviews: `docs/interview-qa-bank.md` (revision list + scenarios)

**Interview prep:** on request, not every day by default.

---

## Dual track (standing rule)

| Track | What | Pace |
|---|---|---|
| **A — App** | Part 2 order: prompts → memory → agents → … | Main daily Important work |
| **B — Foundations / early gaps** | Unchecked earlier topics (backprop, DI, …) | Alongside A: Know first, short study, tiny code when it fits the slice — not a hijack of the day |

Do **not** park B forever. Do **not** make B the whole day unless you choose that. Prefer: one B topic linked to today’s A work when possible.

---

## Every day (order)

1. **Recall** — 1–2 questions (app + one foundation gap if due)  
2. **Important work** — main app slice (Track A)  
3. **Theory → coding** — for A, and a bite of B when it supports A  
4. **Docs** — what you shipped/measured  
5. **Stretch** — only after Important  

**Daily bar:** finish the app Important work. Advance B steadily. `git init` at end of the track.

---

## Plan: Tuesday 2026-11-24

**Resume point:** Streaming closed (40a/40b/40c/42 done). Prompt regression theory done (partly covered). Function/tool calling theory done — ready to build.

**Day goal:** Build `ask_question_with_tools` — Gemini function calling, two-call loop, `POST /answer/tools`.

**Know first (before coding):** Gemini `FunctionDeclaration` schema (name, description, parameters as JSON Schema); how `contents` grows across turns (user → model function_call → function_response → model answer).

### 1. Recall
- What does Gemini receive on the first tool call request, and what does it reply with instead of an answer?
- Why is the tool call loop a minimum of two LLM calls?

### 2. Important work (Track A)
| # | Task | Done when |
|---|---|---|
| 43a | `FunctionDeclaration` for `search_documents` in `llm_client.py` | Schema declared; name, description, parameters correct |
| 43b | `ask_question_with_tools` in `ask_service.py` | Two-call loop: question → tool_call → search → answer; grounding rule enforced |
| 43c | `POST /answer/tools` route | Swagger returns grounded answer with sources |
| 43d | Tests | Mock tool call response; assert search called with model’s args; assert answer returned |

### 3. Track B (alongside — light)
| # | Task | Done when |
|---|---|---|
| B | NN fundamentals or loss functions — one bite | Short explain linked to MiniLM/Gemini in our stack |

### 4. Docs
| # | Task | Done when |
|---|---|---|
| 44 | `design-notes.md` Part I + pipeline stage 13 for tool calling path | Only after 43c ships |

### 5. Stretch (optional)
| # | Task | Done when |
|---|---|---|
| — | Prompt injection hardening — explicit instruction in `SYSTEM_PROMPT`, one break-attempt test | Before moving to memory |

**After tool calling:** model fallback → prompt injection close-out → Phase 7 retrieval leftovers (query expansion, parent-child) → Phase 9 memory.

---

## Done Monday 2026-11-23

| Block | Result |
|---|---|
| 40a | `stream_ask_question_events` generator; 3 stream tests; 73/73 suite |
| 40b | `POST /answer/stream` SSE route; Swagger confirmed |
| 40c | Frontend wired: Route Handler, `streamAskQuestion`, `flushSync`; answer + sources correct; visual deferred |
| 42 | `design-notes.md` Part H + `pipeline-walkthrough.md` Stage 12 |
| Theory | Prompt regression (partly covered); function vs tool calling; MCP distinction |
| Roadmap | Streaming ticked; total 96 done |

---

## Done Friday 2026-11-20

| Block | Result |
|---|---|
| Design | Stream **A**; twin `/answer/stream` SSE; keep JSON `/answer`; shared `GROUNDING_RULES` |
| Prompts | `GROUNDING_RULES` / `SYSTEM_PROMPT` / `STREAM_SYSTEM_PROMPT`; `_user_prompt`; `build_stream_prompt` |
| LLM | `stream_answer` (`generate_content_stream`, yield text; no JSON schema) |
| Service (partial) | `_citations_from_answer` + stream imports; **not** `ask_question_events` yet |
| Not done | Route, frontend, living docs for stream |

---

## Foundation / early-gap backlog (Track B — ongoing)

Work when it fits. Prefer linking to the current app slice.

### A. ML foundations
1. Neural network fundamentals (finish partly)  
2. Loss functions and gradient descent  
3. Forward and backward propagation  
4. Pretraining ↔ backprop  
5. Model families and trade-offs  
6. LoRA / quantisation *(concepts now; deep hands-on with advanced track)*

### B. Python / backend
- Generators; `Protocol` / typing; custom context managers  
- DI; auth; DB; background tasks; tighter tests; config module  

### C. Docs / vectors leftovers
- **More than PDF:** DOCX, HTML, (later) OCR/scanned — shared ingest → same chunk/embed/retrieve path  
- Tables/lists/headers; IVF; hosted embed APIs; re-index job; scaling  

### D. Better-retrieval leftovers
- Multi-query, parent–child, graph, whole-doc summarize, ACL, conflicting docs  

**Prod note:** multi-format ingest is required for a real document product — not optional polish. Schedule after streaming/memory harden the ask path, or earlier if upload demand forces it. Keep one pipeline; only the loader changes per type.

**Policy:** full roadmap in scope. **Only `git init` deferred to the end.**

---

## Done Thursday 2026-11-19

| Block | Result |
|---|---|
| Rerank + measure | CrossEncoder; pool>k reverted; **8/8 / 0.73**; ~26 ms labelled retrieve |
| Frontend | `/answer` + sources + `document_id` + layout |
| Docs + audit | Living docs; encoder/decoder + stale rows; Done **95** |

---

## How to study (when Know first is required)

1. Learn: one source, 20–30 minutes.  
2. Try: tiny REPL or point at our code.  
3. Explain: a few lines in your own words.  
4. Connect: file/function or “why this model was trained that way.”  
5. Then continue the app slice.  
6. Recall next day before new work.
