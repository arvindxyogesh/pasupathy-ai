import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# MongoDB configuration
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/llm_chat')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'llm_chat')

# Google Gemini API configuration
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '').strip('"\'')
if not GOOGLE_API_KEY:
    logger.error("❌ GOOGLE_API_KEY not set! AI features will not work.")
    logger.info("💡 Set GOOGLE_API_KEY in your .env file or environment variables")
else:
    logger.info(f"✅ GOOGLE_API_KEY configured (key: ...{GOOGLE_API_KEY[-4:]})")

# LLM Configuration
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
GEMINI_MODEL = "gemini-2.5-flash"  # Free tier model (1.5M requests/month)
TEMPERATURE = 0.7  # Creative responses

# RAG Configuration
SEARCH_K = 15  # Number of documents to retrieve (increased for better coverage)
CHUNK_SIZE = 1000  # Size of text chunks
CHUNK_OVERLAP = 200  # Overlap between chunks
MAX_CONTEXT_MESSAGES = 6  # For conversation history

# API Configuration
MAX_RETRIES = 3
RETRY_DELAY = 1
REQUEST_TIMEOUT = 30

logger.info("✅ Configuration loaded successfully")