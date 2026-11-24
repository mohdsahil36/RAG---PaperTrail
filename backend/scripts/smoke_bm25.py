# What this file is:
# A small test drive for BM25 (keyword search) on the real handbook chunks.
# It only prints results. It does not change /search or /ask.
# Why? so that we know that if BM25 alone it self can work as the search method instead of dense vector search or we have to combine both with RRF
from rag_assistant.services.retrieval.bm25 import bm25_search
from rag_assistant.storage.vector_store import get_collection

QUESTION="how many leaves I can take annually?"
K=5 # how many top results to show

def main()->None:
    # Open the same Chroma database the app uses.
    collection=get_collection()

    # Ask Chroma for all saved chunk texts and their extra info (heading, pages, ...).
    raw=collection.get(include=["metadatas","documents"])

    # corpus[i] = text of chunk i
    # metadatas[i] = heading/pages for that same chunk i
    corpus=raw["documents"] or []
    metadatas=raw["metadatas"] or []

    if not corpus:
        print("No chunks available in the vector database. Upload the document first!")
        return
    print(f"Found {len(corpus)} chunks in the vector database.")

    # Run keyword search. Each hit is: (which chunk, how strong the match is)
    hits=bm25_search(QUESTION,corpus=corpus,k=K)

    print("Q:", QUESTION)

    # Show the results in order: best match first.
    # rank   = 1, 2, 3... (place in the list we print)
    # index  = which chunk in corpus / metadatas
    # score  = BM25 match strength (higher is better)
    for rank, (index, score) in enumerate(hits, start=1):
        # Look up the heading for this chunk index.
        heading = (metadatas[index] or {}).get("heading", "")
        print(f"  [{rank}] {score:.3f}  {heading}")

if __name__ == "__main__":
    # When you run: python scripts/smoke_bm25.py
    # Python starts here and calls main().
    main()