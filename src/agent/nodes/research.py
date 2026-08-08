from agent.state import AgentState, Citation
from agent.tools.search import SearchTool, SearchToolError


def _format_note(citation: Citation) -> str:
    if citation.snippet:
        return f"{citation.title}: {citation.snippet}"
    return citation.title


def make_research_node(search_tool: SearchTool):
    """Factory that closes over the search tool dependency, keeping the
    node function itself free of any concrete SearchTool implementation."""

    def research_node(state: AgentState) -> dict:
        try:
            citations = search_tool.search(state.topic)
        except SearchToolError as exc:
            return {"status": "failed", "error": f"Research failed after retries: {exc}"}

        return {
            "research_notes": [_format_note(c) for c in citations],
            "sources": citations,
        }

    return research_node
