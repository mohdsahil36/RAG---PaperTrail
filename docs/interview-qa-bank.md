# AI engineering interview Q&A bank

Practice **how you speak** in an interview.  
Read the question. Answer out loud. Then compare to **What you say**.

**Style:** one clear spoken answer. Short sentences. Simple words.  
Scenarios below are practice talks. The **revision list** is what you must not skip.

**Learning rule:** while coding, do not skip required skills. Each build step must cover its theory + code. Update this list when you do interview prep (not every daily update).

---

## Revise before any interview

Status: **Ready** = theory + code in our repo · **Study only** = know it, not built · **Gap** = must learn before claiming it · **Soon** = next on the app plan

### A. Must revise (you built this — speak from the repo)

| # | Topic | Ready when you can explain… |
|---|---|---|
| A1 | PDF → text / headings / pages | How upload becomes sections |
| A2 | Chunking (size, overlap, structure) | Why bad chunks break answers |
| A3 | Embeddings (MiniLM, 384-d, normalize) | Query and chunks share one model |
| A4 | Vector DB (Chroma, metadata, `document_id`) | Store + filter + persist |
| A5 | Dense retrieval (top-K, cosine / score) | How search ranks chunks |
| A6 | `MIN_SCORE` and empty results | Why France returns `[]` |
| A7 | RAG prompt (system vs context vs question) | Why pages stay out of the prompt |
| A8 | Grounded answer + citations | How `[n]` maps to `chunks[n-1]` |
| A9 | Three not-found paths | Empty search / `found:false` / bad citations |
| A10 | LLM client (structured output, errors → 503) | What we mock in tests |
| A11 | Offline tests / mocking | Patch where the name is used |
| A12 | Retrieval eval (hit@k, MRR, labelled set) | How `eval_baseline.py` works |
| A13 | Query rewriting (gated, any-document) | Weak → rewrite once; strong skips Gemini |
| A14 | Hybrid search (BM25 + dense) | `_hybrid_once` + gate; leaves → PTO@5 |
| A15 | RRF | `reciprocal_rank_fusion`, k=60; fuse ranks not raw scores |
| A16 | Cross-encoder rerank | After gate; reorder only; dense `.score` kept; eval 8/8 / 0.73 |

### B. Know soon (in progress or next builds — revise as you finish)

| # | Topic | Status |
|---|---|---|
| B1 | Query rewriting (gated, any-document) | **Ready** (moved to A13; keep practising Scenario 3) |
| B2 | Hybrid search (BM25 + dense) | **Ready** (moved to A14; Scenario 4) |
| B3 | RRF | **Ready** (moved to A15; Scenario 4) |
| B4 | Cross-encoder reranking | **Ready** (moved to A16; Scenario 5). Sources below. |
| B5 | Frontend `/answer` UI + `document_id` scope | **Ready** (no spoken scenario yet). Eval/UI must send filename or other PDFs pollute ranks. |
| B6 | Document ACL / roles at retrieve | Gap (interview favourite) |

### C. Always revise for AI/RAG interviews (even if not fully in our app yet)

| # | Topic | Why |
|---|---|---|
| C1 | Hallucinations vs grounded generation | Core RAG pitch |
| C2 | Dense vs sparse retrieval | Trade-offs |
| C3 | When rewrite vs hybrid vs rerank | Design judgement |
| C4 | Prompt injection (direct / via docs) | Security |
| C5 | Permissions in retrieval (not in the prompt) | Security |
| C6 | Eval: labelled set, hit@k, MRR, faithfulness | “How do you know it works?” |
| C7 | Latency, cost, free-tier / rate limits | Production sense |
| C8 | Chunking failure modes | Debugging answers |
| C9 | Changing embedding model ⇒ re-embed | Ops |
| C10 | Agents vs plain RAG (tools, loops) | Next career step |

### D. General engineering (short revise)

| # | Topic |
|---|---|
| D1 | FastAPI / Pydantic validation (422) |
| D2 | Layering: route → controller → service → storage |
| D3 | Idempotent upload / replace chunks |
| D4 | Secrets (`.env`), never commit keys |
| D5 | Clear API errors (503 vs 500 vs 422) |

**Before an interview:** walk A (all) → C (all) → B (whatever is Ready) → D.  
For each Ready row: one spoken scenario in this file (add if missing).

### B4 references (CrossEncoder / rerank)

Use these while coding `retrieval/rerank.py` and when revising B4:

| Doc | URL | Use for |
|---|---|---|
| Sentence-Transformers — Cross Encoder usage | https://sbert.net/docs/cross_encoder/usage/usage.html | `CrossEncoder`, `predict` on `(query, passage)` pairs |
| Pretrained CrossEncoder models | https://sbert.net/docs/cross_encoder/pretrained_models.html | MS MARCO rerankers; model pick |
| Model card `ms-marco-MiniLM-L6-v2` | https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2 | Load example; logit scores; ranking note |
| Usage source (GitHub) | https://github.com/huggingface/sentence-transformers/blob/main/docs/cross_encoder/usage/usage.rst | Same as sbert.net usage |
| Offline API help | `python -c "from sentence_transformers import CrossEncoder; help(CrossEncoder.predict)"` | `predict` args in the venv |

**Our model id:** `cross-encoder/ms-marco-MiniLM-L6-v2`.  
**Repo today:** default CrossEncoder in `rerank`; fake `score_fn` in unit tests; gate tests mock `rerank`. Eval hit@5 **8/8**, MRR **0.73**. Pool still same k=5.

---

## Scenario 1

**They ask:**  
You build an assistant on company docs. An intern asks about executive pay. Search pulls a secret HR doc. The model answers correctly from it. Is your system working?

**What you say:**  
No. The answer may be factually right, but the system is wrong on access.

RAG finds similar text. It does not decide who is allowed to see a file.  
If the secret chunk enters the prompt, the secret is already out.  
Telling the model “do not share confidential data” is not enough. A prompt is not a permission check.

I would resolve the user’s allowed documents first, then search only inside that set.  
I would also test with two roles: the intern must not retrieve that file; a privileged role may.

Accuracy and authorization are different problems. RAG alone does not solve both.

**If they push:**  
“How do you measure quality then?”  
→ I keep a small labelled question set for retrieval (hit rate, MRR), and separate access tests per role. The product stays general; the tests are specific.

**Our code today:**  
We have `/retrieve` and `/answer`. We can filter by `document_id` if the caller sends it. We do **not** have real user-role ACL yet.

---

## Scenario 2

**They ask:**  
Your pipeline accepts any PDF. Why do you keep fixed handbook questions in an eval script?

**What you say:**  
The product is general. The eval set is not the product.

To know if search got better or worse, I need questions with a known right section.  
Then I can report hit@k and MRR.  
Scores alone only say “similar,” not “correct.”

When documents change, I add or refresh labelled cases. I do not pretend an unlabelled run is a proof.

**Our code today:**  
`scripts/eval_baseline.py` is that ruler for the sample handbook.

---

## Scenario 3

**They ask:**  
Users say “How many leaves can I take?” Your dense search scores about 0.15 and returns nothing useful. What do you do first?

**What you say:**  
I treat that as a weak search, not as “the answer is missing from the company.”

First I keep a minimum score so junk chunks never reach the LLM.  
If nothing clears that bar, I may rewrite the question for search only — same meaning, no answer, no hardcoded section names.  
Then I search once more. Strong hits skip the rewrite to save cost and latency.

Rewrite can still fail. Different words may still miss the right section.  
Then I look at sparse search or hybrid, not at more prompt tricks alone.

**If they push:**  
“Did rewrite fix it in your project?”  
→ We built a gated rewrite and measured. Hit rate and MRR stayed 7/8 and 0.66. Leaves still missed. So we moved to BM25 next.

**Our code today:**  
`rewrite_query` + gate in `search_documents`. Three offline gate tests. Eval uses the gated path.

---

## Scenario 4

**They ask:**  
Dense and BM25 disagree. One list loves meaning. The other loves keywords. How do you combine them?

**What you say:**  
I do not add the raw scores. They live on different scales.

I keep each list as a ranking. Then I fuse with reciprocal rank fusion.  
Each place gives about one over k plus rank. I add those contributions per document.  
Documents that rank well in both rise. I sort by that total.

That way a keyword hit like PTO can help even when the embedding was weak.

**If they push:**  
“Is hybrid live in your API?”  
→ Yes. `_hybrid_once` fuses dense and BM25 with RRF on every `/retrieve` (and inside `/answer`). Gate keeps rewrite for weak dense; after rewrite we ignore `bm25_found` so France stays empty. Eval hit@5 8/8, MRR 0.69; leaves → PTO in top 5.

**Our code today:**  
`bm25_search`, `reciprocal_rank_fusion`, `_hybrid_once` + gate in `search_documents`. Tests mock `_hybrid_once`. Smoke still shows PTO at BM25 rank 4 alone.

---

## Scenario 5

**They ask:**  
Hybrid already returns five candidates. Why add a cross-encoder? Does it invent new documents?

**What you say:**  
It does not invent documents. It only reorders the short list.

Hybrid is cheap recall: dense meaning plus keywords, fused by rank.  
A cross-encoder reads the question and each passage together and scores that pair.  
That is slower, so I run it only on the top few.

I keep the dense cosine on each result for the API and the gate.  
Cross scores are for sort order only. Same set of chunks; better position for the right one raises MRR even when hit@5 stays flat.

**If they push:**  
“What did you measure?”  
→ After wiring `ms-marco-MiniLM-L6-v2`, hit@5 stayed 8/8 and MRR moved from 0.69 to 0.73. Leaves can still sit at PTO rank 2. We tried pool 20 and 10 then cut to 5; both regressed (7/8, ~0.65–0.66), so we keep hybrid depth = API k.

**Our code today:**  
`retrieval/rerank.py` (`cross_encoder_score`, `rerank`) after the gate in `search_documents`. Fake `score_fn` tests; gate tests mock `rerank`.

---

## How to add the next card

1. Write **They ask** in one or two sentences (real interview voice).  
2. Write **What you say** as one spoken answer (about 6–10 short lines).  
3. Optional one **If they push** follow-up.  
4. One honest **Our code today** line.  

No topic folders required. Group only if the list gets long.

## Backfill

Queued: turn earlier build work into more **scenarios** (ingest, chunking, embeddings, `MIN_SCORE`, `/ask`, mocking).  
Rewrite + BM25/RRF cards added 2026-11-17. Hybrid live + Scenario 4 honesty updated 2026-11-18. B4 links + Scenario 5 + A16 Ready 2026-11-19 (eval 8/8 / 0.73). B5 Ready with doc-scope honesty; compare/latency in Part E 2026-11-19.
