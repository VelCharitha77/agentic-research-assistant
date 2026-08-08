from agent.llm_client import FakeLLMClient
from agent.nodes.revise import make_revise_node
from agent.state import AgentState, CritiqueResult


def _state(**kwargs):
    defaults = dict(
        run_id="run-1",
        topic="quantum computing",
        research_notes=["Note A"],
        draft="Original draft.",
        critique=CritiqueResult(verdict="fail", issues=["too vague", "missing dates"]),
        revision_count=0,
    )
    defaults.update(kwargs)
    return AgentState(**defaults)


def test_revise_node_returns_new_draft_and_increments_count():
    fake = FakeLLMClient(text_responses=["Revised draft."])
    node = make_revise_node(fake)

    update = node(_state())

    assert update["draft"] == "Revised draft."
    assert update["revision_count"] == 1


def test_revise_node_includes_issues_in_prompt():
    fake = FakeLLMClient(text_responses=["Revised draft."])
    node = make_revise_node(fake)

    node(_state())

    _, system, prompt = fake.calls[0]
    assert "too vague" in prompt
    assert "missing dates" in prompt


def test_revise_node_increments_from_current_count_not_zero():
    fake = FakeLLMClient(text_responses=["Revised again."])
    node = make_revise_node(fake)

    update = node(_state(revision_count=2))

    assert update["revision_count"] == 3
