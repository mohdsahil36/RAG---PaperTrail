# Text Preprocessing Notes

Simple notes on cleaning text extracted from PDFs before chunking and embedding.
Every code example below was run in Python and the outputs shown are real.

**The one rule to remember:**

> Remove noise from the PDF layout. Keep signals of document structure.

Noise = stray spaces, invisible characters, mixed line endings.
Signal = paragraph breaks, headings, list items, page numbers.

**How each section is written:** every special character or situation has four parts:

- **Why it exists** — the legitimate reason someone uses it
- **Where it comes from** — where you will meet it in real documents
- **Problem** — what goes wrong for search / RAG
- **We** — what our preprocessing should do about it (implemented in the [section 7](#7-reference-implementation-not-yet-in-the-project) example code)

Most "weird" characters exist to control **how text looks** on screen or paper. Our goal is different: text that **searches and compares correctly**. So always ask: *does this change meaning, or only appearance?*

### Built-in vs our own code

> ⚠️ **Not implemented yet.** The functions in the "Our own helpers" row are **not** part of Python or PyMuPDF, and they do **not** exist in the project yet. They are written out in full in [section 7](#7-reference-implementation-not-yet-in-the-project). Before using them, add them to the backend (for example in `backend/src/rag_assistant/ingestion/text_preprocessing.py`).

| Type | Functions used in these notes | Where they come from |
|---|---|---|
| Python built-ins | `str.strip()`, `str.split()`, `str.replace()`, `str.translate()`, `re.sub()`, `unicodedata.normalize()` | Python standard library — available everywhere |
| PyMuPDF methods | `page.get_text()`, `page.get_images()`, `page.find_tables()` | The `pymupdf` package — already installed |
| Our own helpers | `preprocess_page_text()`, `is_blank_page_text()`, `page_needs_ocr()` | **Defined in these notes only** — must be added to the project |

---

## Cheat Sheet

**How to read this table:** each row is one special character or situation. The columns say why it exists, what our preprocessing should do with it, and which section explains it in detail.

| Character or situation | Why it exists | What our preprocessing should do | Details in section |
|---|---|---|---|
| Repeated or trailing spaces | People align text by hand; PDF layout adds them | Collapses to one space; removes spaces at line ends | 1 |
| `\t` tab | Aligns text into columns | Replaces with a normal space (extract tables separately) | 1 |
| `\u00a0` non-breaking space | Keeps two words on the same line | Replaces with a normal space | 1 |
| `\u202f` / `\u2009` narrow / thin space | Spaces out numbers and units neatly | Replaces with a normal space | 1 |
| `\u200b` zero-width space | Allows a line break without a visible space | Removes it | 1 |
| `\u200c` / `\u200d` zero-width non-joiner / joiner | Controls how letters and emoji join | **Keeps it** | 1 |
| `\u00ad` soft hyphen | Shows a hyphen only if the word wraps | Removes it | 1 |
| `\ufeff` byte order mark | Labels a file's encoding | Removes it | 1 |
| `\x00` and other control characters | Old terminal / binary signals | Removes them | 1 |
| `\r\n` / `\r` line endings | End lines on Windows / old Mac | Converts to `\n` | 2 |
| `\u2028` / `\u2029` line / paragraph separator | Unambiguous line / paragraph break | Converts to `\n` / `\n\n` | 2 |
| `\x0c` form feed | Tells a printer to start a new page | Split pages on it before cleaning | 2 |
| Line break inside a sentence | PDFs store lines, not paragraphs | **Keeps it** (join lines only per document) | 2 |
| Blank line `\n\n` | Separates paragraphs | **Keeps it** | 2 |
| `e` + `\u0301` combining accent | Builds accented letters from parts | Merges into one character `é` (NFC) | 3 |
| `ﬁ` `ﬂ` ligatures | Make fonts look better | Replaces with plain letters `fi` `fl` | 3 |
| `²` `½` `¹` superscripts and fractions | Maths, units, footnotes | **Keeps them** | 3 |
| `’` `“` `”` curly quotes | Proper typography | **Keeps them** | 3 |
| Blank, whitespace-only, or scanned page | Covers, separators, scans | Marks the page; never deletes it | 4 |

---

## 1. Whitespace and Invisible Characters

**What it is:** Characters that take up space (or no space at all) but show nothing. Some look exactly like a normal space but are different characters.

**Real data:** in `employee_handbook.pdf`, 1,294 of 1,299 lines end with a trailing space (`"candidates. \n"`), and there are 38 double spaces.

### `" "` repeated and trailing spaces

- **Why it exists:** People align text by typing several spaces. Justified text stretches the gaps between words. PDF extractors add spaces where they guess a gap on the page.
- **Where it comes from:** Almost every PDF — PyMuPDF adds a space at the end of most lines.
- **Problem:** `"Hello   world"` and `"Hello world"` are different strings, so comparison and deduplication fail. Extra spaces also waste tokens.
- **We:** collapse runs to one space, and strip spaces at line ends.
  ```python
  re.sub(r"[ \t]+", " ", "Hello   world")   # 'Hello world'
  ```

### `\t` — Tab

- **Why it exists:** Aligns text into columns; separates fields in TSV files; indents code.
- **Where it comes from:** Tables and forms in PDFs, spreadsheets.
- **Problem:** Two tabs in a row mean "an empty column", which means nothing inside a sentence.
  ```python
  "Name\t\tAge".split("\t")                # ['Name', '', 'Age']
  re.sub(r"[ \t]+", " ", "Name:\tJohn")    # 'Name: John'
  ```
- **We:** turn it into a space in normal text. If tables matter, extract them separately with `page.find_tables()` instead of relying on tabs.

### `\u00a0` — Non-breaking space

- **Why it exists:** Stops a line from breaking between two words that belong together. `10 kg` should never wrap as `10` on one line and `kg` on the next. Same for `Mr. Smith`, `₹ 500`, `Page 5`.
- **Where it comes from:** Word documents, web pages ( `` in HTML), and PDFs exported from them. HTML merges normal spaces, so people also use  `` to force extra spacing.
- **Problem:** Looks like a space, but isn't one.
  ```python
  "Hello\u00a0world" == "Hello world"   # False
  "a\u00a0b".split(" ")                 # ['a\xa0b']   <- not split
  "a\u00a0b".split()                    # ['a', 'b']   <- split() with no argument handles it
  ```
- **We:** turn it into a normal space. Line wrapping doesn't matter once text is extracted.

### `\u202f` / `\u2009` — Narrow no-break space / Thin space

- **Why they exist:** Smaller spaces for numbers and units: `10 000` (thousands separator), `5 km`.
- **Where they come from:** Scientific and European documents; some software writes times as `10:30\u202fAM`.
- **Problem:** Same as non-breaking space — looks normal, isn't `" "`.
- **We:** turn them into a normal space.
  ```python
  re.sub(r"[^\S\n]+", " ", "10:30\u202fAM")   # '10:30 AM'
  ```

### `\u200b` — Zero-width space

- **Why it exists:** Marks a place where a line *may* break, without showing a space. Used in long URLs and file paths, and to mark word boundaries in languages written without spaces (such as Thai and Khmer).
- **Where it comes from:** Web pages, CMS editors, copy-paste.
- **Problem:** Completely invisible, but it splits words for search.
  ```python
  "password" in "pass\u200bword"   # False
  ```
- **We:** remove it.

### `\u200c` / `\u200d` — Zero-width non-joiner / Zero-width joiner — ⚠️ KEEP

- **Why they exist:** Control whether neighbouring characters join together. Required in scripts like Hindi (Devanagari) and Persian, and in emoji sequences.
  ```python
  family = "👨\u200d👩\u200d👧"   # one family emoji = 5 characters, 2 of them are \u200d
  # Removing \u200d turns it into three separate people: 👨👩👧
  ```
- **Problem:** Only if you remove them — that changes how words are written.
- **We:** **never remove them.** They are not whitespace (`\s` doesn't match them), and the section 7 example code leaves them alone.

### `\u00ad` — Soft hyphen

- **Why it exists:** Tells software "you *may* break the word here — show a hyphen only if you do." Used for justified text, narrow columns, and long words (German `"Donau\u00addampf\u00adschiff"`).
- **Where it comes from:** Word processors, typeset PDFs, e-books.
- **Problem:** Invisible when the word isn't wrapped, but it breaks search.
  ```python
  "employment" in "employ\u00adment"   # False
  ```
- **We:** remove it.

### `\ufeff` — Byte Order Mark (BOM)

- **Why it exists:** An invisible label at the very start of a file saying "this is UTF-8 / UTF-16, in this byte order".
- **Where it comes from:** Windows Notepad, Excel's "CSV UTF-8" export.
- **Problem:** It sticks to the first word of the file.
  ```python
  # File bytes: '\ufeffName,Age'
  open(path, encoding="utf-8").read().split(",")[0]       # '\ufeffName'  <- != 'Name'
  open(path, encoding="utf-8-sig").read().split(",")[0]   # 'Name'
  ```
- **We:** read text files with `encoding="utf-8-sig"`, and remove any remaining `\ufeff`.

### `\x00` and other control characters

- **Why they exist:** Signals from old terminals, printers, and binary formats. `\x00` (null) marks the end of a string in C.
- **Where they come from:** Corrupted files, broken PDF text layers, binary data read as text.
- **Problem:** No meaning in text, and PostgreSQL `text` columns reject `\x00` outright — the insert fails.
- **We:** remove them (keeping `\t` and `\n`).

### Rules

- ✅ Collapse repeated spaces/tabs **within a line** to one space.
- ✅ Remove spaces at the start and end of each line.
- ✅ Turn non-breaking, narrow, and thin spaces into normal spaces.
- ✅ Remove zero-width spaces, soft hyphens, BOMs, and control characters.
- ⚠️ Keep zero-width joiners (`\u200c`, `\u200d`).
- ❌ Never use `\s+` → `" "` on the whole text. `\s` includes `\n`, so it destroys paragraphs:
  ```python
  re.sub(r"\s+", " ", "Para one.\n\nPara two.")   # 'Para one. Para two.'  <- paragraphs lost
  ```

**Correct pattern:** `[^\S\n]` means "any whitespace except newline". It catches spaces, tabs, non-breaking, narrow, and thin spaces in one go:

```python
re.sub(r"[^\S\n]+", " ", text)
```

---

## 2. Newlines

**What it is:** The character that ends a line. Different systems write it differently, and in PDFs a line break doesn't always mean what you think.

**How to read this table:** the three ways a line can end, and where each one comes from.

| Line ending | Where it comes from |
|---|---|
| `\n` | Linux, macOS, PyMuPDF output |
| `\r\n` | Windows, HTTP, CSV, email |
| `\r` | old Mac files |

### `\r\n` — Carriage return + line feed

- **Why it exists:** Typewriter heritage. `\r` = move back to the start of the line, `\n` = move down one line. Windows kept both; Linux and macOS use only `\n`. HTTP headers, CSV files, and email still use `\r\n` by standard.
- **Where it comes from:** Files created on Windows, CSV exports, form submissions, API inputs.
- **Problem:** Splitting on `\n` leaves a hidden `\r` behind.
  ```python
  "Name\r\nAge".split("\n")   # ['Name\r', 'Age']   <- 'Name\r' != 'Name'
  ```
- **We:** convert `\r\n` and `\r` to `\n` **first**, so every later rule only handles one case.
  ```python
  text.replace("\r\n", "\n").replace("\r", "\n")
  # 'Line one\r\nLine two\rLine three' -> 'Line one\nLine two\nLine three'
  ```

> Python's `open(..., "r")` already does this for text files (our `file_loader.py` benefits from it). PDFs and API inputs still need it.

### `\u2028` / `\u2029` — Line separator / Paragraph separator

- **Why they exist:** Unicode's unambiguous way to say "new line" and "new paragraph", without the `\n` vs `\r\n` confusion.
- **Where they come from:** Copy-paste from Word, some JSON/JavaScript data.
- **Problem:** Some tools treat them as line breaks, others don't.
  ```python
  "a\u2028b".split("\n")      # ['a\u2028b']   <- not split
  "a\u2028b".splitlines()     # ['a', 'b']     <- split
  ```
- **We:** convert `\u2028` → `\n` and `\u2029` → `\n\n`.

### `\x0c` — Form feed

- **Why it exists:** Tells a printer "start a new page".
- **Where it comes from:** Some extractors (e.g. `pdftotext`) put it between pages. PyMuPDF does not — it already gives text per page.
- **Problem:** If you clean first, it becomes a space and page boundaries are lost.
- **We:** if an extractor uses it, split pages on `\x0c` **before** cleaning.

### Line breaks inside a sentence (PDF wrapping)

- **Why it exists:** A PDF has no idea of paragraphs. It only stores lines of text at positions on the page. When a sentence reaches the right margin, it continues on the next line.
- **Where it comes from:** Every PDF. From our handbook:
  ```text
  Each member of a hiring team \nmight have different responsibilities   <- wrapped sentence (noise)
  x. Screen candidates. \nxi. Run background checks.                    <- list items (structure)
  ```
- **Problem:** The same `\n` means "sentence continues" in the first line and "new item" in the second. A simple rule can't tell them apart (see [section 5](#5-preserving-structure)).
- **We:** keep single line breaks in the global cleaning. Join wrapped lines only when you know the document's layout.

### Blank lines (`\n\n`) — paragraph breaks — ⚠️ KEEP

- **Why it exists:** Separates paragraphs — the strongest "new idea starts here" signal in plain text.
- **Where it comes from:** PyMuPDF writes blank lines as `" \n"`. Our handbook has 246 of them. They become `"\n\n"` once trailing spaces are removed:
  ```python
  # preprocess_page_text() is our own helper (section 7) — not built-in, not in the project yet
  preprocess_page_text(" \n \nWelcome \n \nSteps may overlap. \n")
  # 'Welcome\n\nSteps may overlap.'
  ```
- **Problem:** Several blank lines in a row add nothing.
- **We:** keep paragraph breaks, reduce 3+ newlines to 2.
  ```python
  re.sub(r"\n{3,}", "\n\n", "Para one.\n\n\n\nPara two.")   # 'Para one.\n\nPara two.'
  ```

### Rules

- ✅ Convert all line endings to `\n` first.
- ✅ Convert `\u2028` / `\u2029` to `\n` / `\n\n`.
- ✅ Keep paragraph breaks (`\n\n`); reduce 3+ newlines to 2.
- ⚠️ Join wrapped lines only per document, never globally.

---

## 3. Normalization

**What it is:** Making text that *means* the same thing also *look* the same to the computer — without changing what it says.

### NFC vs NFKC

**How to read this table:** Python's `unicodedata.normalize()` offers several "forms" (modes). These are the two that matter for us.

| Normalization form | What it does | Safe to use? |
|---|---|---|
| **NFC** | Combines characters into their standard form | ✅ Always safe — use by default |
| **NFKC** | NFC + replaces "look-alike" characters | ⚠️ Can change meaning |

```python
unicodedata.normalize("NFKC", "\ufb01le")   # 'file'  ✅ (ligature fixed)
unicodedata.normalize("NFKC", "x²")         # 'x2'    ❌ (x squared became x2)
unicodedata.normalize("NFKC", "½")          # '1⁄2'   ❌ (changed form)
```

Use NFKC only if documents have no maths, units, or footnote markers. For ligatures, use a targeted replacement instead (below).

### `e` + `\u0301` — Combining accent

- **Why it exists:** Unicode can build an accented letter from parts (`e` + accent mark) or use one ready-made character (`é`). Both are valid.
- **Where it comes from:** Some keyboards, older macOS file systems (HFS+), and some PDF generators use the parts.
- **Problem:** They look identical but don't match.
  ```python
  a = "e\u0301"   # 'e' + accent mark
  b = "\u00e9"    # 'é' as one character

  len(a), len(b)                         # (2, 1)
  a == b                                 # False
  unicodedata.normalize("NFC", a) == b   # True
  ```
- **We:** apply NFC to all text.

### `ﬁ` `ﬂ` `ﬀ` `ﬃ` `ﬄ` — Ligatures

- **Why they exist:** Fonts join `f` + `i` into one shape because it looks better. PDFs often store that single shape as one character.
- **Where it comes from:** Professionally typeset PDFs — books, research papers, reports.
- **Problem:**
  ```python
  "file" in "\ufb01le"   # False  <- displays as 'file'
  ```
- **We:** replace these five characters directly (`ﬁ` → `fi`, …). This is safe — they always mean the same letters. Don't use NFKC for this, because NFKC also changes `x²`.

### `²` `½` `¹` — Superscripts and fractions — ⚠️ KEEP

- **Why they exist:** Maths (`x²`), units (`m²`), fractions (`½`), footnote markers (`policy¹`).
- **Where they come from:** Technical documents, contracts, research papers.
- **Problem:** Only if you use NFKC, which turns `x²` into `x2` and `m²` into `m2` — a different meaning.
- **We:** keep them as they are.

### `’` `“` `”` — Curly (smart) quotes

- **Why they exist:** Proper typography. Word's autocorrect replaces `'` and `"` as you type.
- **Where they come from:** Almost every Word-generated document. `employee_handbook.pdf` has 105 `’` and 22 curly double quotes.
- **Problem:** Exact keyword search misses them.
  ```python
  "don't" in "I don\u2019t know"   # False
  ```
- **We:** keep them in stored text (embeddings handle them fine). If you add keyword search, convert to straight quotes in **both** the index and the query.

### Never do these for RAG

These were popular in old keyword search engines — they made `Policy`, `policy`, and `policies` match the same index entry and kept the index small. Embedding models and LLMs need natural text, and answers quote it back to users, so these now cause damage:

**How to read this table:** each row is one old cleaning step, why it was used, and an example of how it breaks meaning today.

| Cleaning step | Why old search engines used it | What goes wrong in RAG |
|---|---|---|
| Lowercasing | match `Policy` and `policy` | `"US"` (country) becomes `"us"` |
| Removing punctuation | simpler tokens | `"3.5%"` becomes `"35"` |
| Removing stopwords | smaller index | `"must not share passwords"` becomes `"must share passwords"` |
| Stemming | match `policy` and `policies` | `"policies"` becomes `"polici"` |

### Rules

- ✅ Apply NFC to everything.
- ✅ Replace ligatures with plain letters.
- ⚠️ NFKC only for documents without maths, units, or footnotes.
- ❌ Never lowercase, remove punctuation or stopwords, or stem.

---

## 4. Empty Content

**What it is:** Pages that have no useful text. There are three different cases, and they need different handling.

**How to read this table:** each row is one kind of "empty" page, what PyMuPDF's `get_text()` returns for it, and what that means.

| Kind of empty page | What `get_text()` returns | What it means |
|---|---|---|
| Empty string | `""` | Blank page |
| Whitespace-only | `" \n \n"` | Looks non-empty, has no content |
| No extractable text | `""` + page has images | Scanned page — needs OCR |

### Blank page — `""`

- **Why it exists:** Printed documents add blank pages on purpose — so chapters start on a right-hand page, as separators, or as back covers.
- **Where it comes from:** Books, manuals, double-sided print layouts.
- **Problem:** Nothing to embed; an empty chunk wastes a database row and can match random queries.
- **We:** mark it as blank, skip it when chunking, keep it in the page list.

### Whitespace-only page — `" \n \n"`

- **Why it exists:** The page has only a logo, a picture, a decorative shape, or a page border — the extractor still outputs a few spaces and line breaks for the layout.
- **Where it comes from:** Cover pages, divider pages, full-page diagrams.
- **Problem:** Whitespace counts as "truthy" in Python, so it looks like content.
  ```python
  bool(" \n")              # True   <- `if text:` thinks this page has content
  " \n".strip() == ""      # True   <- correct check
  ```
- **We:** check with `text.strip()`, then treat it like a blank page.

### Scanned page — no extractable text

- **Why it exists:** The page is a photo of paper. It contains an image of text, not actual text characters.
- **Where it comes from:** Signed contracts, scanned forms, receipts, faxes, phone scanner apps.
- **Problem:** The page *has* content, but `get_text()` returns nothing — users will ask about it and get no answer.
- **We:** detect it and tell the user the page needs OCR.

### Correct checks

> ⚠️ These are **our own helper functions**, not built-in. They are not in the project yet — add them before using them.

```python
def is_blank_page_text(text: str) -> bool:
    return not text.strip()

def page_needs_ocr(page) -> bool:  # page = pymupdf.Page
    return not page.get_text().strip() and bool(page.get_images())
```

Results on test pages: blank page → `False`, image-only page → `True`, text page → `False`.

> Tip: a page with only `"This page intentionally left blank"` has text but no useful content. If needed, also skip pages with very little text — but still keep them in the page list.

### Rules

- ✅ Keep empty pages in the page list — page numbers must stay correct for citations.
- ✅ Skip them when chunking and embedding.
- ✅ If many pages need OCR, tell the user the PDF is scanned.
- ❌ Never re-number pages after removing empty ones.

---

## 5. Preserving Structure

**What it is:** Keeping the boundaries that tell you where one idea ends and the next begins. Chunking and citations depend on them.

### Paragraph breaks (`\n\n`)

- **Why it exists:** One paragraph = one idea.
- **Use case:** A user asks *"What is the notice period?"* The answer lives in one paragraph. If a chunk splits that paragraph in half, retrieval may return only the half without the number.
- **We:** split chunks at `\n\n` first, and only split inside a paragraph if it is too long.

### Headings

- **Why it exists:** Tells the reader which topic the following text belongs to — e.g. `Background checks`.
- **Use case:** A chunk says *"Employees get 20 days per year."* Without its heading, you can't tell whether that is leave for full-time staff or for contractors. Adding the heading to the chunk (`"Leave policy > Contractors: Employees get 20 days…"`) makes the answer correct.
- **We:** keep headings on their own lines so chunking can detect them and attach them to each chunk.

### List items

- **Why it exists:** Each item is a separate point or a numbered step.
- **Use case:** *"What is step 3 of hiring?"* only works if `x.`, `xi.`, `xii.` stay as separate lines.
- **We:** keep each list item on its own line.

### Page numbers

- **Why it exists:** Lets people find the original text.
- **Use case:** An answer that says *"(page 5)"* lets the user check it — essential for HR, legal, and finance documents.
- **We:** keep `page_number` with every chunk, and never re-number.

### Table rows

- **Why it exists:** Each row links values together — a name with its price, a plan with its limit.
- **Use case:** `Plan A  ₹500  Plan B  ₹900` merged into one line can lead the model to give Plan A's price for Plan B.
- **We:** keep one row per line, or extract tables separately with `page.find_tables()`.

### Example — a "helpful" rule that breaks structure

Rule: *"join a line to the previous one if it starts with a lowercase letter"* (to fix wrapped sentences). Run on our handbook's page 5:

```text
Input:
x. Screen candidates.
xi. Run background checks.

Each member of a hiring team
might have different responsibilities.

Output:
x. Screen candidates. xi. Run background checks.          <- ❌ list merged ('xi' starts lowercase)

Each member of a hiring team might have different responsibilities.   <- ✅ sentence fixed
```

### Example — hyphens at line ends are ambiguous

```text
employ-\nment   -> should become "employment"
Drug-\nfree     -> must stay "Drug-free"
```

### Rules

- ✅ Keep `\n\n`, headings, list lines, table rows, and page numbers.
- ⚠️ Line-joining and de-hyphenation are guesses — apply per document, never globally.
- ✅ For reliable structure, ask PyMuPDF instead of guessing:
  - `page.get_text("blocks")` — paragraph-like blocks
  - `page.get_text("dict")` — includes font sizes (helps find headings)
  - `page.find_tables()` — tables as rows and cells
  - `pymupdf4llm` — outputs Markdown with headings and lists marked

---

## 6. Trade-offs: Clean Globally vs Preserve for Chunking

**What it is:** Deciding which cleaning steps are safe for every document, and which depend on the document.

**Store two versions of each page:**

| Stored field | What it is used for |
|---|---|
| `raw_text` | Showing to users, citations — the source of truth |
| `cleaned_text` | Chunking and embeddings |

### Use cases — the same rules don't fit every document

**How to read this table:** each row is a kind of document, an example, and what you should do differently for it.

| Document type | Example | What to do differently |
|---|---|---|
| Word-generated prose | `employee_handbook.pdf` | Global cleaning + split on paragraphs is enough |
| Research paper | maths, footnotes, two columns | No NFKC (keeps `x²`); use `"blocks"` to avoid mixing columns; careful de-hyphenation |
| Invoice / price list | tables | Extract tables with `find_tables()`; never join lines |
| Scanned contract | photo of paper | OCR first — cleaning can't fix missing text |
| Hindi / Persian text | uses zero-width joiners | Never remove `\u200c` / `\u200d` |
| Book | blank pages, repeated headers/footers | Skip blank pages; remove repeated header lines per document |

### Decision table

**How to read this table:** each row is one cleaning step. The middle column says when to apply it:

- ✅ **Always** — apply to every document
- 🔒 **Preserve** — never remove this
- ⚠️ **Per document** — only when you know the document's layout
- ❌ **Never** — don't do this at all

| Cleaning step | When to apply it | Reason |
|---|---|---|
| Line endings → `\n` | ✅ Always | No meaning, one case to handle |
| NFC normalization | ✅ Always | Same text, same bytes |
| Remove zero-width space / soft hyphen / BOM / control chars | ✅ Always | Invisible noise; `\x00` also breaks PostgreSQL |
| Replace ligatures (`ﬁ` → `fi`) | ✅ Always | Same letters, fixes search |
| Collapse spaces within lines | ✅ Always | No meaning |
| Strip spaces at line ends | ✅ Always | No meaning |
| 3+ newlines → 2 | ✅ Always | Keeps paragraph breaks, drops extras |
| Mark blank pages | ✅ Always | Skip in chunking, keep page numbers |
| Keep zero-width joiners (`\u200c`, `\u200d`) | 🔒 Preserve | Needed for Hindi, Persian, emoji |
| Paragraph breaks, headings, lists, tables, pages | 🔒 Preserve | Chunk boundaries and citations |
| Join wrapped lines | ⚠️ Per document | Can merge list items |
| Remove line-end hyphens | ⚠️ Per document | Can break real hyphenated words |
| Remove repeated headers/footers | ⚠️ Per document | Needs cross-page detection |
| NFKC | ⚠️ Per document | Changes `x²`, `½` |
| Lowercase, remove punctuation/stopwords, stem | ❌ Never | Changes meaning |
| Collapse all whitespace into one line | ❌ Never | Destroys all structure |

---

## 7. Reference Implementation (not yet in the project)

> ⚠️ **This is example code to implement, not a built-in method.** `preprocess_page_text()` and `is_blank_page_text()` are custom helpers written for these notes. They do not exist in Python, PyMuPDF, or our backend yet. To use them, create a module such as `backend/src/rag_assistant/ingestion/text_preprocessing.py`, paste this code in, add tests, and call it from the ingestion pipeline.

`preprocess_page_text()` applies every "✅ Always" step, in the correct order.

```python
import re
import unicodedata

# Zero-width space, soft hyphen, byte order mark.
# Zero-width joiners (\u200c, \u200d) are deliberately NOT here: Hindi, Persian and emoji need them.
_INVISIBLE = dict.fromkeys(map(ord, "\u200b\u00ad\ufeff"), None)
# Typographic ligatures -> plain letters (safe, unlike NFKC which also turns x² into x2)
_LIGATURES = str.maketrans({"\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi", "\ufb04": "ffl"})
# Control characters except tab (\x09), newline (\x0a), vertical tab/form feed (\x0b, \x0c)
_CONTROL = re.compile(r"[\x00-\x08\x0e-\x1f\x7f]")


def preprocess_page_text(text: str) -> str:
    # 1. One line-ending style
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u2028", "\n").replace("\u2029", "\n\n")
    # 2. One Unicode form
    text = unicodedata.normalize("NFC", text)
    # 3. Remove invisible and control characters, expand ligatures
    text = text.translate(_INVISIBLE).translate(_LIGATURES)
    text = _CONTROL.sub("", text)
    # 4. Collapse whitespace within lines (keeps \n)
    text = re.sub(r"[^\S\n]+", " ", text)
    # 5. Strip spaces around line breaks
    text = re.sub(r" *\n *", "\n", text)
    # 6. Keep paragraph breaks, drop extra blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def is_blank_page_text(text: str) -> bool:
    return not text.strip()
```

**Why the order matters:**

- Line endings must be fixed before step 4. Otherwise a lone `\r` counts as whitespace and becomes a space, so the line break is lost: `"Line one\rLine two"` → `"Line one Line two"`.
- Invisible characters must be removed before step 4. Otherwise `"a \u200b b"` → `"a  b"` (two spaces) instead of `"a b"`.

**Verified examples**

**How to read this table:** the left column is text passed into `preprocess_page_text()`, the right column is exactly what it returns.

| Text passed in | What `preprocess_page_text()` returns |
|---|---|
| `"  Hello \t\u00a0 world  \r\n\r\n\r\n\u200bNext\u00a0para.  "` | `"Hello world\n\nNext para."` |
| `" \n \nWelcome \n \nSteps may overlap. \n"` | `"Welcome\n\nSteps may overlap."` |
| `"Line one\r\nLine two\rLine three"` | `"Line one\nLine two\nLine three"` |
| `"employ\u00adment"` | `"employment"` |
| `"\ufeffTitle"` | `"Title"` |
| `"a\x00b"` | `"ab"` |
| `" \n \n"` | `""` |
| `"\ufb01le \ufb02ow"` | `"file flow"` |
| `"10:30\u202fAM"` | `"10:30 AM"` |
| `"a\u2028b"` | `"a\nb"` |
| `"cafe\u0301"` | `"café"` (single `é`) |
| `"x² + ½"` | `"x² + ½"` (unchanged) |
| `"👨\u200d👩\u200d👧"` | unchanged (joiners kept) |

---

## 8. Checklist

Before sending text to chunking:

- [ ] Line endings are `\n` only
- [ ] Text is NFC-normalized
- [ ] No zero-width spaces, soft hyphens, BOMs, or control characters
- [ ] Zero-width joiners (`\u200c`, `\u200d`) kept
- [ ] Ligatures (`ﬁ`, `ﬂ`) replaced with plain letters
- [ ] Superscripts and fractions (`²`, `½`) unchanged
- [ ] No repeated spaces or trailing spaces
- [ ] Paragraph breaks (`\n\n`) still present
- [ ] Headings, list items, and table rows still on their own lines
- [ ] Blank pages are marked, not deleted
- [ ] Page numbers unchanged
- [ ] Raw text kept separately for display and citations
- [ ] Nothing lowercased, stemmed, or stripped of punctuation or stopwords
