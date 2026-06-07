#!/usr/bin/env python3
"""BM25 inverted index over two terminology corpora.

  notes         -> terminologies/notes/    -> notes.json
                   (full note bodies; what `terminology-create` writes)
  terminologies -> terminologies/glossary/ -> terminologies.json
                   (one standalone term page each; powers dedup detection)

Documents are keyed by their project-root-relative path. The corpus is chosen
with ``--corpus`` (default ``notes``), so existing single-corpus usage is
unchanged.

Storage is intentionally minimal — only per-document length and term
frequencies. Corpus-level stats (avgdl, document frequency, IDF) are derived
on demand so the on-disk file cannot drift from reality.

Usage:
    python terminologies/index/bm25.py add <path>    [--corpus C]
    python terminologies/index/bm25.py edit <path>   [--corpus C]
    python terminologies/index/bm25.py remove <path> [--corpus C]
    python terminologies/index/bm25.py search "<query>" [--top-k N] [--corpus C]
    python terminologies/index/bm25.py rebuild       [--corpus C]
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Dict, FrozenSet, Iterable, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INDEX_DIR = Path(__file__).resolve().parent

# Two corpora, each a flat folder of markdown docs with its own index file:
#   notes         -> terminologies/notes/    (full note bodies)  -> notes.json
#   terminologies -> terminologies/glossary/ (one term per page) -> terminologies.json
# The terminologies corpus powers duplicate detection: searching it with a new
# term's text surfaces existing terminologies that mean the same thing.
CORPORA: Dict[str, Tuple[str, str]] = {
    "notes": ("terminologies/notes", "notes.json"),
    "terminologies": ("terminologies/glossary", "terminologies.json"),
}
DEFAULT_CORPUS = "notes"

# Standard BM25 hyperparameters
K1 = 1.5
B = 0.75

STOPWORDS: FrozenSet[str] = frozenset(
    """
a an and any are as at be been being but by can did do does for from has have
having he her here him his how if in into is it its itself me more most my of
on once only or other our out over own same she should so some such than that
the their them then there these they this those through to too under until
up upon us was we were what when where which while who whom why will with
would you your yours
""".split()
)

TOKEN_RE = re.compile(r"[a-z0-9]+")
# Replace [text](url) with text so URLs don't pollute the term frequencies.
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")


def tokenize(text: str) -> List[str]:
    text = MD_LINK_RE.sub(r"\1", text)
    return [
        t for t in TOKEN_RE.findall(text.lower()) if len(t) > 1 and t not in STOPWORDS
    ]


def _corpus_root(corpus: str = DEFAULT_CORPUS) -> Path:
    # Resolve at call time so tests can monkeypatch PROJECT_ROOT.
    return PROJECT_ROOT / CORPORA[corpus][0]


def _index_path(corpus: str = DEFAULT_CORPUS) -> Path:
    return INDEX_DIR / CORPORA[corpus][1]


def _normalize_path(path: str) -> str:
    p = Path(path)
    if p.is_absolute():
        try:
            p = p.resolve().relative_to(PROJECT_ROOT)
        except ValueError as exc:
            raise SystemExit(f"path is outside project root: {path}") from exc
    return p.as_posix()


def _read_doc(rel_path: str) -> str:
    full = PROJECT_ROOT / rel_path
    if not full.exists():
        raise SystemExit(f"file not found: {full}")
    return full.read_text(encoding="utf-8")


class BM25Index:
    """In-memory BM25 index with JSON persistence."""

    def __init__(
        self,
        k1: float = K1,
        b: float = B,
        documents: Dict[str, dict] | None = None,
    ) -> None:
        self.k1 = k1
        self.b = b
        # documents[rel_path] = {"length": int, "term_freq": {term: count}}
        self.documents: Dict[str, dict] = documents or {}

    # ---- persistence ---------------------------------------------------

    @classmethod
    def load(cls, index_path: Path | None = None) -> "BM25Index":
        index_path = index_path or _index_path()
        if not index_path.exists():
            return cls()
        data = json.loads(index_path.read_text(encoding="utf-8"))
        cfg = data.get("config", {})
        return cls(
            k1=cfg.get("k1", K1),
            b=cfg.get("b", B),
            documents=data.get("documents", {}),
        )

    def save(self, index_path: Path | None = None) -> None:
        index_path = index_path or _index_path()
        index_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "config": {"k1": self.k1, "b": self.b},
            "documents": dict(sorted(self.documents.items())),
        }
        index_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    # ---- mutators ------------------------------------------------------

    def add(self, rel_path: str) -> str:
        rel_path = _normalize_path(rel_path)
        tokens = tokenize(_read_doc(rel_path))
        if not tokens:
            raise SystemExit(f"no indexable tokens in {rel_path}")
        tf: Dict[str, int] = {}
        for tok in tokens:
            tf[tok] = tf.get(tok, 0) + 1
        self.documents[rel_path] = {"length": len(tokens), "term_freq": tf}
        return rel_path

    def edit(self, rel_path: str) -> str:
        # Same effect as add — re-reads the file and overwrites the entry.
        return self.add(rel_path)

    def remove(self, rel_path: str) -> str:
        rel_path = _normalize_path(rel_path)
        if rel_path not in self.documents:
            raise SystemExit(f"not in index: {rel_path}")
        del self.documents[rel_path]
        return rel_path

    # ---- corpus stats --------------------------------------------------

    @property
    def doc_count(self) -> int:
        return len(self.documents)

    @property
    def avgdl(self) -> float:
        if not self.documents:
            return 0.0
        total = sum(d["length"] for d in self.documents.values())
        return total / len(self.documents)

    def doc_freq(self, term: str) -> int:
        return sum(1 for d in self.documents.values() if term in d["term_freq"])

    # ---- search --------------------------------------------------------

    def _idf(self, term: str) -> float:
        n_q = self.doc_freq(term)
        if n_q == 0:
            return 0.0
        # Robertson-Spärck Jones IDF, smoothed with the standard +1 to keep
        # it non-negative for terms appearing in more than half the corpus.
        return math.log((self.doc_count - n_q + 0.5) / (n_q + 0.5) + 1.0)

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        terms = tokenize(query)
        if not terms or not self.documents:
            return []
        avgdl = self.avgdl
        idf_cache = {t: self._idf(t) for t in set(terms)}
        scores: List[Tuple[str, float]] = []
        for path, doc in self.documents.items():
            length = doc["length"]
            tf = doc["term_freq"]
            score = 0.0
            for term in terms:
                f = tf.get(term, 0)
                if f == 0:
                    continue
                denom = f + self.k1 * (1 - self.b + self.b * length / avgdl)
                score += idf_cache[term] * (f * (self.k1 + 1)) / denom
            if score > 0:
                scores.append((path, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


# ---- CLI ---------------------------------------------------------------


def _cmd_add(args: argparse.Namespace) -> None:
    path = _index_path(args.corpus)
    idx = BM25Index.load(path)
    rel = idx.add(args.path)
    idx.save(path)
    print(f"[{args.corpus}] indexed {rel}")


def _cmd_edit(args: argparse.Namespace) -> None:
    path = _index_path(args.corpus)
    idx = BM25Index.load(path)
    rel = idx.edit(args.path)
    idx.save(path)
    print(f"[{args.corpus}] updated {rel}")


def _cmd_remove(args: argparse.Namespace) -> None:
    path = _index_path(args.corpus)
    idx = BM25Index.load(path)
    rel = idx.remove(args.path)
    idx.save(path)
    print(f"[{args.corpus}] removed {rel}")


def _cmd_search(args: argparse.Namespace) -> None:
    idx = BM25Index.load(_index_path(args.corpus))
    hits = idx.search(args.query, top_k=args.top_k)
    if not hits:
        print("(no matches)")
        return
    path_w = max(len(p) for p, _ in hits)
    for path, score in hits:
        print(f"{path:<{path_w}}  {score:.4f}")


def _cmd_rebuild(args: argparse.Namespace) -> None:
    idx = BM25Index()
    paths = sorted(_corpus_root(args.corpus).glob("*.md"))
    for p in paths:
        idx.add(p.relative_to(PROJECT_ROOT).as_posix())
    idx.save(_index_path(args.corpus))
    print(f"[{args.corpus}] indexed {len(paths)} documents")


def _add_corpus_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--corpus",
        choices=sorted(CORPORA),
        default=DEFAULT_CORPUS,
        help="which index to operate on (default: notes)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="BM25 index over terminology notes / terminologies."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="add a document to the index")
    p_add.add_argument("path", help="project-root-relative or absolute path")
    p_add.set_defaults(func=_cmd_add)

    p_edit = sub.add_parser("edit", help="re-read and replace a document")
    p_edit.add_argument("path")
    p_edit.set_defaults(func=_cmd_edit)

    p_rm = sub.add_parser("remove", help="remove a document from the index")
    p_rm.add_argument("path")
    p_rm.set_defaults(func=_cmd_remove)

    p_s = sub.add_parser("search", help="search top-k documents for a query")
    p_s.add_argument("query")
    p_s.add_argument("--top-k", type=int, default=5)
    p_s.set_defaults(func=_cmd_search)

    p_rb = sub.add_parser("rebuild", help="rebuild the index from disk")
    p_rb.set_defaults(func=_cmd_rebuild)

    for p in (p_add, p_edit, p_rm, p_s, p_rb):
        _add_corpus_arg(p)

    return parser


def main(argv: Iterable[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
