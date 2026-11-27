from typing import TypedDict

class ConversationTurn(TypedDict):
    role: str
    content: str