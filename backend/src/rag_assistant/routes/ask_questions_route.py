from fastapi import APIRouter
from rag_assistant.controller.ask_questions_controller import ask_questions_controller,ask_stream_controller, ask_tools_controller
from rag_assistant.schemas.ask_schema import AskRequest, AskResponse
from fastapi.responses import StreamingResponse

router = APIRouter()

@router.post("/answer", response_model=AskResponse)
def grounded_answer(request: AskRequest):  # one-shot JSON — hybrid search + Gemini answer
    return ask_questions_controller(request)

@router.post("/answer/stream")
def grounded_answer_stream(request: AskRequest):  # SSE stream — tokens live, sources on done event
    return StreamingResponse(
        ask_stream_controller(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

@router.post("/answer/tools", response_model=AskResponse)
def grounded_answer_with_tool_calling(request: AskRequest):  # two-call loop — Gemini picks the query via tool call, then answers from retrieved passages
    return ask_tools_controller(request)