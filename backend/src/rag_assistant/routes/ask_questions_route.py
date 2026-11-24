from fastapi import APIRouter
from rag_assistant.controller.ask_questions_controller import ask_questions_controller,ask_stream_controller
from rag_assistant.schemas.ask_schema import AskRequest, AskResponse
from fastapi.responses import StreamingResponse

router = APIRouter()

@router.post("/answer",response_model=AskResponse) # grounded answer from retrieved passages
def ask_questions_route(request:AskRequest): # plain def , FastAPI runs it in a worker thread so the embedding and the Gemini call do not block other requests
    return ask_questions_controller(request)

@router.post("/answer/stream")
def ask_questions_stream_router(request:AskRequest):
    return StreamingResponse(
        ask_stream_controller(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
