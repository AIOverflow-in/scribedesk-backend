from typing import Literal

from langchain_core.messages import AIMessage
from langgraph.graph import END

from src.agent.state import AgentState


def should_call_tools(state: AgentState) -> Literal["tools", "__end__"]:
    messages = state["messages"]

    if messages and isinstance(messages[-1], AIMessage):
        if messages[-1].tool_calls:
            return "tools"

    return END
