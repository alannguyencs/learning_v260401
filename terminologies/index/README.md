# terminologies/index

Indexing + search for the terminology notes under `terminologies/notes/`.
Two small, dependency-free (stdlib-only) Python tools, each with a CLI and
tests. Modeled on the `catalog/index` BM25 + mapping pattern.

## Files

| File | What it is |
| --- | --- |
| `bm25.py` | BM25 inverted index over two corpora: `notes` (note bodies) and `terminologies` (glossary pages). |
| `notes.json` | Persisted BM25 index for the **notes** corpus (per-note length + term frequencies). |
| `terminologies.json` | Persisted BM25 index for the **terminologies** corpus (glossary pages) — powers duplicate detection. |
| `mapping.py` | Bidirectional **note ↔ terminology** map, parsed from each note's `### Key terminologies` section. |
| `notes_terminologies_mapping.json` | Persisted mapping, compact form `{ "<note>.md": ["Term", ...] }`. |
| `index.md` | **Auto-generated** master list of every terminology, each linked to its glossary page. |
| `../glossary/<slug>.md` | **Auto-generated**, standalone one page per terminology (title + definition only, no note link). |
| `test_bm25.py`, `test_mapping.py` | pytest suites for both tools. |

## BM25 search (`bm25.py`)

Two corpora, selected with `--corpus` (default `notes`):

| Corpus | Folder indexed | Index file | Use |
| --- | --- | --- | --- |
| `notes` | `terminologies/notes/` | `notes.json` | find a note by topic |
| `terminologies` | `terminologies/glossary/` | `terminologies.json` | duplicate detection over terms |

```bash
# notes corpus (default)
python3 terminologies/index/bm25.py rebuild                 # index all notes
python3 terminologies/index/bm25.py add    <note.md>        # index one note
python3 terminologies/index/bm25.py edit   <note.md>        # re-index after edits
python3 terminologies/index/bm25.py remove <note.md>
python3 terminologies/index/bm25.py search "kv cache paging" [--top-k N]

# terminologies corpus (glossary pages) — dedup backbone
python3 terminologies/index/bm25.py rebuild --corpus terminologies
python3 terminologies/index/bm25.py search "key value cache" --corpus terminologies
```

Standard BM25 (k1=1.5, b=0.75). Tokenizer lowercases, strips markdown-link
URLs and stopwords. Documents are keyed by project-root-relative path. The
`terminologies` corpus is derived from the (generated) glossary, so rebuild it
after the glossary changes; the `terminology-indexing` skill does this around
its duplicate check.

## Note ↔ terminology mapping (`mapping.py`)

```bash
python3 terminologies/index/mapping.py rebuild              # re-parse all notes + regen index.md + glossary
python3 terminologies/index/mapping.py sync   <note.md>     # re-parse one note (+ regen index.md + glossary)
python3 terminologies/index/mapping.py remove <note.md>     # drop a note (+ regen index.md + glossary)
python3 terminologies/index/mapping.py list                # master list of terminologies
python3 terminologies/index/mapping.py glossary            # regenerate per-term pages only
python3 terminologies/index/mapping.py terminologies <note.md>     # terms defined in a note
python3 terminologies/index/mapping.py notes  "<exact terminology>"  # notes that define a term
```

The parser reads the `### Key terminologies` section and takes the first
**bold** span of each `- **Term** — definition` bullet as the term name (the
text after the dash becomes the definition shown in the glossary), so keep
that bullet format in notes.

## Glossary (`terminologies/glossary/`)

`mapping.py` generates one **standalone** `<slug>.md` page per terminology —
just the term as an H1 title and its definition(s). The pages carry **no link
back to any note** and no generator marker: the note ↔ terminology
relationship lives solely in `notes_terminologies_mapping.json`. Definitions
are read from the defining notes only at generation time.

The folder is **generator-owned** and kept in sync by every `rebuild` /
`sync` / `remove` (and the standalone `glossary` command): pages for terms
that no longer exist — and any other stray `.md` — are pruned, so don't keep
hand-written files here. To change a definition, edit the source note's
`### Key terminologies` bullet and re-sync.

When a term is defined by **more than one note**, `mapping.py` mechanically
lists each *distinct* definition as its own bullet (identical strings collapse
to one). To get a single **merged** definition instead — common for general
concepts like *dot product* or *softmax* that several notes define from their
own angle — use the `terminology-indexing` skill: it synthesizes one combined
definition and writes that same text into every defining note's bullet, so the
generated page renders one merged entry.

## Tests

```bash
cd terminologies/index && python3 -m pytest -q
```
