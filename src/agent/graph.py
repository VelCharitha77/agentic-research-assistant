from langgraph.graph import END, START, StateGraph

from agent.llm_client import LLMClient
from agent.logging_config import with_logging
from agent.nodes.critique import make_critique_node
from agent.nodes.draft import make_draft_node
from agent.nodes.finalize import finalize_node
from agent.nodes.research import make_research_node
from agent.nodes.revise import make_revise_node
from agent.routing import make_route_after_critique, route_after_research
from agent.state import AgentState
from agent.tools.search import SearchTool


def _failed_node(state: AgentState) -> dict:
    return {}


def build_graph(
    llm_client: LLMClient,
    search_tool: SearchTool,
    max_revisions: int = 3,
    checkpointer=None,
):
    graph = StateGraph(AgentState)

    graph.add_node("research", with_logging("research", make_research_node(search_tool)))
    graph.add_node("draft", with_logging("draft", make_draft_node(llm_client)))
    graph.add_node("critique", with_logging("critique", make_critique_node(llm_client)))
    graph.add_node("revise", with_logging("revise", make_revise_node(llm_client)))
    graph.add_node("finalize", with_logging("finalize", finalize_node))
    graph.add_node("failed", with_logging("failed", _failed_node))

    graph.add_edge(START, "research")
    graph.add_conditional_edges(
        "research",
        route_after_research,
        {"draft": "draft", "failed": "failed"},
    )
    graph.add_edge("draft", "critique")
    graph.add_conditional_edges(
        "critique",
        make_route_after_critique(max_revisions=max_revisions),
        {"revise": "revise", "finalize": "finalize"},
    )
    graph.add_edge("revise", "critique")
    graph.add_edge("finalize", END)
    graph.add_edge("failed", END)

    return graph.compile(checkpointer=checkpointer)
