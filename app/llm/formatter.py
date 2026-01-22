from typing import Any
import json
from app.llm.openai_client import OpenAIClient
import logging

logger = logging.getLogger(__name__)

class ResponseFormatter:
    def __init__(self):
        self.client = OpenAIClient()

    def format_response(self, query: str, context: Any, source: str) -> str:
        """
        Formats the retrieved context into a polite response.
        """
        try:
            if not context and source != "general":
                return "I searched the records but found no matching data for your request."

            # Construct System Prompt based on source
            if source == "general":
                 system_prompt = """You are a helpful and professional Edify Admin Assistant. 
                 Your role is to assist administrators. 
                 Answer general greetings or navigational questions politely.
                 WARN: Do not invent any business data (names, deals, courses) if not provided.
                 """
                 user_input = query
            else:
                 # Serialize context safely
                 context_str = json.dumps(context, indent=2, default=str)
                 
                 system_prompt = f"""You are a helpful Edify Admin Assistant.
                 Your task is to answer the user's query using ONLY the provided context from the {source.upper()} system.
                 
                 RULES:
                 1. Use ONLY the provided context.
                 2. Do not invent information.
                 3. If the context does not answer the question, say "The provided records do not contain the answer."
                 4. Create a clean, readable response (use bullet points or tables if data is structured).
                 
                 CONTEXT:
                 {context_str}
                 """
                 user_input = query

            return self.client.generate_response(system_prompt, user_input)

        except Exception as e:
            logger.error(f"Error formatting response: {e}")
            return "I encountered an error while formatting the data."
