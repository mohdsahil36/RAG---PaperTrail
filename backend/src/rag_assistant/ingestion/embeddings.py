from functools import lru_cache  # built in decorator to cache the result of the function
from sentence_transformers import SentenceTransformer # library to generate embeddings from text
from rag_assistant.ingestion.chunking import DocumentSection # Chunk type so that we can describe the input and the output to and from the function

EMBEDDING_MODEL= "all-MiniLM-L6-v2" # hardcoded model name for now , it can be made a parameter in the future , one place so that the question and the chunks both use the same model

@lru_cache(maxsize=1) # first call loads the model into memory , later calls return the cached model result
def get_embedding_model()->SentenceTransformer: # Function with no inputs which returns a SentenceTransformer object
    return SentenceTransformer(EMBEDDING_MODEL)

class EmbeddedChunk(DocumentSection):
    embedding:list[float] ## vector is 384 vector numbers (according to the current model) telling the chunk meaning , chroma and JSON cannot handle numpy arrays so we convert it into a list , make the vector from the chunk and get ready to save it to ChromaDB
    chunk_type:str
    parent_id:str


def text_for_embedding(chunk:DocumentSection)->str: ## this is a helper function to get the text for the embedding , it combines the heading and the text of the chunk
    if chunk["heading"]:
        return f"{chunk['heading']}\n{chunk['text']}"
    else:
        return chunk["text"]

def embed_chunks(chunks:list[DocumentSection], chunk_type:str="child", parent_id:str="")->list[EmbeddedChunk]:
    if not chunks: # no chunks (e.g. a PDF with no text) , return nothing without loading the model
        return []

    # Loop 1: collect the text to embed for each chunk
    texts=[]
    for chunk in chunks:
        texts.append(text_for_embedding(chunk))

    # One batched call for all the texts , outside any loop
    model= get_embedding_model()
    # encode: splits each text into tokens (max 256) -> model gives a vector per token -> averages them into one 384-number vector per text , all texts processed together in batches
    vectors=model.encode(texts, normalize_embeddings=True) # normalize_embeddings=True scales every vector to length 1 , so comparing two vectors is a plain dot product (= cosine similarity)

    #Loop 2 : pair each chunk with its embedded vector
    embedded_chunks=[]
    for chunk,vector in zip(chunks,vectors): # walk through both the chunk and the vector list at the same time
        embedded_chunks.append(EmbeddedChunk(
            heading=chunk["heading"],
            text=chunk["text"],
            page_number=chunk["page_number"],
            end_page=chunk["end_page"],
            embedding=vector.tolist(),
            chunk_type=chunk_type,
            parent_id=parent_id,
        ))
    return embedded_chunks

def embed_user_query(query:str)->list[float]:
    model=get_embedding_model()
    # encode with a single text returns one 384-number vector (not a table) , tokens -> model -> averaged into one vector
    vector=model.encode(query,normalize_embeddings=True) # normalize_embeddings=True scales the vector to length 1 , matching the stored chunk vectors so dot product = cosine similarity
    return vector.tolist()