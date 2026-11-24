from collections.abc import Callable
from functools import lru_cache
from sentence_transformers import CrossEncoder
from rag_assistant.storage.vector_store import SearchResult

# score_fn(question, texts) -> one float per text (same order)
ScoreFn = Callable[[str, list[str]], list[float]]

CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L6-v2"


@lru_cache(maxsize=1)  # load once, reuse
def get_cross_encoder() -> CrossEncoder:
    return CrossEncoder(CROSS_ENCODER_MODEL)


def cross_encoder_score(question: str, texts: list[str]) -> list[float]:
    # one joint score per (question, text) pair
    if not texts:
        return []
    model = get_cross_encoder()
    pairs = [(question, text) for text in texts]
    raw = model.predict(pairs)
    return [float(score) for score in raw]


def rerank(
    question: str,
    chunks: list[SearchResult],
    score_fn: ScoreFn | None = None, # no real usage of this , we just keep it for the tests , otherwise we use the real cross encoder which will call the LLM
) -> list[SearchResult]:
    # reorder only; keep dense chunk["score"]
    if not chunks:
        return []
    if score_fn is None:
        score_fn=cross_encoder_score

    texts = [chunk["text"] for chunk in chunks]
    scores = score_fn(question, texts)
    if len(scores) != len(chunks):
        raise ValueError("score_fn must return one float per chunk")

    ranked = list(zip(chunks, scores))
    ranked.sort(key=lambda pair: pair[1], reverse=True)
    return [chunk for chunk, _cross_score in ranked]


# --- scenario---
# question = "How many leaves can I take?"
#
# 1) after hybrid+gate, chunks (RRF order), dense .score already set:
#    [Sick leave (0.31), PTO (0.28), Remote (0.22)]
#
# 2) texts = [chunk["text"] for ...]
#    ["…sick…", "…pto…", "…remote…"]
#
# 3) scores = score_fn(question, texts)   # fake or cross_encoder_score
#    [0.40, 0.95, 0.10]   # same order as texts / chunks
#
# 4) zip → ranked
#    [(Sick, 0.40), (PTO, 0.95), (Remote, 0.10)]
#
# 5) sort by cross score, high first
#    [(PTO, 0.95), (Sick, 0.40), (Remote, 0.10)]
#
# 6) return chunks only (drop cross scores)
#    [PTO, Sick, Remote]
#    dense .score still 0.28, 0.31, 0.22 — never overwritten
#    API "top" = list position, not dense .score
