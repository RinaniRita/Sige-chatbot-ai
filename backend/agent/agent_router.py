"""
Agent Router — SIGE Education Consultant AI Agent
================================================
Uses Ollama to process user queries about SIGE programs and Taiwanese universities.
Focuses on RAG-based information retrieval.
"""

import logging
from typing import Dict, Any, List, Optional
import os

from ..services.llm_client import llm_client
from ..services.rag_service import RAGService
from ..config import OLLAMA_BASE_URL, OLLAMA_MODEL

logger = logging.getLogger(__name__)

def _load_prompt(filename: str) -> str:
    path = os.path.join(os.path.dirname(__file__), "ai_prompts", filename)
    if not os.path.exists(path):
        logger.error(f"Prompt file not found: {path}")
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# Initialize RAG service
_rag_service = RAGService()

def process_agent_query(user_input: str, chat_id: int) -> Dict[str, Any]:
    """
    Process a user query using the SIGE RAG system.
    """
    logger.info(f"[SIGE Agent] Processing query: '{user_input[:50]}...'")

    # Load prompts (re-load each time for development flexibility or cache them)
    CUSTOMER_SUPPORT_PROMPT = _load_prompt("customer_support.md")
    FALLBACK_PROMPT = _load_prompt("mini_agent_fallback.md")

    # Retrieve relevant context from the SIGE knowledge base
    rag_results = _rag_service.retrieve(user_input, top_k=4)
    context_docs = [r['content'] for r in rag_results]

    if context_docs:
        # We have RAG context — generate a grounded response
        logger.info(f"[SIGE Agent] Found {len(context_docs)} relevant context chunks")
        response_text = llm_client.generate_response(
            prompt=user_input,
            context=context_docs,
            system_prompt=CUSTOMER_SUPPORT_PROMPT,
        )
    else:
        # No relevant docs found — use safety-first fallback
        logger.info("[SIGE Agent] No RAG context found, using fallback")
        response_text = llm_client.generate_response(
            prompt=user_input,
            context=[],
            system_prompt=FALLBACK_PROMPT,
        )

    return {
        "response": response_text,
        "intent": "GENERAL",
        "tool_used": None,
        "tool_result": None,
    }
