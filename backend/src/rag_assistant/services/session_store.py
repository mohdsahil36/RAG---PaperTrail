from rag_assistant.models.conversation import ConversationTurn

MAX_HISTORY_TURNS=10
_sessions:dict[str,list[ConversationTurn]]={}

def get_conversation_history(session_id:str)->list[ConversationTurn]:
    return _sessions.get(session_id,[])

def append_conversation_turn(session_id:str,role:str,content:str)->None:
    if session_id not in _sessions:
        _sessions[session_id]=[]
    _sessions[session_id].append(ConversationTurn(role=role,content=content))
    if len(_sessions[session_id]) > MAX_HISTORY_TURNS:
        _sessions[session_id] = _sessions[session_id][-MAX_HISTORY_TURNS:]
