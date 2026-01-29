from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings
import logging
import httpx
import os

logger = logging.getLogger(__name__)


class OpenAIClient:
    def __init__(self):
        # Remove proxy env vars before creating httpx client to prevent OpenAI from reading them
        # This prevents the 'proxies' parameter error with openai>=1.10.0
        saved_proxy_vars = {}
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
        for var in proxy_vars:
            if var in os.environ:
                saved_proxy_vars[var] = os.environ.pop(var)
        
        try:
            # Create httpx client - it won't read proxy env vars since we removed them
            http_client = httpx.Client()
            self.llm = ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                model="gpt-4o",
                temperature=0,  # Deterministic for formatting
                http_client=http_client
            )
        finally:
            # Restore proxy env vars
            os.environ.update(saved_proxy_vars)

    def generate_response(self, system_prompt: str, user_input: str) -> str:
        """
        Generates a response from the LLM.
        """
        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_input)
            ]
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            raise e
