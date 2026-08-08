import pytest
from pydantic import BaseModel

from agent.llm_client import FakeLLMClient, _pydantic_to_tool
from agent.state import CritiqueResult


class _Dummy(BaseModel):
    value: int


def test_fake_client_returns_queued_text_responses_in_order():
    fake = FakeLLMClient(text_responses=["first", "second"])
    assert fake.complete(system="s", prompt="p") == "first"
    assert fake.complete(system="s", prompt="p") == "second"


def test_fake_client_raises_when_text_queue_exhausted():
    fake = FakeLLMClient(text_responses=["only one"])
    fake.complete(system="s", prompt="p")
    with pytest.raises(AssertionError):
        fake.complete(system="s", prompt="p")


def test_fake_client_returns_queued_structured_responses():
    expected = CritiqueResult(verdict="pass", issues=[])
    fake = FakeLLMClient(structured_responses=[expected])
    result = fake.complete_structured(system="s", prompt="p", schema=CritiqueResult)
    assert result is expected


def test_fake_client_rejects_wrong_type_in_structured_queue():
    fake = FakeLLMClient(structured_responses=[_Dummy(value=1)])
    with pytest.raises(TypeError):
        fake.complete_structured(system="s", prompt="p", schema=CritiqueResult)


def test_fake_client_records_calls_for_assertions():
    fake = FakeLLMClient(text_responses=["ok"])
    fake.complete(system="sys-prompt", prompt="user-prompt")
    assert fake.calls == [("complete", "sys-prompt", "user-prompt")]


def test_pydantic_to_tool_produces_valid_tool_schema():
    tool = _pydantic_to_tool(CritiqueResult)
    assert tool["name"] == "return_result"
    assert "verdict" in tool["input_schema"]["properties"]
