from rag_assistant.services.retrieval.bm25 import bm25_search

def test_bm25_on_given_corpus_returns_expected_results()->None:
    corpus = [
        "Resignation needs two weeks notice",
        "Paid time off (PTO) is twenty days of leave",
        "The office opens at nine",
    ]

    results=bm25_search("how many leave days PTO",corpus=corpus,k=2)

    # other chunks may score 0 and be dropped; the important check is the winner
    assert len(results)>=1
    best_index, best_score = results[0]
    assert best_index==1 # PTO / leave chunk should rank first
    assert best_score > 0
