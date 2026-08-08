from agent.graph import build_graph
from agent.llm_client import FakeLLMClient
from agent.state import Citation, CritiqueResult, create_initial_state
from agent.tools.search import FakeSearchTool, RetryingSearchTool


def _search_tool(results=None, fail_times=0):
    fake = FakeSearchTool(results=results or [], fail_times=fail_times)
    return RetryingSearchTool(fake, max_attempts=2, wait_seconds=0.01)


def test_graph_happy_path_finishes_on_first_critique_pass():
    llm = FakeLLMClient(
        text_responses=["Draft v1"],
        structured_responses=[CritiqueResult(verdict="pass", issues=[])],
    )
    search_tool = _search_tool(results=[Citation(url="https://example.com", title="Example")])
    compiled = build_graph(llm, search_tool, max_revisions=3)

    result = compiled.invoke(create_initial_state("run-1", "quantum computing"))

    assert result["status"] == "completed"
    assert result["revision_count"] == 0
    assert "Draft v1" in result["final_document"]
    assert "Example" in result["final_document"]


def test_graph_revises_once_then_passes():
    llm = FakeLLMClient(
        text_responses=["Draft v1", "Draft v2"],
        structured_responses=[
            CritiqueResult(verdict="fail", issues=["too short"]),
            CritiqueResult(verdict="pass", issues=[]),
        ],
    )
    search_tool = _search_tool(results=[])
    compiled = build_graph(llm, search_tool, max_revisions=3)

    result = compiled.invoke(create_initial_state("run-2", "dark matter"))

    assert result["status"] == "completed"
    assert result["revision_count"] == 1
    assert "Draft v2" in result["final_document"]


def test_graph_finalizes_anyway_when_revisions_exhausted():
    llm = FakeLLMClient(
        text_responses=["Draft v1", "Draft v2", "Draft v3"],
        structured_responses=[
            CritiqueResult(verdict="fail", issues=["issue 1"]),
            CritiqueResult(verdict="fail", issues=["issue 2"]),
            CritiqueResult(verdict="fail", issues=["issue 3"]),
        ],
    )
    search_tool = _search_tool(results=[])
    compiled = build_graph(llm, search_tool, max_revisions=2)

    result = compiled.invoke(create_initial_state("run-3", "topic"))

    assert result["status"] == "completed"
    assert result["revision_count"] == 2
    assert "Draft v3" in result["final_document"]


def test_graph_routes_to_failed_when_search_exhausts_retries():
    llm = FakeLLMClient()  # no responses queued — proves draft/critique are never reached
    search_tool = _search_tool(fail_times=10)
    compiled = build_graph(llm, search_tool, max_revisions=3)

    result = compiled.invoke(create_initial_state("run-4", "topic"))

    assert result["status"] == "failed"
    assert "Research failed" in result["error"]
