import pytest

from agent.routing import make_route_after_critique, route_after_research
from agent.state import AgentState, CritiqueResult


def _state(**kwargs):
    defaults = dict(run_id="run-1", topic="topic")
    defaults.update(kwargs)
    return AgentState(**defaults)


def test_route_after_research_goes_to_draft_on_success():
    assert route_after_research(_state(status="running")) == "draft"


def test_route_after_research_goes_to_failed_on_failure():
    assert route_after_research(_state(status="failed")) == "failed"


def test_route_after_critique_finalizes_on_pass():
    router = make_route_after_critique(max_revisions=3)
    state = _state(critique=CritiqueResult(verdict="pass", issues=[]))
    assert router(state) == "finalize"


def test_route_after_critique_revises_when_failed_and_under_cap():
    router = make_route_after_critique(max_revisions=3)
    state = _state(critique=CritiqueResult(verdict="fail", issues=["too short"]), revision_count=1)
    assert router(state) == "revise"


def test_route_after_critique_finalizes_when_revisions_exhausted():
    router = make_route_after_critique(max_revisions=2)
    state = _state(critique=CritiqueResult(verdict="fail", issues=["still bad"]), revision_count=2)
    assert router(state) == "finalize"


def test_route_after_critique_raises_if_critique_missing():
    router = make_route_after_critique()
    with pytest.raises(ValueError):
        router(_state())
