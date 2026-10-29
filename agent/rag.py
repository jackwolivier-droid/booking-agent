"""Tiny dependency-free retriever over the knowledge/ markdown files.

This is a TF-IDF cosine retriever in pure Python so the repo runs with no
extra services. It's deliberately simple.

TODO (Jack, portfolio upgrade): swap _vectorize for real embeddings (Anthropic
embeddings or a vector DB like Chroma). Keep the Retriever interface the same.
A real embedding model is what you'd point to in an interview; this keyword
version is the honest starting point.
"""
import math
import re
from pathlib import Path


def _tokenize(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def _chunk(markdown):
    """Split a markdown doc into chunks at headings / blank lines."""
    chunks, current = [], []
    for line in markdown.splitlines():
        if line.startswith("#") and current:
            chunks.append("\n".join(current).strip())
            current = [line]
        elif line.strip() == "" and current:
            current.append(line)
        else:
            current.append(line)
    if current:
        chunks.append("\n".join(current).strip())
    return [c for c in chunks if c]


class Retriever:
    def __init__(self, knowledge_dir):
        self.docs = []          # list[str] chunk text
        self.doc_tokens = []    # list[list[str]]
        self.df = {}            # document frequency per term
        self._load(Path(knowledge_dir))

    def _load(self, knowledge_dir):
        for path in sorted(knowledge_dir.glob("*.md")):
            for chunk in _chunk(path.read_text(encoding="utf-8")):
                toks = _tokenize(chunk)
                if not toks:
                    continue
                self.docs.append(chunk)
                self.doc_tokens.append(toks)
                for term in set(toks):
                    self.df[term] = self.df.get(term, 0) + 1

    def _idf(self, term):
        n = len(self.docs)
        return math.log((n + 1) / (self.df.get(term, 0) + 1)) + 1

    def _vectorize(self, tokens):
        tf = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        return {t: (c / len(tokens)) * self._idf(t) for t, c in tf.items()}

    @staticmethod
    def _cosine(a, b):
        dot = sum(a.get(t, 0) * b.get(t, 0) for t in a)
        na = math.sqrt(sum(v * v for v in a.values()))
        nb = math.sqrt(sum(v * v for v in b.values()))
        return dot / (na * nb) if na and nb else 0.0

    def search(self, query, k=2):
        if not self.docs:
            return []
        q = self._vectorize(_tokenize(query))
        scored = [
            (self._cosine(q, self._vectorize(toks)), doc)
            for toks, doc in zip(self.doc_tokens, self.docs)
        ]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scored[:k] if score > 0]
