from rag_assistant.storage.vector_store import SearchResult
from rag_assistant.generation.system_prompts import (
    NOT_FOUND_ANSWER,
    GROUNDING_RULES,
    SYSTEM_PROMPT,
    STREAM_SYSTEM_PROMPT,
)

def format_chunks(chunks:list[SearchResult])->str:
    passages:list[str]=[]
    for number , chunk in enumerate(chunks, start=1):
        label=f"[{number}] {chunk['heading']}" # e.g. [1] Resignation, convert the chunk to a string
        passages.append(f"{label}\n{chunk['text']}") # label on its own line , then the chunk text
    return "\n\n".join(passages) # a blank line between passages

def _user_prompt(question:str,chunks:list[SearchResult])->str:
    if not chunks:
        raise ValueError("No chunks received!")
    # same user message for JSON and stream — only the system prompt differs
    return f"Context:\n{format_chunks(chunks)}\n\nQuestion: {question}"

def build_prompt(question:str, chunks:list[SearchResult])->tuple[str,str]:
    return SYSTEM_PROMPT,_user_prompt(question,chunks)

def build_stream_prompt(question:str, chunks:list[SearchResult])->tuple[str,str]:
    # twin of build_prompt for /answer/stream
    return STREAM_SYSTEM_PROMPT,_user_prompt(question,chunks)

