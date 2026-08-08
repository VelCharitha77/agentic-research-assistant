from agent.nodes.research import make_research_node
from agent.state import AgentState, Citation
from agent.tools.search import FakeSearchTool, RetryingSearchTool


def _state(topic="quantum computing"):
    return AgentState(run_id="run-1", topic=topic)


def test_research_node_populates_notes_and_sources_on_success():
    fake_tool = FakeSearchTool(
        results=[Citation(url="https://example.com", title="Example", snippet="A summary.")]
    )
    node = make_research_node(fake_tool)

    update = node(_state())

    assert update["sources"][0].url == "https://example.com"
    assert update["research_notes"] == ["Example: A summary."]
    assert "status" not in update


def test_research_node_formats_notes_with_title_only_when_snippet_missing():
    fake_tool = FakeSearchTool(results=[Citation(url="https://example.com", title="Example")])
    node = make_research_node(fake_tool)

    update = node(_state())

    assert update["research_notes"] == ["Example"]


def test_research_node_uses_topic_as_the_query():
    fake_tool = FakeSearchTool(results=[])
    node = make_research_node(fake_tool)

    node(_state(topic="dark matter"))

    assert fake_tool.calls == ["dark matter"]


def test_research_node_marks_state_failed_when_search_exhausts_retries():
    fake_tool = FakeSearchTool(results=[], fail_times=5)
    retrying_tool = RetryingSearchTool(fake_tool, max_attempts=3, wait_seconds=0.01)
    node = make_research_node(retrying_tool)

    update = node(_state())

    assert update["status"] == "failed"
    assert "Research failed" in update["error"]


def test_research_node_handles_empty_results_without_failing():
    fake_tool = FakeSearchTool(results=[])
    node = make_research_node(fake_tool)

    update = node(_state())

    assert update["research_notes"] == []
    assert update["sources"] == []
    assert "status" not in update
