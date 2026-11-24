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
    )

def test_strong_hit_skips_rewrite()->None:
    chunks=[make_result("Resignation","Give two weeks notice.",32)]

    with (
        mock.patch.object(
            search_documents_service,
            "_hybrid_once",
            autospec=True,
            return_value=(chunks, 0.7, False),
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
            "_hybrid_once",
            autospec=True,
            side_effect=[(weak, 0.15, False), (strong, 0.5, False)],
        ) as fake_hybrid,
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
    assert fake_hybrid.call_count==2
    fake_hybrid.assert_any_call("How many leaves can I take?",5,None)
    fake_hybrid.assert_any_call(rewritten,5,None)

def test_weak_hit_llm_rewrite_failure_returns_empty()->None:
    weak=[make_result("Resignation","Give two weeks notice.",32,score=0.15)]

    with (
        mock.patch.object(
            search_documents_service,
            "_hybrid_once",
            autospec=True,
            return_value=(weak, 0.15, False),
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
