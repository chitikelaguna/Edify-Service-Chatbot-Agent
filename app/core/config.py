from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    """
    Application settings loaded from environment variables.
    Supports dual Supabase configuration:
    - Edify Supabase: Read-only data source (CRM/LMS/RMS)
    - Chatbot Supabase: Read/write database (sessions/memory/RAG/audit)
    """
    # OpenAI Configuration
    OPENAI_API_KEY: str
    
    # Edify Supabase (READ-ONLY)
    EDIFY_SUPABASE_URL: str
    EDIFY_SUPABASE_SERVICE_ROLE_KEY: str
    
    # Chatbot Supabase (READ/WRITE)
    CHATBOT_SUPABASE_URL: str
    CHATBOT_SUPABASE_SERVICE_ROLE_KEY: str
    
    # Environment Configuration
    ENV: str = "local"
    LOG_LEVEL: str = "INFO"

settings = Settings(
    OPENAI_API_KEY=os.getenv("OPENAI_API_KEY", ""),
    EDIFY_SUPABASE_URL=os.getenv("EDIFY_SUPABASE_URL", ""),
    EDIFY_SUPABASE_SERVICE_ROLE_KEY=os.getenv("EDIFY_SUPABASE_SERVICE_ROLE_KEY", ""),
    CHATBOT_SUPABASE_URL=os.getenv("CHATBOT_SUPABASE_URL", ""),
    CHATBOT_SUPABASE_SERVICE_ROLE_KEY=os.getenv("CHATBOT_SUPABASE_SERVICE_ROLE_KEY", ""),
    ENV=os.getenv("ENV", "local"),
    LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
)
