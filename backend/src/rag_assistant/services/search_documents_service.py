import chromadb
from typing import cast
from rag_assistant.storage.vector_store import SearchResult, search_chunks, get_collection
from rag_assistant.services.retrieval.query_rewrite import rewrite_query
from rag_assistant.services.retrieval.bm25 import bm25_search
from rag_assistant.services.retrieval.rrf import reciprocal_rank_fusion
from rag_assistant.services.retrieval.rerank import rerank
from rag_assistant.generation.llm_client import expand_userQuery,break_userQuery

MIN_SCORE=0.25 # if dense score is this or more we can directly return the results
WEAK_DENSE_FLOOR=0.12 # less than MIN_SCORE but BM25 can help us find the relevant chunk

def _multi_query_search(question:str, k:int, document_id:str | None) -> list[SearchResult]:
    # break the question into sub-questions; run full search_documents per sub-question; merge by chunk_id
    decomposition = break_userQuery(question)
    sub_questions = [question] + decomposition.sub_questions

    seen: dict[str, SearchResult] = {}

    for query in sub_questions:
        chunks, _ = _expand_and_search(query, k, document_id)
        for chunk in chunks:
            if chunk["chunk_id"] not in seen:
                seen[chunk["chunk_id"]] = chunk

    return list(seen.values())


def _expand_and_search(question:str, k:int, document_id:str | None) -> tuple[list[SearchResult], float]:
    # run _hybrid_once on original + each LLM-generated variant; merge by chunk_id (first occurrence wins)
    expansion = expand_userQuery(question)
    queries = expansion.questionVariants

    seen: dict[str, SearchResult] = {}
    best_dense_score = 0.0

    for query in queries:
        chunks, dense_score, _ = _hybrid_once(query, k, document_id)
        if dense_score > best_dense_score:
            best_dense_score = dense_score
        for chunk in chunks:
            if chunk["chunk_id"] not in seen:
                seen[chunk["chunk_id"]] = chunk  # first occurrence = highest ranked

    return list(seen.values()), best_dense_score


def _hybrid_once(question:str,k:int,document_id:str | None)->tuple[list[SearchResult], float, bool]:
    # returns: top-k chunks, best dense score, and whether BM25 may justify returning
    dense_chunks=search_chunks(question,k=k,document_id=document_id) # search by meaning

    best_dense_score=0.0 # highest dense score; used by the gate in search_documents
    dense_chunk_ids:list[str]=[] # ranked ids for RRF
    chunks_by_id:dict[str,SearchResult]={} # lookup: id -> full chunk for later rebuild
    for dense_chunk in dense_chunks:
        if dense_chunk["score"]>best_dense_score:
            best_dense_score=dense_chunk["score"] # keep the best dense score
        dense_chunk_ids.append(dense_chunk["chunk_id"]) # ids for RRF
        chunks_by_id[dense_chunk["chunk_id"]]=dense_chunk # keep real dense scores in the lookup

    collection=get_collection() # open the chunk store
    where: chromadb.Where | None = (
        {"document_id": document_id} if document_id else None
    ) # one file only when the caller asks for it
    raw=collection.get(where=where, include=["documents", "metadatas"])
    corpus_texts=raw["documents"] or [] # all chunk texts for BM25
    corpus_meta=raw["metadatas"] or [] # heading and pages for each chunk
    corpus_ids=raw["ids"] or [] # chroma id per row; same order as texts/meta

    # fill lookup gaps: dense already stored top hits; add the rest with score 0.0
    for row_number, chunk_id in enumerate(corpus_ids):
        if chunk_id in chunks_by_id:
            continue # already stored from dense with a real score
        meta=corpus_meta[row_number] or {}
        chunks_by_id[chunk_id]=SearchResult(
            text=corpus_texts[row_number] or "",
            heading=cast(str, meta.get("heading", "")),
            page_number=cast(int, meta["page_number"]),
            end_page=cast(int, meta["end_page"]),
            document_id=cast(str, meta["document_id"]),
            score=0.0, # not from dense; BM25 may still use this id
            chunk_id=chunk_id,
        )

    bm25_ranked=bm25_search(question, corpus=corpus_texts, k=k) # search by keywords , result is in the format of index and score
    bm25_chunk_ids:list[str]=[]
    best_bm25_score=0.0
    for row_number, bm25_score in bm25_ranked:
        bm25_chunk_ids.append(corpus_ids[row_number]) # row number -> chroma id for RRF
        if bm25_score>best_bm25_score:
            best_bm25_score=bm25_score # keep the best keyword score

    # True = keywords found something
    bm25_had_hits=len(bm25_chunk_ids)>0 and best_bm25_score>0.0
    # True = keywords found something, and dense is at least 0.12, so this hybrid
    # list is worth returning even if dense is under 0.25
    bm25_found=bm25_had_hits and best_dense_score>=WEAK_DENSE_FLOOR

    fused_ranking=reciprocal_rank_fusion([dense_chunk_ids, bm25_chunk_ids]) # one id order from both lists

    final_chunks:list[SearchResult]=[]
    for ranked_pair in fused_ranking:
        chunk_id=ranked_pair[0] # id only; RRF score is not returned to the API
        if chunk_id not in chunks_by_id:
            continue
        final_chunks.append(chunks_by_id[chunk_id]) # full chunk from the lookup
        if len(final_chunks)==k:
            break # only top k

    return final_chunks, best_dense_score, bm25_found


def search_documents(question:str,k:int,document_id:str | None)->list[SearchResult]:
    
    final_chunks = _multi_query_search(question, k, document_id)
    best_dense_score = max((c["score"] for c in final_chunks), default=0.0)

    if best_dense_score>=MIN_SCORE:
        return rerank(question, final_chunks)

    rewritten=rewrite_query(question) # one clearer wording; no second rewrite
    if not rewritten:
        return [] # rewrite failed; nothing safe to return

    final_chunks, best_dense_score, _bm25_found=_hybrid_once(rewritten, k, document_id)
    # after rewrite we ignore bm25_found; only a strong dense score may return
    if best_dense_score>=MIN_SCORE:
        return rerank(rewritten, final_chunks)
    return [] # still weak after rewrite

