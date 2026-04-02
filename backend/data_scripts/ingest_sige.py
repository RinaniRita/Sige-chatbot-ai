# ingest_sige.py
"""
Orchestrator for SIGE KB ingestion.
Reads the structured SIGE Markdown and builds the FAISS vector store.
"""

from pathlib import Path
import logging
import sys
import os

# Ensure backend can be imported
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.data_scripts.chunk_kb import process_kb_folder
from backend.data_scripts.build_vector_store import build_from_chunks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingest_sige")

KB_ROOT = Path("data/knowledge_base/SIGE_KB")

if __name__ == "__main__":
    if not KB_ROOT.exists():
        logger.error("SIGE KB root not found: %s", KB_ROOT)
        sys.exit(1)

    logger.info("Starting ingestion for SIGE KB: %s", KB_ROOT)
    
    # process_kb_folder will find all .md files in SIGE_KB
    chunks = process_kb_folder(str(KB_ROOT))
    logger.info("Chunks prepared: %d", len(chunks))

    if len(chunks) == 0:
        logger.error("No chunks found. Check your SIGE_KB folder contents.")
        sys.exit(1)

    logger.info("Building SIGE vector store...")
    build_from_chunks(chunks)
    logger.info("Ingestion complete. Vector store saved to data/vector_store/")
