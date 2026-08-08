import pytest

from agent.checkpointer import get_checkpointer
from agent.graph import build_graph
from agent.llm_client import FakeLLMClient
from agent.state import Citation, CritiqueResult, create_initial_state
from agent.tools.search import FakeSearchTool


def test_graph_resumes_from_checkpoint_without_rerunning_completed_nodes():
    search_tool = FakeSearchTool(results=[Citation(url="https://example.com", title="Example")])
    config = {"configurable": {"thread_id": "crash-test-1"}}

    with get_checkpointer() as checkpointer:
        # Simulate a crash partway through: Draft's LLM call has nothing
        # queued, so it raises right after Research has already completed
        # and been checkpointed.
        crashing_llm = FakeLLMClient(text_responses=[])
        graph = build_graph(crashing_llm, search_tool, checkpointer=checkpointer)

        with pytest.raises(AssertionError):
            graph.invoke(create_initial_state("run-1", "quantum computing"), config=config)

        # Simulate a restart: a brand new graph and LLM client, but the same
        # checkpointer and thread_id.
        recovering_llm = FakeLLMClient(
            text_responses=["Draft v1"],
            structured_responses=[CritiqueResult(verdict="pass", issues=[])],
        )
        resumed_graph = build_graph(recovering_llm, search_tool, checkpointer=checkpointer)

        # Passing None as input (not a fresh state) tells LangGraph to
        # continue from the last saved checkpoint rather than start over.
        result = resumed_graph.invoke(None, config=config)

    assert result["status"] == "completed"
    assert "Draft v1" in result["final_document"]
    assert search_tool.calls == ["quantum computing"]  # Research ran exactly once, not twice
