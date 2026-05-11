from typing import Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from src.agent.state import AgentState


class ChatStateBuilder:
    @staticmethod
    async def build_state(
        user_id: str,
        conversation_id: str,
        history_messages: list,
        current_message,
        session_context: Optional[dict] = None,
        patient_context: Optional[dict] = None,
    ) -> AgentState:
        lc_messages = ChatStateBuilder._build_langchain_history(history_messages)

        if current_message:
            lc_messages.append(HumanMessage(content=current_message.content))

        return {
            "messages": lc_messages,
            "user_id": user_id,
            "conversation_id": conversation_id,
            "session_context": session_context,
            "patient_context": patient_context,
        }

    @staticmethod
    def _build_langchain_history(messages: list) -> list:
        lc_messages = []
        for msg in messages:
            if msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                lc_messages.append(AIMessage(content=msg.content))
        return lc_messages
