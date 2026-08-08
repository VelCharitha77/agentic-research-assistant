from agent.nodes.finalize import finalize_node
from agent.state import AgentState, Citation


def _state(**kwargs):
    defaults = dict(
        run_id="run-1",
        topic="quantum computing",
        draft="Final content about quantum computing.",
        sources=[Citation(url="https://example.com", title="Example Source")],
    )
    defaults.update(kwargs)
    return AgentState(**defaults)


def test_finalize_node_sets_status_completed():
    update = finalize_node(_state())
    assert update["status"] == "completed"


def test_finalize_node_appends_sources_to_final_document():
    update = finalize_node(_state())
    assert "Final content about quantum computing." in update["final_document"]
    assert "Example Source" in update["final_document"]
    assert "https://example.com" in update["final_document"]


def test_finalize_node_handles_no_sources():
    update = finalize_node(_state(sources=[]))
    assert "(no sources)" in update["final_document"]
