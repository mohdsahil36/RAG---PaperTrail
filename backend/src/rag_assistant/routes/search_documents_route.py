from fastapi import APIRouter
from rag_assistant.controller.search_documents_controller import search_documents_controller
from rag_assistant.schemas.search_schema import SearchRequest, SearchResponse

router = APIRouter()

@router.post("/retrieve",response_model=SearchResponse) # passages only; no LLM
def search_documents_route(request:SearchRequest): # plain def , FastAPI runs it in a worker thread so embedding the question does not block other requests
    return search_documents_controller(request)
