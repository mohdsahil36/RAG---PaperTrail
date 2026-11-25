# AI Engineering Roadmap

Personal learning and development roadmap for becoming an AI engineer.
Part 1 lists every topic to learn. Part 2 is the order to learn and build them in, using this project (RAG Document Assistant) as the main build.

Status is updated from the daily and monthly updates. See the [progress log](#progress-log) at the end.

## Now

**Current step:** Part 2, [step 7: Prompt engineering and LLM application development](#7-prompt-engineering-and-llm-application-development). Function/tool calling closed (2026-11-24): `SEARCH_TOOL`, `answer_with_tools`, `ask_question_with_tools`, `POST /answer/tools`. Total done: **98**.

**How we work:** evolve the **app** on the Part 2 path, and keep closing earlier unchecked topics **in parallel** (theory + code when it fits — e.g. backprop while we reason about MiniLM/Gemini; DI when we touch FastAPI). Not a separate “stop the product” semester.

**Next actions** (2026-11-24):

1. **Tests for tool calling path** — mock `answer_with_tools`; assert `search_documents` called with model's query; assert grounded `AskResponse`.
2. **Model fallback** — second model in `.env`, retry on 429/404.
3. **Prompt regression testing** — snapshot suite: fixed questions → assert `found: true` + expected source headings.
4. **Between Phase 8 and 9:** query expansion + parent-child retrieval (Phase 7 leftovers — one session).
5. Then [step 8 memory](#8-context-engineering-and-memory) → agents.
6. Ongoing: foundation / early-gap backfill (generators, NN/loss/backprop) — tick when explainable + linked to the project.
7. **Multi-format docs** (DOCX, HTML, later OCR) — required for prod; same pipeline after a per-type loader.

**Deferred to end of track only:** `git init`. Nothing else is “skip forever.”

## How to use this roadmap

**Learning loop for every item**

1. **Study**: learn the concept from one good source
2. **Explain**: write it in your own words in `docs/` (short notes and one example)
3. **Build**: implement the smallest working version in this project
4. **Test**: add a test that proves it works
5. **Record**: tick the box here and mention it in the daily update

**What "done" means**

- `[x]` **only if both are true:** (1) you can explain the topic without notes with an example, and (2) working code for it exists in this repo (with tests where this project has them)
- Theory studied but not built → keep `[ ]` and mark `*(partly covered: studied; not in code yet)*` (or list under "Also covered")
- Part 2 build rows: code in the repo and tests pass
- Only tick what is true today; planned work stays unticked

**Legend**

- `[x]` Done
- `[ ] ... (in progress)` Actively being worked on now (only items in the current step)
- `[ ] ... (partly covered)` Touched as part of other work, not being worked on yet
- `[ ]` Not started
- *(added)* Item added to the original roadmap

## Progress summary

Part 1 topics only. The "Also covered" list is not counted.

| Phase | Done | In progress | Partly covered | Total |
|---|---|---|---|---|
| Phase 0: Python foundations | 9 | 0 | 3 | 13 |
| Phase 1: AI backend engineering | 7 | 0 | 3 | 13 |
| Phase 2: Document processing and chunking | 13 | 0 | 1 | 18 |
| Phase 3: Machine learning and LLM foundations | 15 | 0 | 1 | 22 |
| Phase 4: Embeddings and vector search | 8 | 0 | 2 | 11 |
| Phase 5: Vector databases | 8 | 0 | 2 | 12 |
| Phase 6: Core RAG engineering | 14 | 0 | 0 | 15 |
| Phase 7: Advanced retrieval and RAG | 9 | 0 | 3 | 15 |
| Phase 8: Prompt engineering and LLM application development | 8 | 0 | 4 | 15 |
| Phase 9: Context engineering and memory | 0 | 0 | 0 | 19 |
| Phase 10: Agent engineering | 0 | 0 | 0 | 21 |
| Phase 11: Agent frameworks and protocols | 0 | 0 | 2 | 16 |
| Phase 12: Harness engineering | 0 | 0 | 0 | 19 |
| Phase 13: Agentic software development | 0 | 0 | 0 | 14 |
| Phase 14: Evaluation and testing | 6 | 0 | 2 | 17 |
| Phase 15: AI security and safety | 0 | 0 | 2 | 17 |
| Phase 16: Production AI engineering | 1 | 0 | 5 | 26 |
| Phase 17: Multimodal AI | 0 | 0 | 0 | 11 |
| Phase 18: Advanced model engineering | 0 | 0 | 0 | 11 |
| Phase 19: AI system design and interviews | 0 | 1 | 0 | 18 |
| **Total** | **98** | **1** | **30** | **323** |

---

# Part 1: Topics

## Phase 0: Python foundations

- [x] Python syntax and fundamentals
- [x] Variables and data types
- [x] Lists, tuples, sets, and dictionaries
- [x] Conditions and loops
- [x] Functions and modules
- [x] Classes and OOP fundamentals
- [x] Exceptions and error handling
- [ ] Type hints and advanced typing *(partly covered: type hints,* `TypedDict`*,* `Annotated`*, data classes done; generics and* `Protocol` *next)*
- [ ] Iterators and generators
- [x] Decorators
- [ ] Context managers *(partly covered:* `with` *for files and temporary files; writing your own next)*
- [ ] Async Python and concurrency *(partly covered: async FastAPI endpoints)*
- [x] Advanced pytest, fixtures, and mocking

## Phase 1: AI backend engineering

- [x] FastAPI application setup
- [x] Router and endpoint organisation
- [x] File upload endpoint using UploadFile
- [x] PDF file validation
- [x] Temporary file handling
- [x] Pydantic models and validation
- [ ] Dependency injection
- [ ] Authentication and authorisation
- [ ] Async endpoints and background tasks *(partly covered: async endpoints done, background tasks not started)*
- [ ] Database integration
- [x] API error handling and response contracts *(theory + code: 422 Pydantic; upload 400/500;* `/retrieve` *+* `/answer` **`response_model`*;* `LLMError` *→ 503)*
- [ ] Integration and API testing *(partly covered:* `TestClient` **`/retrieve`*; offline* `test_ask_service` */ gate / rerank; upload still mostly manual)*
- [ ] Logging and configuration management *(partly covered:* `logger.exception` *in controllers;* `GEMINI_MODEL` */ key via* `backend/.env` *— no structured config module yet)*

## Phase 2: Document processing and chunking

- [x] PDF extraction using PyMuPDF
- [x] Page-level text extraction
- [x] Text cleaning and normalisation for RAG *(added)*
- [x] Span extraction
- [x] Font metadata extraction
- [x] Heading identification
- [x] Document section construction
- [x] Section metadata preservation
- [x] Recursive character splitting using LangChain
- [x] Chunk-size and overlap testing
- [x] Chunk metadata validation
- [x] Real-PDF chunk quality inspection *(theory + code: handbook 100 chunks, max 235 tokens; design-notes + pipeline numbers)*
- [ ] Handle tables, lists, headers, and footers
- [ ] Handle malformed and scanned PDFs *(partly covered: invalid-PDF errors, scanned-page detection studied)*
- [ ] OCR fundamentals
- [ ] DOCX, HTML, and other document ingestion
- [x] Document versioning and deletion *(theory + code:* `add_chunk_to_db` *delete-by-*`document_id` *then upsert; re-upload replaces one file)*
- [ ] Incremental document processing

## Phase 3: Machine learning and LLM foundations

Ordered from neural network basics up to LLMs. LoRA, QLoRA and quantisation are covered as concepts here and hands-on in Phase 18.

- [ ] Neural network fundamentals *(partly covered: linear layers and feed-forward networks studied)*
- [ ] Loss functions and gradient descent
- [ ] Forward and backward propagation in detail
- [ ] Pretraining and backpropagation relationship
- [x] Tokenisation fundamentals
- [x] Character, word, and subword tokenisation
- [x] BPE fundamentals
- [x] Vocabulary and one-hot encoding
- [x] Embedding dimensions
- [x] Positional information
- [x] Attention and Q, K, V
- [x] Softmax
- [x] Self-attention and multi-head attention
- [x] Transformer architecture end-to-end
- [x] Encoder vs decoder architectures *(theory + project use: encoder-style bi-encoder MiniLM for embed/search; cross-encoder for rerank pairs; decoder-style Gemini for generate — dense* `.score` *vs cross logits kept separate)*
- [x] Inference and generation
- [x] Temperature, top-p, and sampling
- [x] Context-window limits
- [ ] Model families and capability trade-offs
- [x] Fine-tuning fundamentals
- [ ] Fine-tuning methods: LoRA and QLoRA
- [ ] Quantisation fundamentals

## Phase 4: Embeddings and vector search

- [x] What embeddings represent
- [x] How embedding models transform text into vectors
- [ ] Embedding model selection *(partly covered: chose local MiniLM for dense +* `ms-marco-MiniLM-L6-v2` *for rerank; no full bake-off)*
- [ ] Generate embeddings through model APIs
- [x] Similarity metrics: cosine, dot product, Euclidean distance
- [x] Vector normalisation
- [x] Vector dimensions and storage
- [x] Embedding input limits and token limits
- [x] Batch embedding generation
- [ ] Embedding versioning *(partly covered:* `embedding_model` *in Chroma metadata; no migrate/re-embed job yet)*
- [x] Embedding model changes and re-indexing

## Phase 5: Vector databases

- [x] Why vector databases exist
- [x] Vector database architecture
- [x] Collections and indexes
- [x] Vector storage and retrieval
- [x] Approximate nearest neighbour search
- [ ] HNSW and IVF fundamentals *(partly covered: HNSW studied, IVF not yet)*
- [x] Metadata storage and filtering
- [x] Similarity metrics in vector databases
- [x] Persistence and deletion
- [ ] Vector database selection and trade-offs *(partly covered: chose Chroma for local persistent RAG; no multi-DB comparison)*
- [ ] Scaling vector search
- [ ] Multi-tenant vector storage

## Phase 6: Core RAG engineering

- [x] RAG architecture
- [x] Ingestion-to-retrieval pipeline
- [x] Store chunks, embeddings, and metadata
- [x] Query embedding
- [x] Top-K retrieval
- [x] Similarity thresholds
- [x] Metadata filtering
- [x] Context construction
- [x] Prompt construction for RAG
- [x] Grounded answer generation
- [x] Source attribution and citations
- [x] Handling insufficient context
- [ ] Handling conflicting documents
- [x] Retrieval failure analysis
- [x] End-to-end RAG API

## Phase 7: Advanced retrieval and RAG

- [x] Dense retrieval *(theory + code: MiniLM + Chroma* `search_chunks`*)*
- [x] Sparse retrieval and BM25 *(theory + code:* `bm25_search` *+* `tests/test_bm25.py`*; smoke on Chroma)*
- [x] Hybrid search *(theory + code:* `_hybrid_once` *dense + BM25 → RRF in* `search_documents`*; eval 8/8 / 0.69 then 0.73 with rerank)*
- [x] Reciprocal rank fusion *(theory + code:* `reciprocal_rank_fusion` *+* `tests/test_rrf.py`*; wired)*
- [x] Reranking models *(theory + code:* `rerank` *+* `cross_encoder_score` */* `ms-marco-MiniLM-L6-v2` *after gate; fake* `score_fn` *tests; eval 8/8 / 0.73)*
- [x] Query rewriting *(theory + code: gated LLM rewrite in* `rewrite_query` *+* `search_documents`*; hybrid now fixes leaves)*
- [ ] Query expansion and decomposition *(partly covered: studied; not in code yet)*
- [ ] Parent-child retrieval *(partly covered: parent-child chunking studied)*
- [ ] Multi-query retrieval *(partly covered: studied; not in code yet)*
- [x] Metadata-aware retrieval *(theory + code: Chroma* `document_id` *filter; UI + eval pass filename; unscoped search polluted by other PDFs)*
- [ ] Graph RAG
- [ ] Knowledge graph construction
- [ ] Entity resolution
- [x] Retrieval evaluation *(theory + code:* `scripts/eval_baseline.py`*)*
- [x] RAG optimisation and trade-offs *(theory + code: hybrid vs rerank vs pool>k compare; latency split load/rewrite/labelled; Part E)*

## Phase 8: Prompt engineering and LLM application development

- [x] System, developer, and user instruction hierarchy *(theory + code:* `SYSTEM_PROMPT` */ rewrite system vs user contents; no separate developer role channel)*
- [x] Prompt structure and reusable templates *(theory + code:* `SYSTEM_PROMPT`*,* `REWRITE_SYSTEM_PROMPT`*,* `build_prompt` */* `format_chunks`*)*
- [ ] Zero-shot and few-shot prompting *(partly covered: grounded ask is zero-shot with passages; no few-shot bank yet)*
- [ ] Role and task specification *(partly covered: system role in* `SYSTEM_PROMPT`*; not generalised)*
- [x] Constraints and output contracts *(theory + code: found/citations rules;* `LLMResponse` *shape; citation range check in* `ask_question`*)*
- [x] Structured output generation
- [x] JSON schema validation *(theory + code: Gemini* `response_schema=LLMResponse` */* `LLMRewriteResponse`*; bad parse →* `LLMError`*)*
- [x] Function calling *(theory + code: `FunctionDeclaration` / `SEARCH_TOOL` in `llm_client.py`; `answer_with_tools` call 1; Gemini picks search query via tool call; 2026-11-24)*
- [x] Tool calling *(theory + code: `ask_question_with_tools` two-call loop → `POST /answer/tools`; tool query feeds `search_documents`; answer via standard `generate_answer`; thinking model limitation noted; tests pending 2026-11-25)*
- [x] Streaming responses *(theory + code:* `stream_ask_question_events` *generator →* `POST /answer/stream` *SSE;* `stream_answer` *with* `generate_content_stream`*;* `_citations_from_answer` *on accumulated plain text; frontend Route Handler +* `streamAskQuestion`*; 3 stream generator tests; 2026-11-23)*
- [ ] Prompt versioning
- [ ] Prompt testing and regression testing *(partly covered:* `test_prompt_builder.py`*; no prompt snapshot suite yet)*
- [ ] Prompt injection awareness *(partly covered: passages-are-data rule in system prompt; not red-teamed)*
- [ ] Model provider abstraction
- [ ] Model fallback strategies

## Phase 9: Context engineering and memory

- [ ] Context engineering fundamentals
- [ ] Context windows and token budgeting
- [ ] Context selection and prioritisation
- [ ] Context relevance and freshness
- [ ] Context compression
- [ ] Context summarisation
- [ ] Context compaction
- [ ] Context rot and attention dilution
- [ ] Conversation history management
- [ ] Short-term memory
- [ ] Long-term memory
- [ ] Episodic memory
- [ ] Semantic memory
- [ ] Procedural memory
- [ ] Retrieval-based memory
- [ ] Persistent agent memory
- [ ] Knowledge graphs for context
- [ ] Multi-agent context isolation
- [ ] Context provenance and updates

## Phase 10: Agent engineering

- [ ] LLM calls vs AI agents
- [ ] Agent architecture
- [ ] Agent loop engineering
- [ ] Observe → decide → act → inspect
- [ ] Planning and task decomposition
- [ ] Tool selection
- [ ] Tool schemas and descriptions
- [ ] Tool execution
- [ ] Agent state management
- [ ] Agent memory
- [ ] Reflection and verification
- [ ] Loop termination
- [ ] Iteration and token limits
- [ ] Retry and recovery strategies
- [ ] Deterministic workflows vs autonomous agents
- [ ] Single-agent systems
- [ ] Multi-agent systems
- [ ] Agent delegation and coordination
- [ ] Human-in-the-loop approval
- [ ] Long-running agents
- [ ] Agent session recovery

## Phase 11: Agent frameworks and protocols

- [ ] LangChain fundamentals
- [ ] LangChain retrievers and chains
- [ ] LCEL
- [ ] LangGraph fundamentals
- [ ] Graph state
- [ ] Nodes and edges
- [ ] Conditional routing
- [ ] Checkpointing
- [ ] Persistence
- [ ] Human approval workflows
- [ ] LangSmith tracing and evaluation
- [ ] MCP architecture *(partly covered: studied in October, not retained; revisit in Phase 11)*
- [ ] MCP clients and servers *(partly covered: MCP server architecture studied)*
- [ ] MCP tools and resources
- [ ] MCP authentication and permissions
- [ ] Framework abstractions vs custom implementations

## Phase 12: Harness engineering

- [ ] What an AI harness is
- [ ] Agent runtime architecture
- [ ] Model-runtime boundaries
- [ ] Agent execution environment
- [ ] Tool permissions and policies
- [ ] Sandboxed execution
- [ ] State and session persistence
- [ ] Context loading and compaction
- [ ] Tool-result validation
- [ ] Checkpoints and resumability
- [ ] Idempotent tool execution
- [ ] Parallel tool execution
- [ ] Concurrency and race conditions
- [ ] Execution budgets
- [ ] Timeouts and cancellation
- [ ] Failure recovery
- [ ] Execution tracing
- [ ] Progress reporting
- [ ] Approval and intervention controls

## Phase 13: Agentic software development

- [ ] Coding-agent architecture
- [ ] Repository and codebase context retrieval
- [ ] Codebase indexing
- [ ] Planning code changes
- [ ] Task decomposition
- [ ] Code execution and feedback loops
- [ ] Automated testing and repair loops
- [ ] Debugging agents
- [ ] Git and version-control integration
- [ ] Agent permissions
- [ ] Code execution sandboxing
- [ ] Human approval for code changes
- [ ] Coding-agent evaluation
- [ ] Multi-step software engineering workflows

## Phase 14: Evaluation and testing

- [ ] AI application testing strategy *(partly covered: offline unit/API tests +* `eval_baseline`*; no full test pyramid doc)*
- [x] Evaluation dataset creation *(theory + code: labelled* `CASES` *in* `scripts/eval_baseline.py` *— handbook + unrelated)*
- [x] Retrieval precision and recall
- [x] MRR and NDCG
- [ ] Answer correctness
- [x] Answer relevance
- [x] Faithfulness and groundedness
- [ ] Hallucination evaluation *(partly covered: hallucination fundamentals studied; grounded* `found`*/citations enforce a floor)*
- [ ] LLM-as-a-judge
- [ ] LLM judge limitations
- [ ] Agent trajectory evaluation
- [ ] Tool-call accuracy
- [ ] Prompt regression tests
- [ ] Model regression tests
- [ ] Online evaluation
- [ ] User feedback evaluation
- [x] Evaluation-driven improvement loops *(theory + code: rewrite → hybrid → rerank → pool decisions from hit@5/MRR)*

## Phase 15: AI security and safety

- [ ] Direct prompt injection
- [ ] Indirect prompt injection
- [ ] Sensitive information leakage
- [ ] Insecure output handling
- [ ] Excessive agent permissions
- [ ] Tool authorisation
- [ ] Tenant isolation
- [ ] Vector database access control
- [ ] Secrets management *(partly covered: Gemini key in a git-ignored* `backend/.env`*,* `.env.example`*; a leaked key must be revoked)*
- [ ] Sandboxing
- [ ] Network restrictions
- [ ] MCP server trust
- [ ] Tool poisoning
- [ ] Resource exhaustion
- [ ] Rate limits and quotas *(partly covered: Gemini free-tier limits, 429 handling studied)*
- [ ] AI red teaming
- [ ] Data privacy and retention

## Phase 16: Production AI engineering

- [ ] Redis fundamentals
- [ ] Exact-match caching
- [ ] Semantic caching
- [ ] Prompt caching
- [ ] Cache invalidation
- [ ] Model routing
- [ ] Small vs frontier model trade-offs
- [ ] Fallback models
- [ ] Batch inference
- [ ] Token-cost optimisation *(partly covered: token usage and cost metrics studied; rewrite gated to cut Gemini calls)*
- [ ] Latency optimisation *(partly covered: measured retrieve latency in* `eval_baseline` *~26 ms labelled warm; not optimised yet)*
- [ ] Rate limiting
- [x] Retries and timeouts *(theory + code: Gemini client 15 s timeout, 2 attempts, retry 408/5xx not 429 in* `llm_client`*)*
- [ ] Circuit breakers
- [ ] Background jobs and queues
- [ ] Logging, metrics, and tracing *(partly covered: controller* `logger.exception`*; no metrics/tracing stack)*
- [ ] Prompt and model versioning *(partly covered:* `GEMINI_MODEL` *in* `.env`*; prompts are code constants, not versioned)*
- [ ] Docker
- [ ] CI/CD
- [ ] Deployment
- [ ] Load and concurrency testing
- [ ] Scalability and availability
- [ ] Data lineage and provenance
- [ ] Data freshness
- [ ] Incremental indexing
- [ ] Production monitoring *(partly covered: monitored team backend and frontend deployments)*

## Phase 17: Multimodal AI

- [ ] Multimodal model architecture
- [ ] Vision-language models
- [ ] Image understanding
- [ ] Image embeddings
- [ ] Audio input and processing
- [ ] Speech-to-text
- [ ] Text-to-speech
- [ ] Real-time audio interaction
- [ ] Video understanding
- [ ] Multimodal RAG
- [ ] Multimodal agent workflows

## Phase 18: Advanced model engineering

- [ ] Fine-tuning decision criteria
- [ ] Dataset preparation
- [ ] Supervised fine-tuning
- [ ] LoRA and QLoRA
- [ ] Model evaluation before and after fine-tuning
- [ ] Quantisation
- [ ] Inference optimisation
- [ ] Small language models
- [ ] Model serving
- [ ] GPU and memory fundamentals
- [ ] Batch and streaming inference

## Phase 19: AI system design and interviews

- [ ] Design a RAG document assistant *(in progress: building it in this project)*
- [ ] Design an enterprise knowledge assistant
- [ ] Design a customer-support agent
- [ ] Design a coding agent
- [ ] Design a multi-agent workflow
- [ ] Design a scalable embedding pipeline
- [ ] Design a vector search system
- [ ] Design an agent runtime
- [ ] Design context and memory infrastructure
- [ ] Design AI evaluation infrastructure
- [ ] Design a production AI API
- [ ] AI system security and failure analysis
- [ ] Python coding interviews
- [ ] SQL and data engineering interviews
- [ ] ML and deep learning fundamentals
- [ ] RAG and agent interviews
- [ ] Project deep dives
- [ ] Architecture and trade-off discussions

## Also covered (not in the roadmap)

Topics already studied that do not have their own item above.

**AI and LLMs**

- [x] AI, AGI, and LLM fundamentals
- [x] RLHF (reinforcement learning from human feedback)
- [x] Static vs contextual embeddings
- [x] Sparse vs dense vectors
- [x] Scaled dot-product and masked multi-head attention
- [x] Residual connections, layer normalisation, and feed-forward layers in transformers

**Document processing and chunking**

- [x] Text preprocessing for RAG: whitespace, newlines, Unicode normalisation, empty pages, structure preservation ([notes](text-preprocessing.md))
- [x] PyMuPDF document structure: blocks, lines, and spans
- [x] Font-size distribution analysis to find heading styles
- [x] Chunking strategies: fixed-size, overlapping, structure-aware, recursive, semantic (propositions), sliding-window, parent-child
- [x] Chunk metadata and how to use it

**Vector databases**

- [x] Semantic search vs distance metrics: the metric (cosine, dot product, L2, Manhattan) is only the ruler for "closest"; Chroma offers cosine, L2 and inner product; with length-1 vectors the first three rank identically
- [x] Chroma on-disk storage: SQLite metadata segment (IDs, text, metadata as one row per field), HNSW vector segment (`.bin` files), and the write log of upserts and deletes, explored in DB Browser for SQLite

**Evaluation**

- [x] Hallucination fundamentals
- [x] RAG A/B testing metrics: context precision, semantic answer similarity (SAS), context density, context window utilisation, latency inflation, token usage and cost

**Testing**

- [x] Testing code that uses a database: a temporary Chroma folder per test (`tmp_path`, `monkeypatch`, clearing the `lru_cache`), so tests never touch `backend/data/chroma`
- [x] Proving a test can fail: break the protected line on purpose (the delete in `add_chunk_to_db`), watch the test fail, restore it

**Related engineering work**

- [x] Frontend and backend architecture and end-to-end data flow (frontend, backend, AI model, response)
- [x] Database branching
- [x] NestJS syntax and service relationships, compared with Java
- [x] Frontend upload integration and document preview (original PDF and extracted text)

---

# Part 2: Development map

The order to work in. Follow it while working through Part 1.

## 1. Document processing and chunking

**Study**

- [x] Document parsing
- [x] PDF extraction
- [x] Spans and metadata
- [x] Section detection
- [x] Chunking strategies
- [x] Chunk size and overlap
- [ ] Character-based vs token-based splitting *(partly covered: both studied separately; compare chunk sizes in characters vs tokens next)*
- [x] Structure-aware chunking

**Build**

- [x] Extract text from PDFs
- [x] Extract spans and font metadata
- [x] Identify headings
- [x] Build document sections
- [x] Split sections into chunks using LangChain
- [x] Preserve heading and page metadata
- [x] Keep line breaks in section text for paragraph- and line-level splitting
- [x] Write chunking tests
- [x] Test with real PDFs
- [x] Integrate chunking into the upload pipeline

**Expected output:** A PDF upload produces clean, structured chunks with metadata.

## 2. Embedding generation

**Study**

- [x] What embeddings are
- [x] How embedding models convert text into vectors
- [x] Embedding dimensions
- [x] Similarity and distance
- [x] Cosine similarity
- [x] Dot product
- [x] Euclidean distance
- [x] Normalisation
- [ ] Embedding model selection
- [x] Token limits and batch processing

**Build**

- [x] Select an embedding model
- [x] Generate embeddings for each document chunk
- [x] Inspect vector dimensions
- [x] Generate an embedding for a sample query
- [x] Compare query and chunk similarity
- [ ] Handle API errors and batching

**Expected output:** Every document chunk has an embedding vector.

## 3. Vector database

**Study**

- [x] Why vector databases exist
- [x] Vector storage and retrieval
- [x] Collections and indexes
- [x] Similarity search
- [x] Approximate nearest neighbour search
- [ ] HNSW and IVF *(partly covered: HNSW studied, IVF not yet)*
- [x] Metadata filtering
- [x] Persistence
- [ ] Vector database trade-offs

**Build**

- [x] Select a vector database
- [x] Understand its collection and index structure
- [x] Define a chunk storage schema
- [x] Store embeddings, text, and metadata
- [x] Retrieve vectors using query embeddings
- [x] Filter by document ID and metadata
- [x] Test persistence and deletion

**Expected output:** Document chunks and their embeddings are stored and searchable.

## 4. Retrieval pipeline

**Study**

- [x] Query embeddings
- [x] Top-K retrieval
- [x] Similarity thresholds
- [x] Metadata filtering
- [x] Retrieval quality
- [x] Retrieval latency *(theory + code:* `eval_baseline` *timings; Part E — load vs labelled vs rewrite)*

**Build**

- [x] Accept a user query
- [x] Generate its embedding
- [x] Search the vector database
- [x] Retrieve the top-K chunks
- [x] Apply metadata filters
- [x] Return chunks and similarity scores
- [x] Test relevant and irrelevant queries

**Expected output:** A user query retrieves relevant document passages.

## 5. RAG generation

**Study**

- [x] RAG architecture
- [x] LLM APIs
- [x] System and user prompts
- [x] Context injection
- [x] Structured outputs
- [x] Grounded generation
- [x] Hallucinations
- [x] Citations
- [ ] Pydantic models and dependency injection in FastAPI *(added)*

**Build**

- [x] Accept a user question
- [x] Retrieve relevant chunks
- [x] Construct context from the retrieved chunks
- [x] Build the LLM prompt
- [x] Call the model
- [x] Generate an answer using retrieved evidence
- [x] Return citations and source metadata
- [x] Handle insufficient evidence
- [x] Define Pydantic request and response models for the question API *(added)*
- [x] Add automated API tests for upload and question endpoints *(added)* *(*`/search` *+* `test_ask_service.py` *including* `LLMError` *→ 503)*

**Expected output:** A working document question-answering API.

## 6. Advanced RAG

**Study**

- [x] Dense retrieval *(theory + code: MiniLM + Chroma)*
- [x] Sparse retrieval and BM25 *(theory + code:* `bm25_search` *+ test + smoke)*
- [x] Hybrid search *(theory + code: wired into* `search_documents`*)*
- [x] Reciprocal rank fusion *(theory + code: helper + unit test + wire)*
- [x] Reranking *(theory + code: cross-encoder after gate in* `search_documents`*)*
- [x] Query rewriting *(theory + code: gated LLM rewrite; keep with hybrid gate)*
- [ ] Query decomposition *(partly covered: studied; not in code yet)*
- [ ] Parent-child retrieval *(partly covered: parent-child chunking studied)*
- [ ] Multi-query retrieval *(partly covered: studied; not in code yet)*
- [ ] Graph RAG
- [x] Retrieval evaluation *(theory + code: eval baseline script)*

**Build**

- [x] Create an evaluation dataset *(labelled* `CASES` *in* `scripts/eval_baseline.py`*)*
- [x] Measure baseline retrieval quality *(hit@5 8/8, MRR 0.73 after hybrid+rerank; was 0.69 hybrid-only / 7/8 / 0.66 earlier)*
- [x] Implement hybrid retrieval *(dense + BM25 → RRF + gate in* `search_documents`*)*
- [x] Add reranking *(cross-encoder on fused top-k; pool still k=5)*
- [x] Compare results *(hybrid 0.69 vs rerank 0.73 vs pool>k; table in design-notes Part E)*
- [x] Add query rewriting where useful *(gated rewrite + mocks; kept with hybrid)*
- [x] Measure latency and quality *(*`eval_baseline` *timings: ~26 ms labelled warm retrieve; rewrite cases slower; Part E)*

**Expected output:** A RAG system with measurable retrieval quality.

## 7. Prompt engineering and LLM application development

**Study**

- [x] Instruction hierarchy *(system vs user; no separate developer channel — matches Phase 8)*
- [x] Prompt structure *(ask + rewrite prompts)*
- [ ] Few-shot prompting *(partly covered: grounded ask is zero-shot)*
- [x] Prompt templates *(*`GROUNDING_RULES` *+* `SYSTEM_PROMPT` */* `STREAM_SYSTEM_PROMPT`*;* `build_prompt` */* `build_stream_prompt`*; rewrite prompt separate)*
- [x] Output constraints *(found/citations rules +* `LLMResponse`*)*
- [x] Structured outputs
- [ ] Function calling
- [ ] Tool calling
- [ ] Streaming *(in progress:* `stream_answer` *+ stream prompts; no SSE route/UI yet — 2026-11-20)*
- [ ] Model selection and fallback *(partly covered:* `GEMINI_MODEL` *in* `.env` *only)*

**Build**

- [x] Create reusable prompt templates *(ask + rewrite + stream twin; shared* `GROUNDING_RULES`*)*
- [x] Enforce structured outputs *(*`response_schema=LLMResponse` *in* `generate_answer`*)*
- [ ] Add streaming responses *(in progress:* `stream_answer` *+* `_citations_from_answer`*; events/route/UI open)*
- [ ] Add tool calling
- [ ] Validate model outputs *(partly covered: schema check and citation range check in* `ask_question`*; stream cite helper ready)*
- [ ] Add prompt regression tests *(partly covered:* `test_prompt_builder.py`*)*
- [ ] Compare model behaviour across tasks

**Expected output:** A reusable and reliable LLM interaction layer.

## 8. Context engineering and memory

**Study**

- [ ] Context windows
- [ ] Token budgets
- [ ] Context selection
- [ ] Context prioritisation
- [ ] Context relevance and freshness
- [ ] Context compression
- [ ] Context summarisation
- [ ] Context compaction
- [ ] Context rot
- [ ] Conversation history
- [ ] Short-term and long-term memory
- [ ] Episodic, semantic, and procedural memory

**Build**

- [ ] Create a context builder
- [ ] Define a token budget
- [ ] Prioritise instructions and relevant evidence
- [ ] Include conversation history selectively
- [ ] Compress older context
- [ ] Retrieve relevant memory
- [ ] Track context usage
- [ ] Test long conversations

**Expected output:** A context-management layer that controls what the model receives.

## 9. First AI agent

**Study**

- [ ] LLM calls vs agents
- [ ] Agent architecture
- [ ] Agent loops
- [ ] Planning
- [ ] Task decomposition
- [ ] Tool selection
- [ ] Tool schemas
- [ ] State
- [ ] Memory
- [ ] Reflection
- [ ] Termination
- [ ] Retry and recovery

**Build**

- [ ] Define a bounded task
- [ ] Give the agent two or three tools
- [ ] Implement the observe → decide → act → inspect loop
- [ ] Add state
- [ ] Validate tool results
- [ ] Add iteration and token limits
- [ ] Add termination conditions
- [ ] Test tool failures

**Expected output:** A single agent that completes a bounded task reliably.

## 10. Agent frameworks and workflows

**Study**

- [ ] LangChain
- [ ] LCEL
- [ ] LangGraph
- [ ] Graph state
- [ ] Nodes and edges
- [ ] Conditional routing
- [ ] Checkpointing
- [ ] Persistence
- [ ] Human-in-the-loop
- [ ] MCP architecture *(partly covered: studied in October, not retained; revisit in Phase 11)*
- [ ] MCP clients and servers *(partly covered: MCP server architecture studied)*

**Build**

- [ ] Rebuild the simple agent using LangGraph
- [ ] Add conditional paths
- [ ] Add persistent state
- [ ] Add checkpoints
- [ ] Add human approval
- [ ] Expose a tool through MCP
- [ ] Connect the MCP client to the agent
- [ ] Compare framework and custom implementations

**Expected output:** A stateful agent workflow with external tools.

## 11. Harness engineering

**Study**

- [ ] Agent runtime architecture
- [ ] Model and tool boundaries
- [ ] Execution environments
- [ ] Permissions
- [ ] Sandboxing
- [ ] Context loading and compaction
- [ ] Tool-result validation
- [ ] Checkpoints
- [ ] Resumability
- [ ] Idempotency
- [ ] Parallel execution
- [ ] Concurrency
- [ ] Budgets
- [ ] Timeouts
- [ ] Recovery
- [ ] Tracing

**Build**

- [ ] Create an agent runtime
- [ ] Add tool permission checks
- [ ] Add execution budgets
- [ ] Add checkpoints and resumability
- [ ] Make external actions idempotent where possible
- [ ] Add bounded parallel tool execution
- [ ] Add cancellation and timeout handling
- [ ] Trace every agent step

**Expected output:** A controlled agent runtime, not just an LLM loop.

## 12. Agentic software development

**Study**

- [ ] Coding-agent architecture
- [ ] Repository context retrieval
- [ ] Codebase indexing
- [ ] Planning code changes
- [ ] Task decomposition
- [ ] Code execution
- [ ] Test-feedback loops
- [ ] Automated debugging
- [ ] Git integration
- [ ] Sandboxed execution
- [ ] Approval workflows

**Build**

- [ ] Create a repository-aware coding assistant
- [ ] Let it search code
- [ ] Let it propose a plan
- [ ] Let it modify code in a controlled environment
- [ ] Run tests
- [ ] Feed failures back into the agent
- [ ] Require approval for risky changes
- [ ] Evaluate task success

**Expected output:** A constrained coding agent that can inspect, change, and test a codebase.

## 13. Evaluation and security

**Study**

- [ ] Evaluation datasets
- [x] Retrieval metrics
- [ ] Answer correctness
- [x] Groundedness
- [ ] Hallucination evaluation *(partly covered: hallucination fundamentals studied)*
- [ ] Agent trajectory evaluation
- [ ] Tool-call accuracy
- [ ] Prompt injection
- [ ] Data leakage
- [ ] Tool permissions
- [ ] Tenant isolation
- [ ] Red teaming

**Build**

- [ ] Create evaluation datasets
- [ ] Automate test runs
- [ ] Evaluate answer correctness
- [ ] Evaluate retrieval quality
- [ ] Evaluate tool-call accuracy
- [ ] Test prompt injection
- [ ] Test access control
- [ ] Record regressions

**Expected output:** Evidence that your AI system is reliable and secure.

## 14. Production AI engineering

**Study**

- [ ] Redis
- [ ] Exact-match caching
- [ ] Semantic caching
- [ ] Prompt caching
- [ ] Model routing
- [ ] Fallback models
- [ ] Rate limiting
- [ ] Retries
- [ ] Circuit breakers
- [ ] Background jobs and queues
- [ ] Logging, metrics, and traces
- [ ] Docker
- [ ] CI/CD
- [ ] Load testing
- [ ] Scalability
- [ ] Data lineage
- [ ] Data freshness
- [ ] Incremental indexing

**Build**

- [ ] Add Redis caching
- [ ] Add rate limits
- [ ] Add background document ingestion
- [ ] Add retries and timeouts
- [ ] Add model fallback
- [ ] Add observability
- [ ] Add authentication and authorisation *(added)*
- [ ] Persist documents and chunk records in a database *(added)*
- [ ] Containerise the application
- [ ] Deploy it
- [ ] Load-test it
- [ ] Measure latency and cost

**Expected output:** A deployed AI application with operational controls.

## 15. Advanced AI engineering

Study and implement these after the core RAG and agent systems work.

**Multimodal AI**

- [ ] Study vision-language models
- [ ] Process images
- [ ] Generate image embeddings
- [ ] Process audio
- [ ] Implement speech-to-text and text-to-speech
- [ ] Study video understanding
- [ ] Build multimodal RAG

**Fine-tuning and inference**

- [ ] Study fine-tuning decision criteria
- [ ] Prepare a dataset
- [ ] Implement supervised fine-tuning
- [ ] Study LoRA and QLoRA
- [ ] Evaluate the fine-tuned model
- [ ] Study quantisation
- [ ] Optimise inference
- [ ] Study model serving

**Advanced agent systems**

- [ ] Study knowledge graphs
- [ ] Implement graph-based retrieval
- [ ] Study multi-agent coordination
- [ ] Build a multi-agent workflow
- [ ] Study computer-use agents
- [ ] Build a controlled computer-use workflow

**Expected output:** Advanced AI systems that extend your core portfolio.

## Parallel study track

Do these alongside the development map:

- Advanced Python during backend development
- ML and deep learning fundamentals during embedding and LLM study
- SQL and database design during persistence work
- System design during every architecture decision
- AI security from RAG onwards
- AI evaluation from retrieval onwards
- Interview preparation every week: for each topic ticked this week, answer one interview question about it out loud
- Relevant research papers and engineering articles as needed

---

# Progress log

Newest first. Each monthly update adds an entry here and updates the checkboxes, the summary table, and the "Now" section.

## 2026-11-20 (daily update)

**Built / measured:** Locked stream design (plain-text tokens + sources on `done`; twin `POST /answer/stream` SSE; keep JSON `/answer`). `prompt_builder`: `GROUNDING_RULES`, `SYSTEM_PROMPT`, `STREAM_SYSTEM_PROMPT`, `_user_prompt`, `build_stream_prompt` (docs wording, not company-only). `llm_client.stream_answer` via `generate_content_stream` (yield text; no JSON schema). `ask_service._citations_from_answer` for `[n]` → sources. Prompt tests still green. **Not yet:** `ask_question_events`, SSE route, frontend stream consumer, design-notes/pipeline stream section. **Marked done:** none new (streaming stays in progress). **Totals:** Done **95** / Partly **30**. **Next:** events generator → `/answer/stream` → chat. **End only:** `git init`.

## 2026-11-19 (daily update)

**Built / measured:** `retrieval/rerank.py` + CrossEncoder default; eval **8/8 / 0.73**; pool spike tried and reverted. Frontend: `askQuestion` / `useChat` → `/answer` with upload `document_id`; sources + citation UI; panel width/height. Docs: Part E pool note, **Part G**, pipeline **§13.5**. Afternoon: `eval_baseline` latency (handbook `document_id`; labelled warm ~**26 ms**; first load ~2.9 s); compare table in Part E. Noted: “summarize this document” fails gate (meta query). **Marked done:** Phase 7 metadata-aware + trade-offs; step 4 retrieval latency; step 6 compare/latency; frontend `/answer` + sources + doc scope; Phase 3 encoder vs decoder. **Roadmap audit (same day):** ticked API error contracts; real-PDF chunk inspection; document replace-by-id; prompt hierarchy/templates/constraints/JSON schema; eval `CASES` dataset + improvement loops; Gemini retries/timeouts. Refreshed partly notes (embed model pick, Chroma choice, zero-shot/role, testing strategy, logging/config). **Totals:** Done **95** / Partly **30**. **Next:** Part 2 step 7 (prompts track still has streaming/tools open). **Still todo:** leftover better-retrieval, memory, agents, rest of Part 2. **End only:** `git init`.

## 2026-11-18 (daily update)

**Built / measured:** `tests/test_rrf.py`; wired `_hybrid_once` (dense + BM25 → RRF) into `search_documents` with `MIN_SCORE` / `WEAK_DENSE_FLOOR` / post-rewrite dense-only gate; `chunk_id` on `SearchResult`; gate tests mock `_hybrid_once`. Eval hit@5 **8/8**, MRR **0.69** (Tue 7/8 / 0.66); leaves → PTO@5; France/cake `[]`. Suite **67** passed. Docs: design-notes, pipeline stage 12, interview bank A14/A15 + Scenario 4. Study-queue rolled git to Thu. **Marked done:** hybrid search; RRF. **Next:** `git init` → cross-encoder rerank. **Not yet in the code:** cross-encoder, ACL, `git init`.

## 2026-11-17 (daily update)

**Built / measured:** gated query rewrite end to end (`rewrite_userQuery` / `rewrite_query`, weak-only gate, prompt tune); 3 offline gate tests; eval via gated `search_documents` — hit@5 7/8, MRR 0.66, leaves still miss. Afternoon: `rank-bm25` + `bm25_search` + `tests/test_bm25.py`; `scripts/smoke_bm25.py` on 100 Chroma chunks (leaves → PTO at BM25 rank 4); `reciprocal_rank_fusion` in `rrf.py` (no unit test yet); comment-style rule; `.gitignore` extended for local notes. Suite 66 passed after BM25 test. **Marked done:** query rewriting; sparse/BM25. **In progress:** RRF (helper built). **Next:** RRF unit test → wire hybrid into search → re-eval leaves. **Not yet in the code:** hybrid in `search_documents`, cross-encoder, `git init`. **Also:** interview bank unchanged (not in daily must-do).

## 2026-11-16 (daily update)

**Built / measured:** finished `/ask` tests (6 offline, full suite 62 passed); `scripts/eval_baseline.py` (labelled cases expanded; hit@5 7/8, MRR 0.66); leaves still miss @ ~0.152. **Studied:** hybrid/BM25/RRF, query rewriting, bi-encoder vs cross-encoder. **Decision (task 17):** document-agnostic LLM rewrite first (only when search is weak), then hybrid+RRF; metric in design notes Part E. **Started:** `services/retrieval/` package; `REWRITE_SYSTEM_PROMPT` + empty `rewrite_query` body. **Also:** `docs/interview-qa-bank.md` created (2 cards); backfill of earlier topics still queued. **Not yet in the code:** working rewrite, search gate, BM25, RRF, cross-encoder. **Policy:** `[x]` only when theory **and** code exist; Phase 7 study-only ticks reverted to partly covered (done remain: dense retrieval, retrieval evaluation).

## 2026-11-13 (daily update)

**Afternoon:** topic 26 (mocking external calls) passed with a correction (patch where the name is used: `ask_service.generate_answer`, not `llm_client.generate_answer`); chose `mock.patch.object(..., autospec=True)` over `monkeypatch` because it records calls (`assert_not_called()` proves "not found" costs no quota) and rejects calls that do not match the real signature. `tests/test_ask_service.py`: test 1 (found answer → one cited source, Resignation p. 32; search and Gemini each called once) passes offline in 0.15 s. Marked done: advanced pytest, fixtures, and mocking (Phase 0).

**Marked done:** grounded answer generation, source attribution and citations, handling insufficient context, end-to-end RAG API (Phase 6); Part 2 step 5 study: grounded generation, citations; step 5 build: accept a question, retrieve, call the model, answer from retrieved evidence, return citations and source metadata, handle insufficient evidence, Pydantic request and response models; step 7 build: enforce structured outputs.

**Marked partly covered:** JSON schema validation (Phase 8); validate model outputs (step 7).

**Built:** `POST /ask` end to end: `generation/llm_client.py` (`generate_answer`: Gemini `gemini-3.5-flash-lite` from `.env`, temperature 0.3, 500 output tokens, 15 s × 2 attempts without retrying 429, client created on first use, JSON `LLMResponse` `found`/`answer`/`citations`, `LLMError` for API errors, no reply, or a reply that does not match); `SYSTEM_PROMPT` "set found to false" rule (test 3 updated); `schemas/ask_schema.py`; `services/ask_service.py` (three "not found" paths, citation range and repeat check, sources from `chunks[n - 1]`); controller (`LLMError` → 503) and route. Swagger UI: notice period → "two weeks", Resignation p. 32; France and "pet dog" → "not found". Full suite 56 passed.

**Findings:** `gemini-2.5-flash-lite` returned 404 "no longer available to new users" although listed; JSON mode dropped the `[ two weeks ]` placeholder brackets; running from the project root did not find `.env` until `load_dotenv` got the full path.

**Not yet in the code:** the remaining tests for `ask_question` and `POST /ask` (task 15: tests 2–5 and the 503 API test).

## 2026-11-12 (daily update)

**Marked done:** temperature, top-p, and sampling (Phase 3); structured output generation (Phase 8); Part 2 step 5 study: LLM APIs, structured outputs. All four passed with corrections (timeout handling, temperature 0 to 0.3, a leaked key must be revoked, a safety block is an error, not "not found").

**Marked partly covered:** secrets management, rate limits and quotas (Phase 15); retries and timeouts (Phase 16).

**Set up:** Gemini free tier: key in git-ignored `backend/.env`, `backend/.env.example`, `google-genai` and `python-dotenv` in `pyproject.toml`; free tier and no billing account confirmed in AI Studio. Started `generation/llm_client.py` (settings and `LLMError`; model `gemini-2.5-flash-lite` from the environment; 15 s timeout × 2 attempts, no retry on 429). Finding: the project is not a git repository.

**Revised:** `generation/prompt_builder.py` and `tests/test_prompt_builder.py`; each of the 4 tests explained in one sentence. Concepts explained: grounded generation vs RAG vs citations; a prompt asks, code enforces (output checks, structured output, no tools for the LLM); why "reply exactly" lets code detect "not found" with `==`; pytest FAILED (exception in the test) vs ERROR (exception in setup).

**Design change:** prompt label is `[n] Heading` without pages; pages come from chunk metadata only. Test 1 asserts `"(pages" not in user_prompt`, checked by hand mutation (old label back, test failed). Full suite 56 passed.

**Not yet in the code:** `generate_answer` (Gemini), `POST /ask`, citation checking, mocked-LLM tests.

## 2026-11-11 (daily update)

**Marked done:** context-window limits; context construction; prompt construction for RAG; Part 2 step 4: test relevant and irrelevant queries (`tests/test_search_api.py`: 422 for `k: "five"`, `k: 0` and an empty question, response shape on an empty temp store); Part 2 step 5 study: system and user prompts, context injection; step 5 build: construct context, build the LLM prompt (`generation/prompt_builder.py`: `SYSTEM_PROMPT` with grounding, citation, placeholder, injection and "not found" rules, `format_chunks` numbering passages with heading and pages, `build_prompt` refusing empty context; `tests/test_prompt_builder.py`, 4 tests). Full suite 56 passed; real `backend/data/chroma` untouched by tests (fixture moved to `tests/conftest.py`).

**Marked partly covered:** grounded answer generation and citations (rules and labels, no LLM call or citation check yet); instruction hierarchy, prompt templates and prompt injection awareness (Phase 8); integration and API testing (`/search` automated); question/upload API tests.

**Finding:** "How many leaves can I take?" scores at most 0.152 against the handbook, so a common phrasing returns "not found" (vocabulary mismatch).

**Not yet in the code:** `generate_answer` (Gemini), `POST /ask`, citation checking, mocked-LLM tests.

**Unticked:** MCP architecture (Phase 11 and Part 2 step 9 study), ticked from the October summary but could not be explained when checked; now partly covered, revisit in Phase 11.

## 2026-11-10 (daily update)

**Marked done (afternoon):** Pydantic models and validation; ingestion-to-retrieval pipeline; retrieval failure analysis; Part 2 step 3: test persistence and deletion (`test_chunks_survive_reopening` clears both the `get_collection` cache and Chroma's shared system cache, and fails with `EphemeralClient`); Part 2 step 4: accept a user query, search the vector database, retrieve the top-K chunks, apply metadata filters, return chunks and scores, retrieval quality. Verified: `POST /search` (`schemas/search_schema.py`, `routes/search_documents_route.py`, `controller/search_documents_controller.py`, `services/search_documents_service.py`) returns ranked chunks in Swagger UI, 422 for invalid input, `[]` for unrelated questions; 11-question check: hit rate 8/8 at k=5, MRR 0.84, `MIN_SCORE` = 0.25; full suite 48 passed.

**Marked partly covered (afternoon):** reranking models (top-K plus reranker flow); test relevant and irrelevant queries (manual, not automated).

**Not yet in the code:** automated `/search` endpoint tests; step 5 (prompt builder, Gemini call, `POST /ask`).

**Marked done (morning):** top-K retrieval and similarity thresholds (Phase 6 and Part 2 step 4 study), explained with real handbook scores: "annual leave" put the PTO chunk at rank 4, so `k=1` returns the wrong chunk; unrelated questions score below 0.1 vs 0.38 to 0.76 for real ones, so a minimum score returns `[]`. Part 2 step 4 study: query embeddings and metadata filtering (already done in Phase 6).

**Marked partly covered:** Pydantic models and validation (studied, not in the code); temperature, top-p, and sampling (top-K sampling vs top-K retrieval); handling insufficient context (design only); retrieval failure analysis (readiness questions pending); evaluation dataset creation and retrieval quality (choosing k with hit rate and recall at k).

**Also covered:** semantic search vs distance metrics (cosine, dot product, L2, Manhattan); with length-1 vectors cosine, dot product and L2 give the same ranking.

**Not yet in the code** (listed under "Now"): `schemas/search_schema.py`, `POST /search` endpoint, minimum score, persistence test.

## 2026-11-09 (daily update)

**Studied:** hands-on Chroma storage review: write-ahead log sequence IDs, typed metadata rows, HNSW neighbour links (16 per upper layer, 32 at layer 0) and `data_level0.bin` size, and how a query reaches the closest vectors through the HNSW index.

**Marked done:** Part 2 step 3: store embeddings, text, and metadata; retrieve vectors using query embeddings; filter by document ID. Verified by `tests/test_vector_store.py` (4 tests: empty store, store and search ranking, re-upload with fewer chunks leaves no stale chunk, deleting one document leaves another); full suite 47 passed; the real `backend/data/chroma` was unchanged by the test run.

**Marked partly covered:** test persistence and deletion (deletion tested, persistence after reopening not yet); advanced pytest (custom fixtures, `monkeypatch`).

**Also covered:** testing code that uses a database (queue topic 17); proving a test can fail by temporarily breaking the code; document identity (`document_id` is the file name, so a renamed file is stored as a new document).

**Not yet in the code** (listed under "Now"): `POST /search` endpoint, minimum similarity score, persistence test.

## 2026-11-06 (daily update)

**Marked done:** vector database architecture (Chroma's METADATA and VECTOR segments, write-ahead log, key-value metadata store, HNSW index file layout); storage reviewed hands-on on 2026-11-09.

**Not yet in the code** (carried to Monday, listed under "Now"): vector store tests, `POST /search` endpoint, minimum similarity score.

## 2026-11-05 (daily update)

**Marked done:** vector dimensions and storage; embedding model changes and re-indexing; Euclidean distance; collections and indexes; vector storage and retrieval; approximate nearest neighbour search; metadata storage and filtering; similarity metrics in vector databases; persistence and deletion; storing chunks, embeddings, and metadata; query embedding; Part 2 step 3: select a vector database (Chroma), its collection and index structure, chunk storage schema.

**Marked partly covered:** embedding versioning (model name in metadata); HNSW and IVF (HNSW only); top-K retrieval and the step 4 search items (`search_chunks` built).

**Not yet in the code** (left unticked, listed under "Now"):

- Vector store tests: there is no `tests/test_vector_store.py`
- `POST /search` endpoint and a minimum similarity score

## October 2026 (monthly update)

**Marked done:** Python OOP, classes, data classes, decorators; transformer and LLM foundations (tokenisation, BPE, one-hot encoding, embedding dimensions, positional encoding, Q/K/V attention, softmax, multi-head attention, transformer architecture, inference); embeddings fundamentals; RAG architecture; MCP architecture; LangChain recursive splitting; text cleaning and normalisation.

**Marked partly covered:** neural network fundamentals, encoder vs decoder, dense and sparse retrieval, MCP clients and servers, API testing (manual Swagger UI testing), token-cost and latency optimisation (metrics studied), production monitoring.

**In the October summary but not yet in the code** (left unticked, listed under "Now"):

- Chunk embeddings with Sentence Transformers: `sentence-transformers` is not installed and there is no embedding code
- Unit tests for splitter size limits, metadata, overlap, heading-only sections, and embedding similarity: not in `tests/`
- Updated loader tests: 2 tests in `tests/test_loader.py` still fail
- Line breaks preserved for paragraph- and line-level splitting: `build_sections` still joins spans with spaces
- `langchain-text-splitters` dependency: misspelled in `pyproject.toml`

**Roadmap changes:** reordered Phase 3 so neural network basics come first; added text cleaning to Phase 2; added Pydantic, API tests, authentication, and database persistence to Part 2 (they were in Part 1 but had no build step); added the "Now" and "How to use this roadmap" sections.

## 2026-10-30: Baseline

Statuses set from the project code (`backend/`), `docs/`, and daily updates up to Oct 29.
