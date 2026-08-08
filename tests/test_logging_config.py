import json
import logging

from agent.logging_config import JSONFormatter


def test_json_formatter_produces_valid_json_with_expected_fields():
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname=__file__, lineno=1,
        msg="node_success", args=(), exc_info=None,
    )
    record.run_id = "run-1"
    record.node = "draft"
    record.duration_ms = 12.5

    output = json.loads(formatter.format(record))

    assert output["message"] == "node_success"
    assert output["run_id"] == "run-1"
    assert output["node"] == "draft"
    assert output["duration_ms"] == 12.5
    assert output["level"] == "INFO"
