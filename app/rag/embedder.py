from typing import List
from langchain_openai import OpenAIEmbeddings
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class Embedder:
    def __init__(self):
        # Using text-embedding-3-small or ada-002
        self.client = OpenAIEmbeddings(
            api_key=settings.OPENAI_API_KEY,
            model="text-embedding-3-small" 
        )

    def embed_text(self, text: str) -> List[float]:
        """
        Generates embedding for a single string.
        """
        try:
            return self.client.embed_query(text)
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise e

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generates embeddings for a list of strings.
        """
        try:
            return self.client.embed_documents(texts)
        except Exception as e:
            logger.error(f"Error generating document embeddings: {e}")
            raise e
