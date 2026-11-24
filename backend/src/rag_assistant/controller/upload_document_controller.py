import logging  # for logging errors
import shutil   # Copies the uploaded file to a temporary file
import tempfile # Creates a temporary file
from pathlib import Path # Extracts the file extension and filename.
from typing import Annotated # Define the uploaded file parameter for the FASTAPI processing

from fastapi import File, HTTPException, UploadFile # FASTAPI imports for file handling
from rag_assistant.services.upload_document_service import upload_document

logger= logging.getLogger(__name__) # For logging errors 

async def upload_document_controller(file:Annotated[UploadFile, File(...)]):
# Annotated- represents the file received from the client.
# File(...) tells FastAPI that the file is required.
# Annotated combines the type and FastAPI metadata.
    if not file.filename or Path(file.filename).suffix.lower()!=".pdf":
        raise HTTPException(status_code=400,detail="Invalid file format . For now only PDF files are supported.")
    try:
        with tempfile.NamedTemporaryFile(delete=False,suffix=".pdf") as temp_file: 
            temp_path=temp_file.name
            shutil.copyfileobj(file.file,temp_file) 
            # this because creating a temporary file does not copy the data of the file into the temporary file , so we move the data from the uploaded file to the temporary file
            # using tempfile NamedTemporaryFile() creates a file on disk, 
            # suffix=".pdf" gives the temporary file a PDF extension,
            # delete=False keeps the file available after the with block closes it,
            # temp_file.name gives you its path,
            # file.file provides access to the uploaded file's underlying file object
        data=upload_document(temp_path, Path(file.filename).name)
        return {"filename": Path(file.filename).name, "pages": data["pages"], "chunks": data["chunks"],"chunks_stored": data["chunks_stored"]}
    except HTTPException:
        raise  
    except Exception as e:
        logger.exception("Error uploading document")
        raise HTTPException(
            status_code=500,
            detail="Document ingestion failed.",
        )
    finally:
        if "temp_path" in locals():
            Path(temp_path).unlink(missing_ok=True)
        await file.close()