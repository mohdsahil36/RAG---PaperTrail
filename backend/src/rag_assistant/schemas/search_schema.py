from pydantic import BaseModel, Field

class SearchRequest(BaseModel): # the JSON body POST /search accepts , FastAPI returns 422 when it does not match
    question:str=Field(min_length=1) # an empty question cannot be embedded into anything useful
    k:int=Field(default=5,ge=1,le=20) # how many chunks to return , capped so one request cannot pull the whole collection
    document_id:str | None=None # search one document only , None searches everything

class SearchResultItem(BaseModel): # one chunk in the API response , kept separate from storage's SearchResult so storage can change without breaking the frontend
    text:str
    heading:str
    page_number:int
    end_page:int
    document_id:str
    score:float # similarity: 1.0 = same meaning, 0 = unrelated

class SearchResponse(BaseModel):
    question:str
    results:list[SearchResultItem] # best match first , empty when nothing passes the minimum score
