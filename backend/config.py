import os
from dotenv import load_dotenv

# Load environment variables from .env file (root of ai-agent-cs)
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=env_path, override=True)

# --------------------------------------------------
# Ollama configuration
# --------------------------------------------------
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b-instruct")
# Default matches .env.example (nomic-embed-text) so it "fits" out of the box
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

# --------------------------------------------------
# RAG settings
# --------------------------------------------------
TOP_K = int(os.getenv("TOP_K", 4))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", 0.30))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.75))
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", 2048))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.4))
# Chunking settings
# --------------------------------------------------
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 500))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 80))

# --------------------------------------------------
# Vector store settings
# --------------------------------------------------
VECTOR_STORE_PATH = os.getenv("VECTOR_STORE_PATH", "data/vector_store/")
FAISS_INDEX_FILE = os.getenv("FAISS_INDEX_FILE", "faiss_index.index")
METADATA_FILE = os.getenv("METADATA_FILE", "metadata.json")

# --------------------------------------------------
# Application settings
# --------------------------------------------------
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Facebook Messenger Configuration
FB_PAGE_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
FB_VERIFY_TOKEN = os.getenv("FB_VERIFY_TOKEN", "SIGE_BOT_2026")
FB_APP_SECRET = os.getenv("FB_APP_SECRET")

# Whitelist for user IDs that should NEVER be blocked
WHITELIST_PSIDS = [
    pid.strip() for pid in os.getenv("WHITELIST_PSIDS", "").split(",") if pid.strip()
]

# App IDs that represent bots/automation (to exclude from human intervention detection)
# 921841513979535: SIGE AI Bot
BOT_APP_IDS = [
    aid.strip() for aid in os.getenv("BOT_APP_IDS", "921841513979535").split(",") if aid.strip()
]

# Shared Messenger Inbox App ID (Meta Business Suite)
# This ID is used for both ad automation AND human replies.
SHARED_INBOX_APP_ID = "263902037430900"

# Specific text patterns for ad automation messages that should NOT trigger a bot pause.
AD_AUTOMATION_PATTERNS = [
    r"(?s)Chào bạn, để Viện SIGE tư vấn chính xác lộ trình và học bổng.*Bạn đang học/đã tốt nghiệp THPT",
    r"(?s)Xin chào .* Bạn có câu hỏi nào cần trao đổi thêm với chúng tôi không\?"
]

# --------------------------------------------------
# Optional / future settings
# --------------------------------------------------
RATE_LIMIT = int(os.getenv("RATE_LIMIT", 60))
ENABLE_ESCALATION_LOG = os.getenv("ENABLE_ESCALATION_LOG", "True").lower() == "true"
