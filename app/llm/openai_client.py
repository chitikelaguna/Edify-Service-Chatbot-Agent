from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class OpenAIClient:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model="gpt-4o",
            temperature=0  # Deterministic for formatting
        )

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
