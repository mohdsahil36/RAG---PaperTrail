from rag_assistant.storage.vector_store import SearchResult
from rag_assistant.generation.system_prompts import SYSTEM_PROMPT, STREAM_SYSTEM_PROMPT
from rag_assistant.models.conversation import ConversationTurn

def format_chunks(chunks:list[SearchResult])->str:
    passages:list[str]=[]
    for number , chunk in enumerate(chunks, start=1):
        label=f"[{number}] {chunk['heading']}" # e.g. [1] Resignation, convert the chunk to a string
        passages.append(f"{label}\n{chunk['text']}") # label on its own line , then the chunk text
    return "\n\n".join(passages) # a blank line between passages

def _format_history(history:list[ConversationTurn])->str:
    lines=[]
    for turn in history:
        role="User" if turn["role"]=="user" else "Assistant"
        lines.append(f"{role}:{turn['content']}")

    return "\n".join(lines)

def _user_prompt(question:str,chunks:list[SearchResult],history:list[ConversationTurn]=[])->str:
    if not chunks:
        raise ValueError("No chunks received!")
    base = f"Context:\n{format_chunks(chunks)}"
    if history:
        base += f"\n\nConversation so far:\n{_format_history(history)}"
    # same user message for JSON and stream — only the system prompt differs
    return base + f"\n\nQuestion: {question}"

def build_prompt(question:str, chunks:list[SearchResult],history:list[ConversationTurn]=[])->tuple[str,str]:
    return SYSTEM_PROMPT,_user_prompt(question,chunks,history)

def build_stream_prompt(question:str, chunks:list[SearchResult],history:list[ConversationTurn]=[])->tuple[str,str]:
    # twin of build_prompt for /answer/stream
    return STREAM_SYSTEM_PROMPT,_user_prompt(question,chunks,history)

