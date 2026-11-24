import time
from rag_assistant.storage.vector_store import SearchResult
from rag_assistant.services.search_documents_service import search_documents

K=5 # same default as /search

# (question, expected heading) , heading must match the store exactly , None = unrelated
CASES: list[tuple[str, str | None]] = [
    ("How many days of annual leave do I get?", "Paid time off (PTO)"),
    ("Am I paid extra for working late?", "Overtime"),
    ("Can I date a coworker?", "Employee relationships"),
    ("What is the notice period for resignation?", "Resignation"),
    ("How many leaves can I take?", "Paid time off (PTO)"),
    ("What is the capital of France?", None),
    ("How do I bake a chocolate cake?", None),
    ("Whom to contact if have been harassed at workplace?","Workplace harassment"),
    ("What are the rules fo taking work from home?","Work from home"),
    ("What happens if I am required to work on a holiday?","Holidays")
]

def find_rank(chunks: list[SearchResult], expected: str)->int | None:
    """1 = top result , None = expected heading not in the list."""
    for i, chunk in enumerate(chunks, start=1):
        if chunk["heading"] == expected:
            return i
    return None

def main()->None:
    hits=0 # how many labelled questions put the right heading in top K
    rr_sum=0.0 # add 1/rank for each hit (for MRR)
    n_labelled=0 # how many questions have an expected heading

    time_ms:list[float]=[] # one ms per CASES row, same order
    labelled_ms:list[float]=[] # only questions with an expected heading

    for question, expected in CASES:
        t0=time.perf_counter() #this is a stopwatch
        # if we want to check how close the dense search is then we can replace the search_documents by search chunks, but if we want to check if our rewrite made any difference then we use search_documents ,
        chunks=search_documents(question, k=K,document_id="employee_handbook.pdf") # raw top-K , no MIN_SCORE cut
        ms=(time.perf_counter()-t0)*1000 #elapsed time in milliseconds
        time_ms.append(ms) # keep in memory
        print(f"Fetch time: {ms:.2f}ms")
        print("---")
        print("Q:", question)
        print("expected:", expected)
        for i, chunk in enumerate(chunks, start=1):
            print(f"  [{i}] {chunk['score']:.3f}  {chunk['heading']}")

        if expected is None:
            top=chunks[0]["score"] if chunks else 0.0
            print(f"unrelated, top score={top:.3f}")
            continue

        labelled_ms.append(ms) # typical retrieve path (no unrelated rewrite cases)
        n_labelled+=1
        rank=find_rank(chunks, expected)
        if rank is None: # if the required answer is not in the top K retrived chunks 
            print("rank: miss")
        else:
            print(f"rank: {rank}")
            hits+=1
            rr_sum+=1/rank

    print("===")
    if n_labelled==0:
        print("no labelled cases")
        return
    print(f"hit@{K}: {hits}/{n_labelled} = {hits/n_labelled:.2f}")
    print(f"MRR: {rr_sum/n_labelled:.2f}")

    # time_ms[i] ↔ CASES[i]; labelled_ms omits expected=None (France/cake rewrite)
    if time_ms:
        print(f"first question (models loading): {time_ms[0]:.1f} ms")
        after_first = time_ms[1:] if len(time_ms) > 1 else time_ms
        print(
            f"avg after that (all questions): {sum(after_first)/len(after_first):.1f} ms  "
            f"({len(after_first)} questions; includes slow rewrite cases)"
        )
        # skip first labelled time — same as first question above
        later_labelled = labelled_ms[1:] if len(labelled_ms) > 1 else labelled_ms
        if later_labelled:
            print(
                f"avg handbook questions (no rewrite): {sum(later_labelled)/len(later_labelled):.1f} ms  "
                f"({len(later_labelled)} questions)"
            )

if __name__ == "__main__":
    main()
