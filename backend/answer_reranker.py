"""
Answer reranker module for Pasupathy RAG system.
Uses a simple scoring heuristic to re-rank candidate answers.
Can be extended to use an LLM for re-ranking.
"""

def rerank_answers(query, answers):
    """
    Rerank a list of (answer, score) tuples using LLM if available, fallback to score-based.
    Returns the best answer.
    """
    if not answers:
        return None
    try:
        from llm_rerank_llm import llm_rerank
        return llm_rerank(query, answers)
    except Exception as e:
        print(f"[answer_reranker] LLM rerank unavailable: {e}")
    # Fallback: Sort by score descending
    answers = sorted(answers, key=lambda x: x[1], reverse=True)
    return answers[0][0]
