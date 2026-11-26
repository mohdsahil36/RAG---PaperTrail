from rag_assistant.generation.llm_client import LLMError, answer_with_tools, generate_answer, stream_answer
from rag_assistant.generation.prompt_builder import NOT_FOUND_ANSWER, GROUNDING_RULES, build_prompt, build_stream_prompt, format_chunks
from rag_assistant.schemas.ask_schema import AskResponse,Source
from rag_assistant.services.search_documents_service import search_documents
from rag_assistant.storage.vector_store import SearchResult, get_parent_chunk_by_id
import re
import json

# finds [1], [12], ... in answer text; (\d+) is the number we keep
_CITATION_RE = re.compile(r"\[(\d+)\]")

def _enrich_with_parent_text(chunks: list[SearchResult]) -> list[SearchResult]:
    # swap child text for parent text so Gemini sees the full section, not just the small span
    enriched = []
    for chunk in chunks:
        if chunk["parent_id"]:
            parent_text = get_parent_chunk_by_id(chunk["parent_id"])
            if parent_text:
                chunk = {**chunk, "text": parent_text} # create a copy of the chunk and replace the text value with the parent id 
        enriched.append(chunk)
    return enriched

def _not_found(question:str)->AskResponse:
    return AskResponse(question=question, answer=NOT_FOUND_ANSWER, found=False, sources=[])

def _citations_from_answer(answer:str,chunk_count:int)->list[int]:
    # stream has no citations list — read [n] from the plain-text answer
    # chunk_count = how many passages we sent (len(chunks)), not len(answer)
    # in:  "Leave is 20 days [1]. Also [2][1]." , chunk_count=5
    # out: [1, 2]  (in range, unique, first-seen order)
    valid:list[int]=[]
    for match in _CITATION_RE.finditer(answer): # walk left → right over every [n]
        n=int(match.group(1)) # digits inside the brackets, e.g. "2" → 2
        if 1<=n<=chunk_count and n not in valid: # drop out-of-range and repeats
            valid.append(n)
    return valid # after all matches — not inside the loop



def ask_question(question:str,k:int,document_id:str|None=None)->AskResponse:
    chunks=search_documents(question=question,k=k,document_id=document_id)
    if not chunks:
        return _not_found(question)
    chunks=_enrich_with_parent_text(chunks)
    system_prompt,user_prompt=build_prompt(question,chunks)
    llm_response=generate_answer(system_prompt,user_prompt)
    if not llm_response.found: # chunks were found but they do not have the answer
        return _not_found(question)
    valid_citations:list[int]=[]
    for citation in llm_response.citations:
        if 1<=citation<=len(chunks) and citation not in valid_citations: # skip numbers we never sent , and repeats like [1, 1]
            valid_citations.append(citation)
    if not valid_citations: # an answer we cannot trace to any page is not shown
        return _not_found(question)
    sources:list[Source]=[]
    for citation in valid_citations:
        chunk=chunks[citation-1] # [1] is chunks[0] , the prompt counts from 1 and the list from 0
        sources.append(Source(
            heading=chunk["heading"],
            page_number=chunk["page_number"],
            end_page=chunk["end_page"],
            document_id=chunk["document_id"],
        ))
    return AskResponse(question=question,answer=llm_response.answer,found=True,sources=sources)

def stream_ask_question_events(question:str,k:int,document_id:str|None=None):
    try:
        chunks=search_documents(question=question,k=k,document_id=document_id)
        if not chunks:
            yield f"data: {json.dumps({'type':'done','found':False,'sources':[]})}\n\n"
            return
        chunks=_enrich_with_parent_text(chunks)
        system_prompt,user_prompt=build_stream_prompt(question,chunks)
        full_answer:list[str]=[]
        for token in stream_answer(system_prompt,user_prompt):
            full_answer.append(token)
            yield f"data: {json.dumps({'type':'token','text':token})}\n\n"
        citations=_citations_from_answer("".join(full_answer),len(chunks))
        if not citations: # answer had no traceable [n] — could not confirm any source
            yield f"data: {json.dumps({'type':'done','found':False,'sources':[]})}\n\n"
            return
        sources=[
            {
                'heading':chunks[n-1]['heading'],
                'page_number':chunks[n-1]['page_number'],
                'end_page':chunks[n-1]['end_page'],
                'document_id':chunks[n-1]['document_id'],
            }
            for n in citations
        ]
        yield f"data: {json.dumps({'type':'done','found':True,'sources':sources})}\n\n"
    except LLMError as e:
        yield f"data: {json.dumps({'type':'error','message':str(e)})}\n\n"
    except Exception:
        yield f"data: {json.dumps({'type':'error','message':'Stream failed.'})}\n\n"

def ask_question_with_tools(question: str, k: int, document_id: str | None = None) -> AskResponse:
    # call 1 — answer_with_tools sends question + SEARCH_TOOL to Gemini
    #           Gemini returns a better search query e.g. "Paid time off PTO leave entitlement" instead of the raw user question
    #           tool_args = {"query": "..."} — the query Gemini chose
    # search  — search_documents runs with Gemini's query (not the original question) for better retrieval
    # call 2  — build_prompt + generate_answer: standard JSON path, same as /answer
    #           we use this instead of answer_with_tool_result_and_context because gemini-3.5-flash-lite
    #           is a thinking model that ignores tool_config=NONE and keeps calling tools on multi-turn
    tool_args, _ = answer_with_tools(question)                                          # call 1 — query decision
    chunks = search_documents(question=tool_args["query"], k=k, document_id=document_id)
    if not chunks:
        return _not_found(question)
    chunks = _enrich_with_parent_text(chunks)
    system_prompt, user_prompt = build_prompt(question, chunks)  # original question + passages — defined in prompt_builder.py
    llm_response = generate_answer(system_prompt, user_prompt)   # call 2 — grounded JSON answer
    if not llm_response.found:
        return _not_found(question)
    valid_citations: list[int] = []
    for citation in llm_response.citations:
        if 1 <= citation <= len(chunks) and citation not in valid_citations:  # drop out-of-range and repeats
            valid_citations.append(citation)
    if not valid_citations:  # answer has no traceable [n] — treat as not found
        return _not_found(question)
    sources: list[Source] = []
    for citation in valid_citations:
        chunk = chunks[citation - 1]  # [1] is chunks[0]
        sources.append(Source(
            heading=chunk["heading"],
            page_number=chunk["page_number"],
            end_page=chunk["end_page"],
            document_id=chunk["document_id"],
        ))
    return AskResponse(question=question, answer=llm_response.answer, found=True, sources=sources)
