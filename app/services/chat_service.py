from app.langgraph.graph import graph
from app.db.memory_repo import MemoryRepo
from app.db.audit_repo import AuditRepo
from app.db.chat_history_repo import ChatHistoryRepo
from app.services.session_service import SessionService
from typing import Dict, Any, List
import logging
import time

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        self.memory_repo = MemoryRepo()
        self.audit_repo = AuditRepo()
        self.chat_history_repo = ChatHistoryRepo()
        self.session_service = SessionService()

    async def process_user_message(
        self, 
        session_id: str, 
        user_message: str, 
        session_data: Dict[str, Any]
    ) -> str:
        """
        Orchestrates the chat flow with full persistence:
        1. Update session last_activity
        2. Save user message
        3. Audit log user query
        4. Load history
        5. Invoke LangGraph (which persists retrieved_context)
        6. Save assistant response (with source_type)
        7. Audit log completion
        8. Return response
        """
        start_time = time.time()
        admin_id = session_data.get("admin_id", "anonymous")
        
        try:
            # 1. Update session last_activity
            self.session_service.update_last_activity(session_id)
            
            # 2. Audit log user query
            self.audit_repo.log_action(
                admin_id=admin_id,
                action="user_message_received",
                details={"message_length": len(user_message)},
                session_id=session_id
            )
            
            # 3. Load History (from chat_history table)
            history = self.memory_repo.get_chat_history(session_id, limit=5)
            
            # 5. Construct Initial State (matching AgentState TypedDict)
            initial_state = {
                "session_id": session_id,
                "admin_id": admin_id,
                "user_message": user_message,
                "conversation_history": history,
                "retrieved_context": None,
                "source_type": None,
                "response": None
            }
            
            # 6. Invoke Graph (nodes will persist retrieved_context)
            result = await graph.ainvoke(initial_state)
            
            # 7. Extract Response
            bot_response = result.get("response", "I'm sorry, I couldn't generate a response.")
            source_type = result.get("source_type")
            
            # 8. Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # 9. Save to chat_history table (user message + assistant response pair)
            # This saves the complete conversation pair for historical tracking
            try:
                chat_history_success = self.chat_history_repo.save_chat_history(
                    session_id=session_id,
                    admin_id=admin_id,
                    user_message=user_message,
                    assistant_response=bot_response,
                    source_type=source_type,
                    response_time_ms=response_time_ms,
                    tokens_used=None  # Can be added later if token counting is implemented
                )
                
                if chat_history_success:
                    logger.info(f"Successfully saved chat history for session {session_id[:8]}...")
                else:
                    logger.warning(f"Failed to save chat history for session {session_id[:8]}...")
                    self.audit_repo.log_action(
                        admin_id=admin_id,
                        action="chat_history_save_failed",
                        details={
                            "error": "Failed to save chat history",
                            "session_id": session_id,
                            "user_message_length": len(user_message),
                            "response_length": len(bot_response)
                        },
                        session_id=session_id
                    )
            except Exception as chat_history_error:
                logger.error(f"Exception while saving chat history: {chat_history_error}", exc_info=True)
                self.audit_repo.log_action(
                    admin_id=admin_id,
                    action="chat_history_save_exception",
                    details={
                        "error": str(chat_history_error),
                        "session_id": session_id
                    },
                    session_id=session_id
                )
            
            # 10. Audit log completion
            self.audit_repo.log_action(
                admin_id=admin_id,
                action="chat_completed",
                details={
                    "source_type": source_type,
                    "response_time_ms": response_time_ms,
                    "response_length": len(bot_response)
                },
                session_id=session_id
            )
            
            return bot_response

        except Exception as e:
            logger.error(f"Error in ChatService: {e}", exc_info=True)
            # Audit log the error
            try:
                self.audit_repo.log_action(
                    admin_id=admin_id,
                    action="chat_error",
                    details={"error": str(e), "user_message": user_message[:100]},
                    session_id=session_id
                )
            except:
                pass
            raise e

