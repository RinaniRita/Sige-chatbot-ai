import ollama
from typing import List, Optional
import logging
from ..config import OLLAMA_BASE_URL, OLLAMA_MODEL, MAX_OUTPUT_TOKENS, LLM_TEMPERATURE

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.client = ollama.Client(host=OLLAMA_BASE_URL)
        self.model = OLLAMA_MODEL

    def generate_response(self, prompt: str, context: List[str] = None, system_prompt: Optional[str] = None, **kwargs) -> str:
        """
        Generate a response using the local Ollama model.

        Args:
            prompt: The main prompt/question
            context: List of context strings from RAG retrieval
            system_prompt: Optional system prompt to guide the model's behavior
            **kwargs: Additional parameters

        Returns:
            Generated response string
        """
        try:
            # Combine context with prompt if provided
            full_prompt = prompt
            if context and len(context) > 0:
                context_str = "\n\n".join(context)
                full_prompt = (
                    f"Context:\n{context_str}\n\n"
                    f"Question: {prompt}\n\n"
                    "INSTRUCTIONS:\n"
                    "1. Use the Context above to answer the question clearly and professionally.\n"
                    "2. If the Context does NOT contain the specific information needed to answer the question (e.g., specific majors for a gender, deep personal advice), do NOT say you do not know. "
                    "Instead, state that this is a specialized matter requiring expert analysis and ask for the user's phone number so a SIGE expert can call them in 15 minutes for a 1-1 consultation.\n"
                    "3. ALWAYS prioritize directing the user to professional 1-1 support.\n"
                    "4. ANSWER ONLY IN VIETNAMESE."
                )
            else:
                full_prompt = (
                    f"Question: {prompt}\n\n"
                    "CRITICAL: You have NO context documents for this specific question. "
                    "Politely greet the user and state that for this specialized query, they need a professional 1-1 consultation. "
                    "Ask them to leave their phone number so a SIGE expert can contact them directly in 15 minutes to assist. "
                    "Keep it very short and professional. ANSWER ONLY IN VIETNAMESE."
                )

            # Prepare the messages for chat
            messages = []
            
            # Add system prompt if available
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
                
            messages.append({
                "role": "user",
                "content": full_prompt
            })

            # Generate response
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    "num_predict": MAX_OUTPUT_TOKENS,
                    "temperature": LLM_TEMPERATURE,
                    **kwargs
                }
            )

            return response["message"]["content"]

        except Exception as e:
            logger.error(f"Error generating response with Ollama: {e}")
            raise

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embeddings using Ollama (if supported by the model).

        Note: Not all Ollama models support embeddings. You might need a separate embedding service.

        Args:
            text: Text to embed

        Returns:
            List of embedding floats
        """
        try:
            # Note: This assumes the model supports embeddings
            # If not, you'll need to use a different embedding service
            response = self.client.embeddings(
                model=self.model,
                prompt=text
            )
            return response["embedding"]
        except Exception as e:
            logger.error(f"Error generating embedding with Ollama: {e}")
            # Fallback: return empty list or raise
            raise ValueError(f"Embedding generation failed: {e}")

# Global instance
llm_client = LLMClient()
