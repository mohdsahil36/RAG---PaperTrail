from pathlib import Path
from rag_assistant.ingestion.chunking import DocumentSection
from rag_assistant.ingestion.embeddings import embed_chunks, EmbeddedChunk
from rag_assistant.storage import vector_store # import the module itself , patching a copied name would leave the module unchanged
from chromadb.api.shared_system_client import SharedSystemClient



def make_chunks(sections:list[tuple[str,str,int]])->list[EmbeddedChunk]: # (heading, text, page) tuples -> chunks with real 384-number vectors
    chunks:list[DocumentSection]=[]
    for heading, text, page in sections: # each tuple unpacks into three names
        chunks.append({
            "heading": heading,
            "text": text,
            "page_number": page,
            "end_page": page, # a short test section starts and ends on the same page
        })
    return embed_chunks(chunks)


def test_empty_store_returns_empty_list(temp_vector_store:Path)->None:
    result = vector_store.search_chunks("How many leave days do I get?") # nothing stored yet in the temp folder

    assert result == []

def test_store_and_search_chunks(temp_vector_store:Path)->None:
    embedded_chunks=make_chunks([
        ("Leave Policy", "Employees get 20 days of paid leave.", 1),
        ("Office Hours", "The office opens at 9 am.", 2),
    ])
    stored=vector_store.add_chunk_to_db("handbook.pdf", embedded_chunks) # returns how many chunks were stored

    results=vector_store.search_chunks("How many leave days do I get?")

    assert stored == 2
    assert len(results)==2
    assert results[0]["heading"]=="Leave Policy"
    assert results[0]["score"]>results[1]["score"]
    assert (temp_vector_store / "chroma.sqlite3").exists()

def test_reupload_replaces_chunks(temp_vector_store:Path)->None:
    old_version=make_chunks([
        ("Leave Policy", "Employees get 20 days of paid leave.", 1),
        ("Office Hours", "The office opens at 9 am.", 2),
    ])
    new_version=make_chunks([
        ("Leave Policy", "Employees get 20 days of paid leave.", 1), # Office Hours was removed from the handbook
    ])

    first_upload=vector_store.add_chunk_to_db("handbook.pdf", old_version)
    second_upload=vector_store.add_chunk_to_db("handbook.pdf", new_version) # same document_id , so it replaces the old version
    results=vector_store.search_chunks("When does the office open?")

    assert first_upload==2
    assert second_upload==1
    assert vector_store.get_collection().count()==1 # delete removed both old chunks , upsert alone would leave handbook.pdf--1 behind
    assert all(result["heading"]!="Office Hours" for result in results) # the removed section can no longer be found

def test_change_document_never_touch_other_document(temp_vector_store:Path)->None:
    handbook_chunks=make_chunks([("Leave Policy", "Employees get 20 days of paid leave.", 1)])
    manual_chunks=make_chunks([("Office Hours", "The office opens at 9 am.", 2)])

    vector_store.add_chunk_to_db("handbook.pdf", handbook_chunks)
    vector_store.add_chunk_to_db("employee_manual.pdf", manual_chunks)

    stored=vector_store.add_chunk_to_db("handbook.pdf", []) # the change: empties handbook.pdf only, we have added [] so it has emptied the handbook.pdf

    handbook_results=vector_store.search_chunks("How many leave days do I get?", document_id="handbook.pdf")
    manual_results=vector_store.search_chunks("When does the office open?", document_id="employee_manual.pdf")

    assert stored==0
    assert handbook_results==[] # handbook.pdf is gone
    assert len(manual_results)==1 # employee_manual.pdf survived the delete
    assert manual_results[0]["heading"]=="Office Hours"
    assert vector_store.get_collection().count()==1

def test_chunks_survive_reopening(temp_vector_store:Path)->None:
    handbook_chunks=make_chunks([("Leave Policy", "Employees get 20 days of paid leave.", 1)])
    vector_store.add_chunk_to_db("handbook.pdf",handbook_chunks)
    vector_store.get_collection.cache_clear() # clear LRU cache
    SharedSystemClient.clear_system_cache() # clear system cache

    results = vector_store.search_chunks("How many leave days do I get?")

    assert len(results)==1
    assert results[0]["heading"]=="Leave Policy"
    assert vector_store.get_collection().count()==1