from pydantic import BaseModel, Field

class AskRequest(BaseModel):
    question:str=Field(min_length=1)
    k:int=Field(default=5,le=20,ge=1)
    document_id:str | None=None

class Source(BaseModel):
    heading:str
    page_number:int
    end_page:int
    document_id:str

class AskResponse(BaseModel):
    question:str
    answer:str
    found:bool
    sources:list[Source] # we  can have multiple sources for the answer