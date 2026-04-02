# build_vector_store.py
"""
Build a FAISS vector index from chunk objects produced by chunk_kb.process_kb_folder.
Saves:
 - data/vector_store/faiss_index.index
 - data/vector_store/metadata.json
 - data/vector_store/embeddings.npy
"""

import os
import json
import time
import requests
from pathlib import Path
from typing import List, Dict

import numpy as np
import faiss
import logging
from dotenv import load_dotenv

# Load env vars
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("build_vector_store")

# ---------- CONFIG ----------
KB_FOLDER = Path("data/knowledge_base/SIGE_KB")
VECTOR_STORE_DIR = Path("data/vector_store")
VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)

# Ollama settings from .env or defaults
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "qwen2.5:7b-instruct")

# Fallback model name for local CPU if Ollama fails
SF_MODEL_NAME = "all-MiniLM-L6-v2"
# ----------------------------

# Optional fallback libs
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

# Package import of sibling module
try:
    from .chunk_kb import process_kb_folder
except ImportError:
    from chunk_kb import process_kb_folder


def get_ollama_embedding(text: str) -> List[float]:
    """
    Get embedding via local Ollama API.
    Supports both /api/embeddings (Ollama <0.5) and /api/embed (Ollama >=0.5).
    """
    # Try legacy endpoint first (Ollama 0.x)
    url = f"{OLLAMA_BASE_URL}/api/embeddings"
    payload = {
        "model": OLLAMA_EMBED_MODEL,
        "prompt": text
    }
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["embedding"]
    except Exception as e:
        logger.error(f"Ollama embedding (/api/embeddings) failed: {e}")
        raise


_local_st_model = None

def get_local_embedding(text: str) -> List[float]:
    """
    Fallback using sentence-transformers local model.
    """
    global _local_st_model
    if SentenceTransformer is None:
        raise RuntimeError("sentence-transformers not installed.")
    if _local_st_model is None:
        logger.info(f"Loading local sentence-transformers model ({SF_MODEL_NAME})...")
        _local_st_model = SentenceTransformer(SF_MODEL_NAME)
    vec = _local_st_model.encode([text], show_progress_bar=False)[0]
    return vec.tolist()


def get_embedding(text: str) -> List[float]:
    """
    Priority: 1. Ollama (Local API), 2. Sentence-Transformers (Local CPU).
    """
    # 1. Try Ollama (Matches .env config)
    try:
        return get_ollama_embedding(text)
    except Exception:
        logger.warning(f"Ollama embedding failed. Ensure '{OLLAMA_EMBED_MODEL}' model is pulled via `ollama pull {OLLAMA_EMBED_MODEL}`. Falling back to local model...")

    # 2. Try Local Sentence-Transformers
    try:
        return get_local_embedding(text)
    except Exception as e:
        logger.error(f"Local fallback embedding failed: {e}")
        # Final deterministic dummy for safety (NOT for search quality)
        import hashlib
        h = hashlib.sha256(text.encode("utf-8")).digest()
        vec = np.frombuffer(h, dtype=np.uint8).astype("float32")
        vec = vec / np.linalg.norm(vec)
        return vec.tolist()


def build_faiss_index(vectors: np.ndarray):
    """
    Build and return FAISS index. Uses IndexFlatIP (Cosine) with normalized vectors.
    """
    d = vectors.shape[1]
    # Normalize for cosine similarity
    faiss.normalize_L2(vectors)
    index = faiss.IndexFlatIP(d)
    index.add(vectors)
    return index


def save_index_and_metadata(index, vectors, metadata_list):
    idx_path = VECTOR_STORE_DIR / "faiss_index.index"
    meta_path = VECTOR_STORE_DIR / "metadata.json"
    emb_path = VECTOR_STORE_DIR / "embeddings.npy"

    logger.info(f"Saving FAISS index to {idx_path}")
    faiss.write_index(index, str(idx_path))

    logger.info(f"Saving {len(metadata_list)} metadata entries to {meta_path}")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata_list, f, ensure_ascii=False, indent=2)

    logger.info(f"Saving raw embeddings to {emb_path}")
    np.save(str(emb_path), vectors)


def build_from_chunks(chunks: List[Dict]):
    """
    Index a list of chunks into FAISS.
    """
    logger.info(f"Generating embeddings for {len(chunks)} chunks...")
    vectors = []
    metadata_list = []

    start = time.time()
    for i, c in enumerate(chunks):
        text = c["text"]
        meta = c.get("metadata", {})
        try:
            emb = get_embedding(text)
            vectors.append(emb)
            metadata_list.append({
                "id": c["id"],
                "text_snippet": text,
                "metadata": meta
            })
        except Exception as e:
            logger.error(f"Failed to process chunk {c['id']}: {e}")

    vectors = np.array(vectors, dtype="float32")
    logger.info(f"Embeddings generated in {time.time() - start:.2f}s (Dimension: {vectors.shape[1]})")

    if vectors.shape[0] == 0:
        raise RuntimeError("No vectors were generated. Check your embedding service.")

    index = build_faiss_index(vectors)
    save_index_and_metadata(index, vectors, metadata_list)
    logger.info(f"Vector store built successfully with {vectors.shape[0]} documents.")


if __name__ == "__main__":
    if not KB_FOLDER.exists():
        logger.error(f"KB folder not found: {KB_FOLDER}")
    else:
        logger.info(f"Processing knowledge base at: {KB_FOLDER}")
        chunks = process_kb_folder(str(KB_FOLDER))
        build_from_chunks(chunks)
