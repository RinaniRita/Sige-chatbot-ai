import os
import json
import logging
import requests
import numpy as np
import faiss
from typing import List
from dotenv import load_dotenv

from ..config import (
    OLLAMA_BASE_URL,
    OLLAMA_EMBEDDING_MODEL,
    VECTOR_STORE_PATH,
    FAISS_INDEX_FILE,
    METADATA_FILE,
)

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

def get_ollama_embedding(text: str, model: str, base_url: str) -> List[float]:
    """
    Get embedding via local Ollama API.
    Handles legacy /api/embeddings and modern /api/embed endpoints.
    """
    # 1. Try Modern Endpoint (Ollama >= 0.1.33)
    try:
        url = f"{base_url}/api/embed"
        payload = {"model": model, "input": text}
        response = requests.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            if "embeddings" in data:
                return data["embeddings"][0]
    except Exception:
        pass

    # 2. Try Legacy Endpoint (Ollama < 0.1.33)
    url = f"{base_url}/api/embeddings"
    payload = {"model": model, "prompt": text}
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["embedding"]
    except Exception as e:
        logger.error(f"Ollama embedding failure in RAG service: {e}")
        raise

class RAGService:
    def __init__(
        self,
        embedding_model: str = OLLAMA_EMBEDDING_MODEL,
        vector_store_path: str = VECTOR_STORE_PATH,
        base_url: str = OLLAMA_BASE_URL
    ):
        """
        Initialize RAG service using local Ollama embeddings and FAISS index.
        """
        try:
            self.vector_store_path = vector_store_path
            self.model_name = embedding_model
            self.base_url = base_url
            
            os.makedirs(self.vector_store_path, exist_ok=True)

            # Lazy load index and metadata
            self.index = None
            self.metadata: List[dict] = []
            self.documents: List[str] = []
            
            self._load_vector_store()
            
            # 3. Eagerly load fallback model to prevent lag on first failure
            self.fallback_model = None
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Pre-loading fallback embedding model (all-MiniLM-L6-v2) for efficiency...")
                self.fallback_model = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception as e:
                logger.warning(f"Could not pre-load fallback model: {e}")

            logger.info(
                f"RAG service initialized with model: {embedding_model}, "
                f"store: {self.vector_store_path}"
            )
            
            # 4. Perform a warmup call to Ollama (if available)
            self.warmup()
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            raise

    def get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding using Ollama.
        """
        # 1. Try local Ollama
        try:
            vec = get_ollama_embedding(text, self.model_name, self.base_url)
            return np.array(vec, dtype=np.float32)
        except Exception:
            logger.warning(f"Ollama embedding failed for retrieval. trying library fallback...")
            
        # 2. Fallback to pre-loaded local CPU model
        if self.fallback_model:
            return self.fallback_model.encode([text], show_progress_bar=False)[0].astype(np.float32)
        
        # 3. Last resort dummy
        return np.zeros(384, dtype=np.float32)

    def warmup(self):
        """Warm up the embedding engine by performing a dummy call."""
        logger.info("🔥 Warming up embedding engine...")
        try:
            self.get_embedding("warmup")
            logger.info("✅ Embedding engine warmed up.")
        except Exception as e:
            logger.warning(f"Warmup failed (this is usually okay if Ollama is still starting): {e}")

    def _load_vector_store(self):
        """Load existing vector store if available."""
        index_path = os.path.join(self.vector_store_path, FAISS_INDEX_FILE)
        metadata_path = os.path.join(self.vector_store_path, METADATA_FILE)

        if os.path.exists(index_path) and os.path.exists(metadata_path):
            try:
                # Load FAISS index
                self.index = faiss.read_index(index_path)

                # Load metadata
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata_list = json.load(f)
                    self.metadata = metadata_list
                    self.documents = [item.get('text_snippet', '') for item in metadata_list]

                logger.info(f"Loaded vector store with {self.index.ntotal} vectors")
            except Exception as e:
                logger.warning(f"Failed to load vector store: {e}")
        else:
            logger.info("No existing vector store found. Please run the ingestion script.")

    def retrieve(self, query: str, top_k: int = 4, threshold: float = 0.5) -> List[dict]:
        """
        Retrieve relevant documents for a query.
        For Cosine Similarity (IndexFlatIP with normalized vectors), scores are 
        dot products in range [0, 1]. A threshold of 0.5 is reasonable.
        """
        if not self.index or self.index.ntotal == 0:
            logger.warning("Vector store is empty or not loaded.")
            return []
            
        try:
            # Generate query embedding
            query_emb = self.get_embedding(query).reshape(1, -1)
            
            # Normalize for Cosine Similarity (Inner Product)
            faiss.normalize_L2(query_emb)
            
            # Search
            distances, indices = self.index.search(query_emb, min(top_k, self.index.ntotal))

            results = []
            for dist, idx in zip(distances[0], indices[0]):
                # In IndexFlatIP, distance is INNER PRODUCT (1.0 = identical)
                if idx < len(self.documents) and dist >= threshold:
                    results.append({
                        'content': self.documents[idx],
                        'score': float(dist),
                        'metadata': self.metadata[idx]
                    })

            logger.info(f"Retrieved {len(results)} docs for query: {query[:50]}...")
            return results
        except Exception as e:
            logger.error(f"Failed to retrieve documents: {e}")
            return []

    def get_stats(self) -> dict:
        """Get statistics."""
        return {
            'total_documents': len(self.documents),
            'index_size': self.index.ntotal if self.index else 0,
            'model': self.model_name
        }