import logging # for logging errors

from fastapi import HTTPException
from rag_assistant.schemas.search_schema import SearchRequest, SearchResponse, SearchResultItem
from rag_assistant.services.search_documents_service import search_documents

logger=logging.getLogger(__name__)

def search_documents_controller(request:SearchRequest)->SearchResponse: # request is already validated by FastAPI , invalid input never reaches here (422)
    try:
        results=search_documents(request.question,request.k,request.document_id)
        items:list[SearchResultItem]=[]
        for result in results:
            items.append(SearchResultItem(**result)) # ** unpacks the dict into keyword arguments , a new item per result
        return SearchResponse(question=request.question,results=items)
    except Exception:
        logger.exception("Error searching documents") # full error goes to the server log only
        raise HTTPException(
            status_code=500,
            detail="Search failed.", # generic message , internal errors are not shown to the client
        )
