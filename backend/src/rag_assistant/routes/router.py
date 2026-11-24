from fastapi import APIRouter

from rag_assistant.routes import ask_questions_route, health, search_documents_route, upload_document_route

api_router = APIRouter()

# Register each route module's router here so main.py only needs this one router
api_router.include_router(health.router)
api_router.include_router(upload_document_route.router)
api_router.include_router(search_documents_route.router)
api_router.include_router(ask_questions_route.router)
