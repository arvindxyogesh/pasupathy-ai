"""
Semantic chunking utility for splitting text into topic/paragraph-based chunks for RAG.
Uses simple heuristics and can be extended to use ML models.
"""
import re

def semantic_chunk_text(text, max_length=500, overlap=100):
    # Split by double newlines (paragraphs)
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) < max_length:
            current += ("\n" if current else "") + para
        else:
            if current:
                chunks.append(current.strip())
            current = para
    if current:
        chunks.append(current.strip())
    # Add overlap
    if overlap > 0 and len(chunks) > 1:
        overlapped = []
        for i, chunk in enumerate(chunks):
            if i == 0:
                overlapped.append(chunk)
            else:
                prev = chunks[i-1]
                overlap_text = prev[-overlap:] if len(prev) > overlap else prev
                overlapped.append(overlap_text + "\n" + chunk)
        return overlapped
    return chunks
