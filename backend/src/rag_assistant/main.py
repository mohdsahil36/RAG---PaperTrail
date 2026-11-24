from fastapi import FastAPI

from rag_assistant.routes.router import api_router

app = FastAPI()

app.include_router(api_router)
