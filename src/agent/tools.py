from langgraph.prebuilt import ToolNode

from src.agent.events import EventEmitter
from src.infrastructure.external.brave import BraveSearchClient
from src.modules.patients.tools import get_patient_history
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig


@tool
async def web_search(query: str, config: RunnableConfig) -> str:
    """
    Search medical websites for health information.
    Use this when the user asks about medical conditions, medications,
    treatments, procedures, or clinical guidelines.
    """
    emitter = EventEmitter(config)
    await emitter.emit_status(f"Searching for '{query}'...")

    try:
        client = BraveSearchClient()
        results = await client.search(query, count=8)

        if not results:
            return "No results found."

        citations_data = {
            "count": len(results),
            "items": [
                {
                    "id": i + 1,
                    "name": r.profile_name,
                    "title": r.title,
                    "description": r.description,
                    "url": r.url,
                    "domain": r.hostname,
                    "favicon": r.profile_img,
                }
                for i, r in enumerate(results)
            ],
        }
        await emitter.emit_artifact("citations", citations_data)

        formatted = []
        for i, result in enumerate(results, 1):
            entry = f"{i}. {result.title}\n   URL: {result.url}\n   {result.description}"
            if result.extra_snippets:
                snippets = "\n   ".join(f"- {s}" for s in result.extra_snippets)
                entry += f"\n   Additional context:\n   {snippets}"
            formatted.append(entry)

        return "\n\n".join(formatted)

    except Exception as e:
        return f"Search failed: {e}"


AGENT_TOOLS = [web_search, get_patient_history]

tools_node = ToolNode(AGENT_TOOLS)
