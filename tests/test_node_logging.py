import logging

import pytest

from agent.logging_config import with_logging
from agent.state import AgentState


def test_with_logging_passes_through_successful_result(caplog):
    def fake_node(state):
        return {"draft": "hello"}

    wrapped = with_logging("draft", fake_node)
    state = AgentState(run_id="run-1", topic="topic")

    with caplog.at_level(logging.INFO):
        result = wrapped(state)

    assert result == {"draft": "hello"}
    assert any("node_success" in r.message for r in caplog.records)
    assert any(getattr(r, "run_id", None) == "run-1" for r in caplog.records)


def test_with_logging_logs_and_reraises_on_failure(caplog):
    def failing_node(state):
        raise ValueError("boom")

    wrapped = with_logging("draft", failing_node)
    state = AgentState(run_id="run-1", topic="topic")

    with caplog.at_level(logging.INFO):
        with pytest.raises(ValueError):
            wrapped(state)

    assert any("node_failure" in r.message for r in caplog.records)
