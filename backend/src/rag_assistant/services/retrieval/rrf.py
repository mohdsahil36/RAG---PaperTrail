# k in the formula 1/(k + rank). Ranks still start at 1 — not at 60.
RRF_K=60

def reciprocal_rank_fusion(rankings:list[list[str]],k:int=RRF_K)->list[tuple[str,float]]:
    # in:  two (or more) top lists, best first — e.g. dense ids + BM25 ids
    # out: one combined list [(id, score), ...] best first
    if not rankings:
        return []

    scores:dict[str,float]={} # empty bag: each id gets a running total

    for ranking in rankings: # take list 1, then list 2, ...
        for rank, item_id in enumerate(ranking,start=1): # 1st place, 2nd place, ...
            old = scores.get(item_id, 0.0) # 0 if we never saw this id before
            scores[item_id] = old + (1.0 / (k + rank)) # add this list's points if we already have this id in tge scores dict

    # bag -> list, then sort so the biggest total is first
    ranked = list(scores.items()) # e.g. [("A", 0.032), ("B", 0.033), ...]
    ranked.sort(key=lambda pair: pair[1], reverse=True)
    return ranked

# --- full example, step by step ---
# rankings = [
#   ["A", "B", "C"],   # list 1 (e.g. dense)
#   ["B", "D", "A"],   # list 2 (e.g. BM25)
# ]
# k = 60
# scores starts as {}
#
# FIRST LOOP — parse list 1 ["A", "B", "C"]:
#   A rank 1 -> scores["A"] = 0 + 1/61
#   B rank 2 -> scores["B"] = 0 + 1/62
#   C rank 3 -> scores["C"] = 0 + 1/63
#   bag now: A=1/61, B=1/62, C=1/63
#
# SECOND LOOP — parse list 2 ["B", "D", "A"] (same bag, keep adding):
#   B rank 1 -> scores["B"] = 1/62 + 1/61   (B already existed, we ADD)
#   D rank 2 -> scores["D"] = 0 + 1/62      (new id)
#   A rank 3 -> scores["A"] = 1/61 + 1/63   (A already existed, we ADD)
#   bag now: A=1/61+1/63, B=1/62+1/61, C=1/63, D=1/62
#
# THEN SORT — biggest total first:
#   B wins, then A, then D, then C
#   return [("B", ...), ("A", ...), ("D", ...), ("C", ...)]

