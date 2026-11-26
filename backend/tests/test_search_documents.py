from unittest import mock
from rag_assistant.services import search_documents_service
from rag_assistant.storage.vector_store import SearchResult

def make_result(heading:str,text:str,page:int,score:float=0.7)->SearchResult:
    return SearchResult(
        text=text,
        heading=heading,
        page_number=page,
        end_page=page,
        document_id="handbook.pdf",
        score=score,
        chunk_id=f"handbook.pdf--{page}",
        parent_id=""
    )

def test_strong_hit_skips_rewrite()->None:
    chunks=[make_result("Resignation","Give two weeks notice.",32)]

    with (
        mock.patch.object(
            search_documents_service,
            "_multi_query_search",
            autospec=True,
            return_value=chunks,
        ) as fake_hybrid,
        mock.patch.object(search_documents_service,"rewrite_query",autospec=True) as fake_rewrite,
        # lambda question, chunks, score_fn=None: chunks
        # means the same as:
        #   def fake_rerank(question, chunks, score_fn=None):
        #       return chunks
        # search_documents calls rerank(...); we hand chunks back — no CrossEncoder.
        mock.patch.object(
            search_documents_service,
            "rerank",
            autospec=True,
            side_effect=lambda question, chunks, score_fn=None: chunks,
        ),
    ):
        result=search_documents_service.search_documents("What is the notice period?",5,None)

    assert result==chunks
    fake_hybrid.assert_called_once_with("What is the notice period?",5,None)
    fake_rewrite.assert_not_called()

def test_weak_hit_rewrites_and_searches_again()->None:
    weak=[make_result("Resignation","Give two weeks notice.",32,score=0.15)]
    strong=[make_result("Paid time off (PTO)","You get 20 days.",10,score=0.5)]
    rewritten="How many paid time off days do I get?"

    with (
        mock.patch.object(
            search_documents_service,
            "_multi_query_search",
            autospec=True,
            return_value=weak,
        ) as fake_hybrid,
        mock.patch.object(
            search_documents_service,
            "_hybrid_once",
            autospec=True,
            return_value=(strong, 0.5, False),
        ),
        mock.patch.object(
            search_documents_service,
            "rewrite_query",
            autospec=True,
            return_value=rewritten,
        ) as fake_rewrite,
        # same fake rerank as strong-hit test (see comments there)
        mock.patch.object(
            search_documents_service,
            "rerank",
            autospec=True,
            side_effect=lambda question, chunks, score_fn=None: chunks,
        ),
    ):
        result=search_documents_service.search_documents("How many leaves can I take?",5,None)

    assert result==strong
    fake_rewrite.assert_called_once_with("How many leaves can I take?")
    fake_hybrid.assert_called_once_with("How many leaves can I take?",5,None)

def test_weak_hit_llm_rewrite_failure_returns_empty()->None:
    weak=[make_result("Resignation","Give two weeks notice.",32,score=0.15)]

    with (
        mock.patch.object(
            search_documents_service,
            "_multi_query_search",
            autospec=True,
            return_value=weak,
        ) as fake_hybrid,
        mock.patch.object(
            search_documents_service,
            "rewrite_query",
            autospec=True,
            return_value=None,
        ) as fake_rewrite,
    ):
        result=search_documents_service.search_documents("How many leaves can I take?",5,None)

    assert result==[]
    fake_rewrite.assert_called_once_with("How many leaves can I take?")
    fake_hybrid.assert_called_once_with("How many leaves can I take?",5,None)

def test_expand_and_search_deduplicates_across_variants() -> None:
    from rag_assistant.generation.llm_client import RephraseResponse
    variants = RephraseResponse(questionVariants=[
        "How many days of annual leave am I entitled to?",
        "How many paid time off days do I get?",
    ])
    chunk_a = make_result("PTO", "You get 20 days.", 10, score=0.5)
    chunk_b = make_result("Leave", "Annual leave is 20 days.", 11, score=0.4)
    chunk_c = make_result("Holidays", "Public holidays are separate.", 12, score=0.3)

    with (
        mock.patch.object(search_documents_service, "expand_userQuery", autospec=True, return_value=variants),
        mock.patch.object(
            search_documents_service,
            "_hybrid_once",
            autospec=True,
            side_effect=[
                ([chunk_a, chunk_b], 0.5, True),  # variant 1
                ([chunk_b, chunk_c], 0.4, False),  # variant 2 — chunk_b is duplicate
            ],
        ) as fake_hybrid,
    ):
        result, best_score = search_documents_service._expand_and_search("annual leave policy", 5, None)

    assert fake_hybrid.call_count == 2
    result_ids = [r["chunk_id"] for r in result]
    assert len(result_ids) == 3                        # A, B, C — no duplicates
    assert result_ids.count("handbook.pdf--11") == 1   # chunk_b appears once
    assert best_score == 0.5


def test_multi_query_search_deduplicates_across_sub_questions() -> None:
    from rag_assistant.generation.llm_client import DecompositionResponse
    decomposition = DecompositionResponse(sub_questions=[
        "What is the leave policy?",
        "How do I apply for leave?",
    ])
    chunk_a = make_result("PTO", "You get 20 days.", 10, score=0.5)
    chunk_b = make_result("Leave", "Annual leave is 20 days.", 11, score=0.4)
    chunk_c = make_result("Apply", "Submit a request form.", 12, score=0.3)

    with (
        mock.patch.object(search_documents_service, "break_userQuery", autospec=True, return_value=decomposition),
        mock.patch.object(
            search_documents_service,
            "_expand_and_search",
            autospec=True,
            side_effect=[
                ([chunk_a, chunk_b], 0.5),  # original question
                ([chunk_b, chunk_c], 0.4),  # sub-q1 — chunk_b is duplicate
                ([chunk_c], 0.3),           # sub-q2 — chunk_c is duplicate
            ],
        ) as fake_expand,
    ):
        result = search_documents_service._multi_query_search("compound question", 5, None)

    assert fake_expand.call_count == 3
    result_ids = [r["chunk_id"] for r in result]
    assert len(result_ids) == 3                        # A, B, C — no duplicates
    assert result_ids.count("handbook.pdf--11") == 1   # chunk_b appears once
