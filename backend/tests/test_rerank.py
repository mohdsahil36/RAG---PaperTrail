from rag_assistant.services.retrieval.rerank import rerank
from rag_assistant.storage.vector_store import SearchResult

def _chunk(heading: str, text: str, score: float, chunk_id: str = "c1") -> SearchResult:
    return SearchResult(
        text=text,
        heading=heading,
        page_number=1,
        end_page=1,
        document_id="handbook.pdf",
        score=score,
        chunk_id=chunk_id,
    )

def test_rerank_empty_returns_empty():
    question="How many leaves I can take?"
    chunks=[]
    result=rerank(question=question, chunks=chunks, score_fn=None)

    assert result ==[]

def test_rerank_reorders_by_score_fn() -> None:
    question = "How many leaves I can take?"
    chunks = [
        _chunk(heading="Sick Leave", text="You can take up to 10 sick leaves per year.", score=0.31, chunk_id="c1"),
        _chunk(heading="PTO", text="You can take up to 10 PTO days per year.", score=0.28, chunk_id="c2"),
        _chunk(heading="Remote Work", text="You can work remotely for up to 10 days per year.", score=0.22, chunk_id="c3"),
    ]
    score_fn = lambda q, texts: [0.40, 0.95, 0.10]

    results = rerank(question=question, chunks=chunks, score_fn=score_fn)

    # fake scores: Sick 0.40, PTO 0.95, Remote 0.10 → order PTO, Sick, Remote
    assert [chunk["heading"] for chunk in results] == ["PTO", "Sick Leave", "Remote Work"]

def test_rerank_keeps_dense_score()->None:
    question = "How many leaves I can take?"
    chunks = [
        _chunk(heading="Sick Leave", text="You can take up to 10 sick leaves per year.", score=0.31, chunk_id="c1"),
        _chunk(heading="PTO", text="You can take up to 10 PTO days per year.", score=0.28, chunk_id="c2"),
        _chunk(heading="Remote Work", text="You can work remotely for up to 10 days per year.", score=0.22, chunk_id="c3"),
    ]
    score_fn = lambda q, texts: [0.40, 0.95, 0.10]

    results = rerank(question=question, chunks=chunks, score_fn=score_fn)

    assert [chunk["score"] for chunk in results]==[0.28,0.31,0.22]