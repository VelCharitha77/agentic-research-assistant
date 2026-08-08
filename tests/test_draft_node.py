from agent.llm_client import FakeLLMClient
from agent.nodes.draft import make_draft_node
from agent.state import AgentState


def _state(**kwargs):
    defaults = dict(run_id="run-1", topic="quantum computing", research_notes=["Note A", "Note B"])
    defaults.update(kwargs)
    return AgentState(**defaults)


def test_draft_node_returns_llm_output_as_draft():
    fake = FakeLLMClient(text_responses=["This is the generated draft."])
    node = make_draft_node(fake)

    update = node(_state())

    assert update["draft"] == "This is the generated draft."


def test_draft_node_includes_topic_and_notes_in_prompt():
    fake = FakeLLMClient(text_responses=["draft"])
    node = make_draft_node(fake)

    node(_state())

    _, system, prompt = fake.calls[0]
    assert "quantum computing" in prompt
    assert "Note A" in prompt
    assert "Note B" in prompt


def test_draft_node_handles_empty_research_notes():
    fake = FakeLLMClient(text_responses=["draft"])
    node = make_draft_node(fake)

    node(_state(research_notes=[]))

    _, system, prompt = fake.calls[0]
    assert "no research notes available" in prompt
