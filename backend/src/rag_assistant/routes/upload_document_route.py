from fastapi import APIRouter, File, UploadFile
from typing import Annotated
from rag_assistant.controller.upload_document_controller import upload_document_controller

router = APIRouter()

@router.post("/upload-document")
async def upload_document_route(file:Annotated[UploadFile,File(...)]):
    return await upload_document_controller(file)