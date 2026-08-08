import pytest
from pydantic import ValidationError

from agent.state import AgentState, Citation, CritiqueResult


def test_agent_state_minimal_construction():
    state = AgentState(run_id="run-1", topic="quantum computing")
    assert state.status == "running"
    assert state.revision_count == 0
    assert state.draft == ""
    assert state.critique is None


def test_critique_result_rejects_invalid_verdict():
    with pytest.raises(ValidationError):
        CritiqueResult(verdict="maybe")


def test_citation_requires_url_and_title():
    with pytest.raises(ValidationError):
        Citation(title="Missing URL")


def test_agent_state_holds_sources():
    state = AgentState(
        run_id="run-2",
        topic="topic",
        sources=[Citation(url="https://example.com", title="Example")],
    )
    assert len(state.sources) == 1
    assert state.sources[0].url == "https://example.com"
