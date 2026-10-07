"""Knowledge base lookup tool scanning internal documentation markdown files."""

from pathlib import Path
import re
from typing import List, Tuple
from langchain_core.tools import tool
from src.config import settings


def _load_kb_documents(kb_dir: Path) -> List[Tuple[str, str]]:
    """Loads all markdown files from the knowledge base directory."""
    docs = []
    if not kb_dir.exists():
        return docs

    for file_path in kb_dir.glob("*.md"):
        try:
            content = file_path.read_text(encoding="utf-8")
            docs.append((file_path.name, content))
        except Exception:
            continue
    return docs


def _score_document(query: str, doc_name: str, doc_content: str) -> float:
    """Calculates a simple lexical/relevancy match score between query and document."""
    query_terms = [t.lower() for t in re.findall(r"\w+", query) if len(t) > 2]
    if not query_terms:
        return 0.0

    content_lower = doc_content.lower()
    score = 0.0

    # Boost title/header matches
    headers = [line.lower() for line in doc_content.splitlines() if line.startswith("#")]
    for term in query_terms:
        for header in headers:
            if term in header:
                score += 3.0

    # Body word frequency
    for term in query_terms:
        matches = content_lower.count(term)
        if matches > 0:
            score += min(matches, 5) * 1.0

    # Phrase match bonus
    if query.lower() in content_lower:
        score += 8.0

    return score


@tool
def lookup_knowledge_base(query: str) -> str:
    """Searches internal company knowledge base and runbooks for policies, troubleshooting guides, and FAQs.

    Args:
        query: Search keywords or question regarding billing holds, refunds, outages, macOS appearance bugs, etc.

    Returns:
        Relevant policy excerpts and troubleshooting steps, or a notice if no documentation was found.
    """
    docs = _load_kb_documents(settings.kb_dir)
    if not docs:
        return "Knowledge base directory is empty or not accessible."

    scored_docs = []
    for doc_name, content in docs:
        score = _score_document(query, doc_name, content)
        if score > 2.0:
            scored_docs.append((score, doc_name, content))

    if not scored_docs:
        return (
            f"No relevant documentation found in internal knowledge base for query: '{query}'. "
            "This may be an unsupported capability, an unreleased feature, or an uncatalogued issue."
        )

    # Sort by score descending and take the top match
    scored_docs.sort(key=lambda x: x[0], reverse=True)
    best_score, best_name, best_content = scored_docs[0]

    # Return trimmed document excerpt
    lines = best_content.splitlines()
    excerpt = "\n".join(lines[:45])  # Cap length to prevent context explosion
    return f"[Source: {best_name}]\n{excerpt}"
