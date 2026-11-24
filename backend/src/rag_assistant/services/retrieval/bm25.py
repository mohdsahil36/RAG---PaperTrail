import re  # for splitting texts to individual words
from rank_bm25 import BM25Okapi # for the BM25 search strategy

def _tokenize(text:str)->list[str]: #private helper (underscore==internal)
    lower=text.lower() # step 1: same word, same form
    words=re.findall(r"[a-z0-9]+", lower) # step 2: keep letter/digit runs; drop punctuation
    return words


def bm25_search(query: str, corpus: list[str], k: int) -> list[tuple[int, float]]: #public function tests will call , corpus is the complete list of chunks from the store of the document
    if not corpus:
        return []
    if k<=0:
        raise ValueError("K must be a valid positive integer!")
    tokenized_corpus=[_tokenize(doc) for doc in corpus]
    query_tokens=_tokenize(query)
    if not query_tokens: # user query is empty or just punctuation
        return []
    bm25=BM25Okapi(tokenized_corpus) # build the keyword index from all the chunk tokens
    scores=bm25.get_scores(query_tokens) # get the BM25 score for the user query vs the tokenized corpus

    # give a numbering of each chunks score to an index number
    scored_chunks = []
    for index, score in enumerate(scores):
        scored_chunks.append((index, float(score)))

    # highest score first
    scored_chunks.sort(key=lambda pair: pair[1], reverse=True) #reverse= True means highest first, pair[1] means that we are sorting according to the second value of the pair which is the score

    # keep at most k hits that actually matched some words
    results = []
    for index, score in scored_chunks[:k]: # k means we only keep the top k values 
        if score > 0: # then we return the index and the score of the sorted top K values
            results.append((index, score))
    return results