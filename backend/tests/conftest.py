from collections.abc import Iterator
from pathlib import Path
import pytest
from rag_assistant.storage import vector_store

@pytest.fixture # pytest runs this before every test that lists temp_vector_store as a parameter
def temp_vector_store(tmp_path:Path,monkeypatch:pytest.MonkeyPatch)->Iterator[Path]: # tmp_path = new empty folder per test , monkeypatch = temporary changes undone after the test
    monkeypatch.setattr(vector_store,"CHROMA_PATH",tmp_path) # Chroma now saves into the temp folder , the real backend/data/chroma is never touched
    vector_store.get_collection.cache_clear() # forget any collection opened earlier , so the next call opens one at the new path
    yield tmp_path # the test runs here and receives the temp folder
    vector_store.get_collection.cache_clear() # cleanup , the next test must not reuse a collection whose folder is about to be deleted