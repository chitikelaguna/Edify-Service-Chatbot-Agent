from typing import List, Dict, Any
from app.db.supabase import get_chatbot_supabase_client
from app.rag.embedder import Embedder
import logging

logger = logging.getLogger(__name__)

class IngestionService:
    def __init__(self):
        self.supabase = get_chatbot_supabase_client()
        self.embedder = Embedder()
        self.table = "rag_documents"  # Updated to match requirements

    def ingest_text(self, content: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Embeds and stores text in Supabase.
        """
        try:
            # 1. Embed content
            embedding = self.embedder.embed_text(content)
            
            # 2. Prepare data
            data = {
                "content": content,
                "embedding": embedding, # pgvector treats list as vector
                "metadata": metadata or {}
            }
            
            # 3. Insert
            self.supabase.table(self.table).insert(data).execute()
            logger.info("Successfully ingested document.")
            return True
            
        except Exception as e:
            logger.error(f"Error ingesting document: {e}")
            return False

    def ingest_bulk(self, contents: List[str]) -> bool:
        """
        Batch ingestion.
        """
        try:
            embeddings = self.embedder.embed_documents(contents)
            
            records = []
            for content, embedding in zip(contents, embeddings):
                records.append({
                    "content": content,
                    "embedding": embedding
                })
                
            self.supabase.table(self.table).insert(records).execute()
            return True
            
        except Exception as e:
            logger.error(f"Error bulk ingesting: {e}")
            return False
