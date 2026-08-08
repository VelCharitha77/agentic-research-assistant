from agent.llm_client import FakeLLMClient
from agent.nodes.critique import make_critique_node
from agent.state import AgentState, CritiqueResult


def _state(**kwargs):
    defaults = dict(
        run_id="run-1",
        topic="quantum computing",
        research_notes=["Note A"],
        draft="A draft about quantum computing.",
    )
    defaults.update(kwargs)
    return AgentState(**defaults)


def test_critique_node_returns_structured_verdict():
    expected = CritiqueResult(verdict="pass", issues=[])
    fake = FakeLLMClient(structured_responses=[expected])
    node = make_critique_node(fake)

    update = node(_state())

    assert update["critique"] is expected


def test_critique_node_requests_the_correct_schema():
    fake = FakeLLMClient(structured_responses=[CritiqueResult(verdict="fail", issues=["too short"])])
    node = make_critique_node(fake)

    node(_state())

    _, system, prompt, schema = fake.calls[0]
    assert schema is CritiqueResult


def test_critique_node_includes_draft_in_prompt():
    fake = FakeLLMClient(structured_responses=[CritiqueResult(verdict="pass", issues=[])])
    node = make_critique_node(fake)

    node(_state(draft="Unique draft content xyz"))

    _, system, prompt, schema = fake.calls[0]
    assert "Unique draft content xyz" in prompt
