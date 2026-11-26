import pytest
from rag_assistant.generation.prompt_builder import build_prompt
from rag_assistant.generation.system_prompts import NOT_FOUND_ANSWER
from rag_assistant.storage.vector_store import SearchResult

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

def test_chunks_are_numbered_with_heading()->None:
    chunks=[make_result("Resignation","Give two weeks notice.",32),
            make_result("Leaving our company","How resignation works.",31)]

    _,user_prompt=build_prompt("What is the notice period?",chunks) # _ = we don't need the system prompt here

    assert "[1] Resignation" in user_prompt
    assert "[2] Leaving our company" in user_prompt
    assert "(pages" not in user_prompt

def test_question_comes_after_context()->None:
    question="What is the notice period?"
    chunks=[make_result("Resignation","Give two weeks notice.",32)]
    _,user_prompt=build_prompt(question,chunks)

    assert user_prompt.index(question)>user_prompt.index("[1]") # index = position in the text , bigger = further down , so the question comes after the passages

def test_system_prompt_has_found_rule()->None:
    chunks=[make_result("Resignation","Give two weeks notice.",32)]
    system_prompt,_=build_prompt("What is the notice period?",chunks) # keep the rules this time , ignore the user query

    assert "set found to false" in system_prompt # not found is now a JSON field , not a sentence
    assert NOT_FOUND_ANSWER not in system_prompt # the sentence is for the user only , the service returns it

def test_empty_chunks_raise_error()->None:
    with pytest.raises(ValueError): # passes only if build_prompt raises a ValueError here
        build_prompt("What is the notice period?",[])
