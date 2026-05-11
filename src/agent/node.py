from typing import Dict, Any

from langchain_core.messages import AIMessage, SystemMessage, ToolMessage

from src.agent.helpers import format_patient_context, format_session_context
from src.agent.state import AgentState
from src.agent.tools import AGENT_TOOLS
from src.content.prompts.chat import ChatPrompts
from src.core.logging import get_logger
from src.dependencies.ai import get_smart_llm_service
from src.utils.formatters import format_current_date

logger = get_logger(__name__)


async def agent_node(state: AgentState) -> Dict[str, Any]:
    messages = state["messages"]
    user_id = state.get("user_id", "")
    conversation_id = state.get("conversation_id", "")
    session_ctx = state.get("session_context")
    patient_ctx = state.get("patient_context")

    llm_service = get_smart_llm_service()

    citation_instr = ""
    has_search = any(isinstance(m, ToolMessage) and m.name == "web_search" for m in messages)
    if has_search:
        citation_instr = "\n\n" + ChatPrompts.CITATION_INSTRUCTIONS

    system_content = ChatPrompts.COPILOT_SYSTEM.format(
        current_date=format_current_date(),
        patient_context=format_patient_context(patient_ctx),
        session_context=format_session_context(session_ctx),
    ) + citation_instr

    if not messages or not isinstance(messages[0], SystemMessage):
        system_msg = SystemMessage(content=system_content)
        messages = [system_msg] + list(messages)
    else:
        messages[0] = SystemMessage(content=system_content)

    try:
        model_with_tools = llm_service.model.bind_tools(AGENT_TOOLS)
        response = await model_with_tools.ainvoke(messages)

        logger.info(f"Agent response generated for user={user_id}, conv={conversation_id}")
        return {"messages": [response]}

    except Exception as e:
        logger.error(f"Agent error for user={user_id}, conv={conversation_id}: {e}", exc_info=True)
        error_msg = AIMessage(content="I encountered an error. Please try again.")
        return {"messages": [error_msg]}
