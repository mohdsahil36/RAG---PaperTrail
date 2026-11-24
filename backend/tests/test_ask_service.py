import json
from unittest import mock
from fastapi.testclient import TestClient
from rag_assistant.generation.llm_client import LLMError, LLMResponse
from rag_assistant.main import app
from rag_assistant.services import ask_service
from rag_assistant.storage.vector_store import SearchResult

client = TestClient(app) # calls the app directly (route, validation, controller) , it does not require the server to be started

def make_result(heading:str,text:str,page:int)->SearchResult:
    return SearchResult(
        text=text,
        heading=heading,
        page_number=page,
        end_page=page,
        document_id="handbook.pdf",
        score=0.7,
        chunk_id=f"handbook.pdf--{page}",
    )

def test_found_answer_returns_cited_source()->None:
    chunks=[make_result("Resignation","Give two weeks notice.",32),
        make_result("Leaving our company","How resignation works.",31)]
    llm_reply=LLMResponse(found=True,answer="Two weeks [1].",citations=[1])

    with (
        mock.patch.object(ask_service,"search_documents",autospec=True,return_value=chunks) as fake_search,
        mock.patch.object(ask_service,"generate_answer",autospec=True,return_value=llm_reply) as fake_llm,
    ):
        result=ask_service.ask_question("What is the notice period?",5)

    assert result.found is True  # the answer was found
    assert len(result.sources)==1 # only the cited passage [1] becomes the source
    assert result.sources[0].heading=="Resignation" # the source is the first chunk 
    assert result.sources[0].page_number==32# the source is the first chunk 
    fake_search.assert_called_once_with(question="What is the notice period?",k=5,document_id=None) #Search was called once with the right args
    fake_llm.assert_called_once() #Gemini was called once

def test_empty_search_skips_gemini()->None:
   with (
        mock.patch.object(ask_service,"search_documents",autospec=True,return_value=[]) as fake_search,
        mock.patch.object(ask_service,"generate_answer",autospec=True) as fake_llm,
    ):
        result=ask_service.ask_question("What is the capital of India?",5)

        assert result.found is False
        assert result.sources==[]
        fake_search.assert_called_once()
        fake_llm.assert_not_called()

def test_llm_not_found_returns_empty_sources()->None:
    chunks=[make_result("Pets","No pets at work.",10)]
    llm_reply=LLMResponse(found=False,answer="",citations=[])
    with (
        mock.patch.object(ask_service,"search_documents",autospec=True,return_value=chunks) as fake_search,
        mock.patch.object(ask_service,"generate_answer",autospec=True,return_value=llm_reply) as fake_llm,
    ):
        result=ask_service.ask_question("Can I bring my pet dog to the office?",5)
    
    assert result.found is False
    assert result.sources==[]
    fake_search.assert_called_once()
    fake_llm.assert_called_once()

def test_invalid_and_duplicate_citations_are_filtered()->None:
    chunks=[make_result("Resignation","Give two weeks notice.",32),
            make_result("Leaving our company","How resignation works.",31)]
    llm_reply=LLMResponse(found=True,answer="Two weeks.",citations=[1,1,7,2])

    with (
        mock.patch.object(ask_service,"search_documents",autospec=True,return_value=chunks) as fake_search,
        mock.patch.object(ask_service,"generate_answer",autospec=True,return_value=llm_reply) as fake_llm,
    ):
        result=ask_service.ask_question("What is the notice period?",5)
        assert result.found is True
        assert len(result.sources)==2 # if we have duplicate citations , we only keep single values of it , if we have any ones which are out of range we ignore them
        assert result.sources[0].heading=="Resignation"
        assert result.sources[1].heading=="Leaving our company"
        fake_llm.assert_called_once()

def test_only_invalid_citations_return_not_found()->None:
    chunks=[make_result("Resignation","Give two weeks notice.",32),
        make_result("Leaving our company","How resignation works.",31)]
    llm_reply=LLMResponse(found=True,answer="Made up.",citations=[9])
    with (
    mock.patch.object(ask_service,"search_documents",autospec=True,return_value=chunks),
    mock.patch.object(ask_service,"generate_answer",autospec=True,return_value=llm_reply),
    ):
        result=ask_service.ask_question("What is the notice period?",5)
        assert result.found is False
        assert result.sources==[]

def test_ask_returns_503_when_llm_fails()->None:
    chunks=[make_result("Resignation","Give two weeks notice.",32)]
    with (
        mock.patch.object(ask_service,"search_documents",autospec=True,return_value=chunks),
        mock.patch.object(ask_service,"generate_answer",autospec=True,side_effect=LLMError("boom")),
    ):
        response=client.post("/answer",json={"question":"What is the notice period?","k":5})

    assert response.status_code==503 # Gemini failed , controller maps LLMError to 503
    assert response.json()["detail"]=="The answer service is not available right now. Try again later."

# --- stream generator tests ---

def _parse_events(gen)->list[dict]:
    # each SSE line is "data: {...}\n\n" — strip prefix and trailing newlines then parse
    return [json.loads(s.removeprefix("data: ").rstrip("\n")) for s in gen]

def test_stream_tokens_and_done_event()->None:
    chunks=[make_result("Resignation","Give two weeks notice.",32)]
    tokens=["Two weeks ","[1]."]
    with (
        mock.patch.object(ask_service,"search_documents",autospec=True,return_value=chunks),
        mock.patch.object(ask_service,"stream_answer",autospec=True,return_value=iter(tokens)),
    ):
        events=_parse_events(ask_service.stream_ask_question_events("What is the notice period?",5))
    token_events=[e for e in events if e["type"]=="token"]
    done_event=events[-1]
    assert len(token_events)==2 # one event per yielded token
    assert token_events[0]["text"]=="Two weeks "
    assert token_events[1]["text"]=="[1]."
    assert done_event["type"]=="done"
    assert done_event["found"] is True
    assert len(done_event["sources"])==1
    assert done_event["sources"][0]["heading"]=="Resignation"

def test_stream_empty_search_yields_done_not_found()->None:
    with (
        mock.patch.object(ask_service,"search_documents",autospec=True,return_value=[]),
        mock.patch.object(ask_service,"stream_answer",autospec=True) as fake_stream,
    ):
        events=_parse_events(ask_service.stream_ask_question_events("Unrelated question",5))
    assert len(events)==1
    assert events[0]["type"]=="done"
    assert events[0]["found"] is False
    assert events[0]["sources"]==[]
    fake_stream.assert_not_called() # Gemini is never called when search returns nothing

def test_stream_llm_error_yields_error_event()->None:
    chunks=[make_result("Resignation","Give two weeks notice.",32)]
    with (
        mock.patch.object(ask_service,"search_documents",autospec=True,return_value=chunks),
        mock.patch.object(ask_service,"stream_answer",autospec=True,side_effect=LLMError("boom")),
    ):
        events=_parse_events(ask_service.stream_ask_question_events("What is the notice period?",5))
    assert events[-1]["type"]=="error"
    assert "boom" in events[-1]["message"]