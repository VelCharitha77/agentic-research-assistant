from fastapi.testclient import TestClient
from langgraph.checkpoint.memory import MemorySaver

from agent.api.main import app, get_graph
from agent.graph import build_graph
from agent.llm_client import FakeLLMClient
from agent.state import CritiqueResult, create_initial_state
from agent.tools.search import FakeSearchTool


def test_stream_returns_immediately_for_an_already_completed_run():
    llm = FakeLLMClient(
        text_responses=["Draft v1"], structured_responses=[CritiqueResult(verdict="pass", issues=[])]
    )
    graph = build_graph(llm, FakeSearchTool(results=[]), checkpointer=MemorySaver())

    # Run it synchronously (bypassing the API's background task) purely to
    # get a completed checkpoint in place before testing the stream endpoint.
    config = {"configurable": {"thread_id": "already-done-run"}}
    graph.invoke(create_initial_state("already-done-run", "test topic"), config=config)

    app.dependency_overrides[get_graph] = lambda: graph
    client = TestClient(app)

    with client.stream("GET", "/runs/already-done-run/stream") as response:
        lines = [line for line in response.iter_lines() if line]

    assert any("done" in line for line in lines)
    app.dependency_overrides.clear()
