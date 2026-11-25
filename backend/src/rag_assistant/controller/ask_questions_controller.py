import logging # for logging errors

from fastapi import HTTPException
from rag_assistant.generation.llm_client import LLMError
from rag_assistant.schemas.ask_schema import AskRequest,AskResponse
from rag_assistant.services.ask_service import ask_question, ask_question_with_tools, stream_ask_question_events

logger=logging.getLogger(__name__)

def ask_questions_controller(request:AskRequest)->AskResponse: # request is already validated by FastAPI , invalid input never reaches here (422)
    try:
        return ask_question(request.question,request.k,request.document_id)
    except LLMError: # Gemini failed , timeout , rate limit or a broken reply , the user can try again later
        logger.exception("Gemini failed to answer")
        raise HTTPException(
            status_code=503,
            detail="The answer service is not available right now. Try again later.",
        )
    except Exception: # anything else is a bug on our side
        logger.exception("Error answering the question")
        raise HTTPException(
            status_code=500,
            detail="Answering the question failed.", # generic message , internal errors are not shown to the client
        )

def ask_stream_controller(request:AskRequest):
    # errors are SSE {"type":"error"} events inside the generator — no try/except here
    return stream_ask_question_events(request.question,request.k,request.document_id)

def ask_tools_controller(request: AskRequest) -> AskResponse:
    try:
        return ask_question_with_tools(request.question, request.k, request.document_id)
    except LLMError:
        logger.exception("Gemini failed on tool calling path")
        raise HTTPException(status_code=503, detail="The answer service is not available right now. Try again later.")
    except Exception:
        logger.exception("Error on tool calling path")
        raise HTTPException(status_code=500, detail="Answering the question failed.")