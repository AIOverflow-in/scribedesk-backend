from langgraph.graph import StateGraph

from src.agent.state import AgentState
from src.agent.node import agent_node
from src.agent.edges import should_call_tools
from src.agent.tools import tools_node

workflow = StateGraph(AgentState)

workflow.add_node("agent", agent_node)
workflow.add_node("tools", tools_node)

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_call_tools,
    {
        "tools": "tools",
        "__end__": "__end__",
    },
)

workflow.add_edge("tools", "agent")

agent_app = workflow.compile()
