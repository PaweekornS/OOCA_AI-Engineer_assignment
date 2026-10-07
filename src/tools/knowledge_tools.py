"""Hybrid Search Knowledge Base Engine: Markdown Section Chunking + BM25 + Dense Embeddings + RRF.

Implements Reciprocal Rank Fusion (RRF) combining sparse lexical search (Okapi BM25)
with dense semantic search (OpenAI text-embedding-3-small).
"""

from dataclasses import dataclass
import math
from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple
from langchain_core.tools import tool
from src.config import settings


@dataclass
class KBChunk:
    """An atomic document section chunk extracted from a Markdown runbook/policy."""

    chunk_id: str
    doc_name: str
    section_title: str
    content: str

    @property
    def full_text(self) -> str:
        return f"{self.section_title}\n{self.content}"


class MarkdownChunker:
    """Splits Markdown documents into structured section-level chunks."""

    @staticmethod
    def chunk_document(doc_name: str, raw_text: str) -> List[KBChunk]:
        chunks: List[KBChunk] = []
        lines = raw_text.splitlines()

        current_title = "Overview"
        current_lines: List[str] = []
        chunk_idx = 0

        for line in lines:
            if line.startswith("## "):
                if current_lines:
                    content = "\n".join(current_lines).strip()
                    if len(content) > 30:
                        chunks.append(
                            KBChunk(
                                chunk_id=f"{doc_name}#{chunk_idx}",
                                doc_name=doc_name,
                                section_title=current_title,
                                content=content,
                            )
                        )
                        chunk_idx += 1
                current_title = line.replace("## ", "").strip()
                current_lines = [line]
            else:
                current_lines.append(line)

        if current_lines:
            content = "\n".join(current_lines).strip()
            if len(content) > 30:
                chunks.append(
                    KBChunk(
                        chunk_id=f"{doc_name}#{chunk_idx}",
                        doc_name=doc_name,
                        section_title=current_title,
                        content=content,
                    )
                )

        return chunks


class BM25Retriever:
    """Okapi BM25 sparse lexical search implementation."""

    def __init__(self, chunks: List[KBChunk], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self.doc_len = []
        self.avgdl = 0.0
        self.doc_freqs: Dict[str, int] = {}
        self.corpus_size = len(chunks)
        self.tokenized_corpus = []

        self._build_index()

    @staticmethod
    def tokenize(text: str) -> List[str]:
        # Support alphanumeric tokens in both English and Thai script
        return [t.lower() for t in re.findall(r"[\u0e00-\u0e7f\w]+", text) if len(t) > 1]

    def _build_index(self):
        total_len = 0
        for chunk in self.chunks:
            tokens = self.tokenize(chunk.full_text)
            self.tokenized_corpus.append(tokens)
            self.doc_len.append(len(tokens))
            total_len += len(tokens)

            # Document frequency
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1

        self.avgdl = (total_len / self.corpus_size) if self.corpus_size > 0 else 0.0

    def score(self, query: str) -> List[float]:
        query_tokens = self.tokenize(query)
        scores = [0.0] * self.corpus_size
        if not query_tokens or self.corpus_size == 0:
            return scores

        for token in query_tokens:
            df = self.doc_freqs.get(token, 0)
            if df == 0:
                continue

            # Standard Robertson-Spärck Jones IDF formula
            idf = math.log((self.corpus_size - df + 0.5) / (df + 0.5) + 1.0)

            for idx, doc_tokens in enumerate(self.tokenized_corpus):
                tf = doc_tokens.count(token)
                if tf > 0:
                    numerator = tf * (self.k1 + 1.0)
                    denominator = tf + self.k1 * (
                        1.0 - self.b + self.b * (self.doc_len[idx] / self.avgdl)
                    )
                    scores[idx] += idf * (numerator / denominator)

        return scores


class DenseEmbeddingsRetriever:
    """Dense semantic retriever using OpenAI embeddings."""

    def __init__(self, chunks: List[KBChunk]):
        self.chunks = chunks
        self.embeddings_cache: Optional[List[List[float]]] = None
        self._client = None

    def _get_client(self):
        if self._client is None and settings.openai_api_key:
            from langchain_openai import OpenAIEmbeddings

            self._client = OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=settings.openai_api_key,
            )
        return self._client

    def _ensure_cache(self):
        client = self._get_client()
        if client and self.embeddings_cache is None and self.chunks:
            try:
                texts = [c.full_text for c in self.chunks]
                self.embeddings_cache = client.embed_documents(texts)
            except Exception:
                self.embeddings_cache = None

    @staticmethod
    def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def score(self, query: str) -> List[float]:
        self._ensure_cache()
        if not self.embeddings_cache or not self.chunks:
            return [0.0] * len(self.chunks)

        client = self._get_client()
        if not client:
            return [0.0] * len(self.chunks)

        try:
            query_embedding = client.embed_query(query)
            return [
                self._cosine_similarity(query_embedding, doc_emb)
                for doc_emb in self.embeddings_cache
            ]
        except Exception:
            return [0.0] * len(self.chunks)


class HybridSearchEngine:
    """Combines BM25 and Dense Embeddings using Reciprocal Rank Fusion (RRF)."""

    def __init__(self, kb_dir: Path, rrf_k: int = 60):
        self.kb_dir = kb_dir
        self.rrf_k = rrf_k
        self.chunks: List[KBChunk] = []
        self.bm25: Optional[BM25Retriever] = None
        self.dense: Optional[DenseEmbeddingsRetriever] = None

        self._load_corpus()

    def _load_corpus(self):
        self.chunks = []
        if not self.kb_dir.exists():
            return

        for file_path in self.kb_dir.glob("*.md"):
            try:
                raw_text = file_path.read_text(encoding="utf-8")
                self.chunks.extend(MarkdownChunker.chunk_document(file_path.name, raw_text))
            except Exception:
                continue

        if self.chunks:
            self.bm25 = BM25Retriever(self.chunks)
            self.dense = DenseEmbeddingsRetriever(self.chunks)

    def search(self, query: str, top_k: int = 2) -> List[Tuple[float, KBChunk]]:
        if not self.chunks or not self.bm25:
            return []

        # 1. Sparse Scores (BM25)
        bm25_scores = self.bm25.score(query)

        # 2. Dense Scores (Embeddings)
        dense_scores = self.dense.score(query) if self.dense else [0.0] * len(self.chunks)

        # Check if query has any relevance at all
        max_bm25 = max(bm25_scores) if bm25_scores else 0.0
        max_dense = max(dense_scores) if dense_scores else 0.0

        # Knowledge gap threshold: requires meaningful lexical match (>= 4.0) OR strong semantic signal (>= 0.40)
        if max_bm25 < 4.0 and max_dense < 0.40:
            return []

        # 3. Compute RRF Ranks
        # Sort indices by BM25 score descending
        bm25_ranked = sorted(range(len(self.chunks)), key=lambda i: bm25_scores[i], reverse=True)
        dense_ranked = sorted(range(len(self.chunks)), key=lambda i: dense_scores[i], reverse=True)

        bm25_rank_map = {idx: rank + 1 for rank, idx in enumerate(bm25_ranked)}
        dense_rank_map = {idx: rank + 1 for rank, idx in enumerate(dense_ranked)}

        # RRF formula: Score(d) = 1/(k + rank_bm25) + 1/(k + rank_dense)
        rrf_scores = []
        has_dense = max_dense > 0.0

        for idx, chunk in enumerate(self.chunks):
            # Only consider documents with positive lexical match OR semantic signal
            if bm25_scores[idx] <= 0.0 and dense_scores[idx] < 0.35:
                continue

            bm25_component = 1.0 / (self.rrf_k + bm25_rank_map[idx]) if bm25_scores[idx] > 0.0 else 0.0
            dense_component = 1.0 / (self.rrf_k + dense_rank_map[idx]) if has_dense else 0.0

            total_rrf = bm25_component + dense_component
            rrf_scores.append((total_rrf, chunk))

        rrf_scores.sort(key=lambda x: x[0], reverse=True)
        return rrf_scores[:top_k]


# Singleton engine instance
_ENGINE: Optional[HybridSearchEngine] = None


def get_search_engine() -> HybridSearchEngine:
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = HybridSearchEngine(settings.kb_dir)
    return _ENGINE


@tool
def lookup_knowledge_base(query: str) -> str:
    """Searches internal company knowledge base and runbooks using Hybrid Search (BM25 + Semantic Embeddings + RRF).

    Args:
        query: Search keywords or question regarding billing holds, refund policies, Sev-1 outages, macOS appearance bugs, etc.

    Returns:
        Relevant runbook sections and troubleshooting steps, or an explicit notice if no documentation was found.
    """
    engine = get_search_engine()
    results = engine.search(query, top_k=3)

    if not results:
        return (
            f"No relevant documentation found in internal knowledge base for query: '{query}'. "
            "This may be an unsupported capability, an unreleased feature, or an uncatalogued issue."
        )

    formatted_chunks = []
    for score, chunk in results:
        formatted_chunks.append(
            f"[Source: {chunk.doc_name} > {chunk.section_title}]\n{chunk.content}"
        )

    return "\n\n---\n\n".join(formatted_chunks)
