from rag_assistant.services.retrieval.rrf import reciprocal_rank_fusion

def test_rrf_on_given_rankings()->None:
    rankings=[
        ["A","B","C"],
        ["B","D","A"]
    ]

    result = reciprocal_rank_fusion(rankings)

    assert len(result) == 4
    assert [item_id for item_id, _ in result] == ["B", "A", "D", "C"]
    scores = [score for _, score in result]
    assert all(scores[i] >= scores[i + 1] for i in range(len(scores) - 1))
    assert all(isinstance(score, float) and score > 0 for score in scores)