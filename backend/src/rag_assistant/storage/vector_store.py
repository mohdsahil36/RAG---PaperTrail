from functools import lru_cache
from pathlib import Path
from rag_assistant.ingestion.embeddings import EMBEDDING_MODEL,EmbeddedChunk,embed_user_query
from typing import TypedDict, cast
import chromadb

CHROMA_PATH=Path(__file__).resolve().parents[3]/"data"/"chroma" # folder where Chroma saves its data: backend/data/chroma
COLLECTION_NAME="dataStorage_collection" # the "table" that holds all our chunks , name needs 3+ characters

@lru_cache(maxsize=1) # open Chroma once , later calls reuse the same collection
def get_collection()->chromadb.Collection:
    client = chromadb.PersistentClient(path=str(CHROMA_PATH)) # persistent client: data is saved on disk and survives restarts
    return client.get_or_create_collection( # create the collection the first time , reuse it after
        name=COLLECTION_NAME,
        configuration={
            "hnsw":{
                "space":"cosine" # distance metric , set once at creation , distance = 1 - similarity
            }
        }
    )

def add_chunk_to_db(document_id:str,chunks:list[EmbeddedChunk])->int: # saves one document's chunks , returns how many were stored
    collection =get_collection()
    collection.delete(where={"document_id":document_id}) # delete any existing chunks for this document , so an older version leaves nothing behind
    
    if not chunks: # nothing to store (e.g. a PDF with no text)
        return 0
    ids=[] # one unique key per chunk
    metadatas=[] # extra fields per chunk , used for filtering and citations
    embeddings=[] # one vector per chunk
    documents=[] # one clean text per chunk , returned with search results

    for number, chunk in enumerate(chunks): # enumerate gives each chunk its position: 0, 1, 2...
        ids.append(f"{document_id}--{number}") # stable ID: same file + same position = same ID
        documents.append(chunk["text"]) # clean chunk text , without the heading
        embeddings.append(chunk["embedding"]) # our own vector , so Chroma never embeds anything itself
        metadatas.append({
            "document_id": document_id,
            "heading": chunk["heading"] or "",
            "page_number": chunk["page_number"],
            "end_page": chunk["end_page"],
            "embedding_model": EMBEDDING_MODEL,
            "chunk_type": chunk["chunk_type"],
            "parent_id": chunk["parent_id"],
        })
    collection.upsert(ids=ids,documents=documents,metadatas=metadatas,embeddings=embeddings) # one call for all chunks: inserts new IDs , replaces existing ones
    return len(ids) # number of chunks stored

class SearchResult(TypedDict):
    text: str
    heading: str
    page_number: int
    end_page: int
    document_id: str
    score: float  # similarity: 1.0 = same meaning, 0 = unrelated
    chunk_id: str  # unique ID for this chunk , used for RRF
    parent_id: str  # ID of the parent chunk; "" for parent chunks themselves

def search_chunks(question: str, k: int = 5, document_id: str | None = None)->list[SearchResult]:
    if k<=0:
        raise ValueError("k must be a positive integer")

    collection = get_collection()
    if(collection.count()==0): # nothing stored yet , skip embedding the question
        return []

    question_vector_embedding= embed_user_query(question) # same model and settings as the stored chunks
    child_filter: chromadb.Where = {"chunk_type": "child"}
    whereQuery: chromadb.Where | None = (
        {"$and": [{"document_id": document_id}, child_filter]} if document_id else child_filter
    )
    result = collection.query(query_embeddings=[question_vector_embedding], n_results=k, where = whereQuery) # a list of question vectors , we send one

    found: list[SearchResult] = []

    documents = result["documents"] or [[]] # Chroma types these fields as optional , fall back to "no results" if missing
    metadatas = result["metadatas"] or [[]]
    distances = result["distances"] or [[]]
    ids=result["ids"] or [[]]

    # field[0] = results for our single question , already sorted closest first
    for text, metadata, distance, chunk_id in zip(
        documents[0], metadatas[0], distances[0], ids[0]
    ):
        # Chroma types every metadata value as "any allowed type" , cast tells the type checker what we stored in add_chunk_to_db
        found.append(
            SearchResult(
                text=text,
                heading=cast(str, metadata["heading"]),
                page_number=cast(int, metadata["page_number"]),
                end_page=cast(int, metadata["end_page"]),
                document_id=cast(str, metadata["document_id"]),
                score=1-distance,
                chunk_id=chunk_id,
                parent_id=cast(str, metadata.get("parent_id", "")),
            )
        )
    return found

def get_parent_chunk_by_id(parent_id:str)->str | None:
    collection =get_collection()
    data=collection.get(ids=[parent_id], include=["documents"])

    parentText = data["documents"]
    return parentText[0] if parentText else None