import pytest

from agent.state import Citation
from agent.tools.search import FakeSearchTool, RetryingSearchTool, SearchToolError


def test_fake_search_tool_returns_configured_results():
    fake = FakeSearchTool(results=[Citation(url="https://example.com", title="Example")])
    results = fake.search("quantum computing")
    assert len(results) == 1
    assert results[0].url == "https://example.com"
    assert fake.calls == ["quantum computing"]


def test_fake_search_tool_can_simulate_failures():
    fake = FakeSearchTool(results=[], fail_times=2)
    with pytest.raises(SearchToolError):
        fake.search("topic")
    with pytest.raises(SearchToolError):
        fake.search("topic")
    results = fake.search("topic")
    assert results == []


def test_retrying_wrapper_succeeds_after_transient_failures():
    fake = FakeSearchTool(
        results=[Citation(url="https://example.com", title="Example")], fail_times=2
    )
    retrying = RetryingSearchTool(fake, max_attempts=3, wait_seconds=0.01)
    results = retrying.search("topic")
    assert len(results) == 1
    assert len(fake.calls) == 3


def test_retrying_wrapper_gives_up_after_max_attempts():
    fake = FakeSearchTool(results=[], fail_times=5)
    retrying = RetryingSearchTool(fake, max_attempts=3, wait_seconds=0.01)
    with pytest.raises(SearchToolError):
        retrying.search("topic")
    assert len(fake.calls) == 3
