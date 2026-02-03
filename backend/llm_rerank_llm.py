"""
LLM-based answer reranker for Pasupathy RAG system.
Uses Gemini or OpenAI to select the best answer from candidates.
"""
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

def llm_rerank(query, candidates, model_name="gemini-1.5-flash"):
    """
    Given a query and a list of (answer, score) tuples, use LLM to select the best answer.
    Returns the best answer string.
    """
    if not candidates:
        return None
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    if not GOOGLE_API_KEY:
        return candidates[0][0]  # fallback
    llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=GOOGLE_API_KEY, temperature=0.0)
    prompt = ChatPromptTemplate.from_template(
        """
        You are an expert assistant. Given a user question and several candidate answers (with optional scores), select the best answer to return to the user. Only return the answer text, not any explanation.
        
        User question: {query}
        Candidates:
        {candidates}
        """
    )
    candidates_str = "\n".join([f"- {a[0]} (score: {a[1]:.2f})" for a in candidates])
    full_prompt = prompt.format(query=query, candidates=candidates_str)
    try:
        result = llm.invoke(full_prompt)
        if hasattr(result, 'content'):
            return result.content.strip()
        return str(result).strip()
    except Exception as e:
        print(f"[llm_rerank] LLM rerank failed: {e}")
        return candidates[0][0]
