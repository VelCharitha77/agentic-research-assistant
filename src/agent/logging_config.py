import json
import logging
import time


class JSONFormatter(logging.Formatter):
    _extra_fields = ("run_id", "node", "duration_ms", "error")

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        for key in self._extra_fields:
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)


_logger = logging.getLogger("agent.nodes")


def with_logging(node_name: str, node_fn):
    """Wraps a node function with structured start/success/failure logging,
    correlated by run_id. Cross-cutting, so individual node files stay free
    of logging boilerplate."""

    def wrapped(state):
        start = time.monotonic()
        _logger.info("node_start", extra={"run_id": state.run_id, "node": node_name})
        try:
            result = node_fn(state)
        except Exception as exc:
            duration_ms = (time.monotonic() - start) * 1000
            _logger.error(
                "node_failure",
                extra={
                    "run_id": state.run_id,
                    "node": node_name,
                    "duration_ms": round(duration_ms, 1),
                    "error": str(exc),
                },
            )
            raise
        duration_ms = (time.monotonic() - start) * 1000
        _logger.info(
            "node_success",
            extra={
                "run_id": state.run_id,
                "node": node_name,
                "duration_ms": round(duration_ms, 1),
            },
        )
        return result

    return wrapped
