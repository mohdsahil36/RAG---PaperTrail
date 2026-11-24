import math
import pytest
from rag_assistant.ingestion.chunking import DocumentSection
from rag_assistant.ingestion.embeddings import text_for_embedding,embed_chunks,embed_user_query

def test_heading_and_text_combined():
    chunk:DocumentSection={"heading":"Leave Policy","text": "Employees get 20 days of paid leave.", "page_number": 1, "end_page": 1}

    result=text_for_embedding(chunk)

    assert result == "Leave Policy\nEmployees get 20 days of paid leave."  # heading, a new line, then the text

def test_no_heading():
    chunk:DocumentSection={"heading":None,"text": "Employees get 20 days of paid leave.", "page_number": 1, "end_page": 1}

    result=text_for_embedding(chunk)

    assert result =="Employees get 20 days of paid leave."

def test_embed_chunks():
    chunk1:DocumentSection={"heading":"Leave Policy","text": "Employees get 20 days of paid leave.", "page_number": 1, "end_page": 1}
    chunk2:DocumentSection={"heading": "Office Hours", "text": "The office opens at 9 am.", "page_number": 2, "end_page": 2}

    chunks=[chunk1,chunk2]

    result=embed_chunks(chunks)

    assert len(result)==2
    for chunk,embedding_result in zip(chunks,result):
        assert len(embedding_result["embedding"])==384
        assert embedding_result["heading"]==chunk["heading"]
        assert embedding_result["text"]==chunk["text"]
        assert embedding_result["page_number"]==chunk["page_number"]
        assert embedding_result["end_page"]==chunk["end_page"]

def test_normalized_embedding():
        # Why: search treats the dot product as cosine similarity , which is only true when every vector has length 1
        # if normalize_embeddings=True is ever removed , nothing crashes but every similarity score becomes wrong , this test catches that
        chunk:DocumentSection={"heading":"Leave Policy","text": "Employees get 20 days of paid leave.", "page_number": 1, "end_page": 1}

        result=embed_chunks([chunk])
        vector=result[0]["embedding"]

        # Formula: length = sqrt(x1² + x2² + ... + x384²) , square every number , add them up , take the square root
        total=0
        for value in vector:
            total+=value*value
        length=math.sqrt(total)

        # pytest.approx allows tiny rounding errors (e.g. 0.99999994) , an exact == 1.0 could fail on them
        assert length==pytest.approx(1.0)

def test_chunk_scores():
    # test to capture that if the query relates to the chunk , then its score is higher than the others
    chunk1:DocumentSection={"heading":"Leave Policy","text": "Employees get 20 days of paid leave.", "page_number": 1, "end_page": 1}
    chunk2:DocumentSection={"heading": "Office Hours", "text": "The office opens at 9 am.", "page_number": 2, "end_page": 2}

    chunks=[chunk1,chunk2]

    result=embed_chunks(chunks)

    assert len(result)==2
    leave_vector=result[0]["embedding"]
    office_vector=result[1]["embedding"]

    question_vector=embed_user_query("How many leave days do I get?")
    leave_score=0
    office_score=0
    for a,b in zip(leave_vector,question_vector):
        leave_score+=a*b
    for c,d in zip(office_vector,question_vector):
        office_score+=c*d

    assert leave_score>office_score

def test_empty_input():
    assert embed_chunks([])==[]