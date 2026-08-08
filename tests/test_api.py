import time

from fastapi.testclient import TestClient
from langgraph.checkpoint.memory import MemorySaver

from agent.api.main import app, get_graph
from agent.graph import build_graph
from agent.llm_client import FakeLLMClient
from agent.state import Citation, CritiqueResult
from agent.tools.search import FakeSearchTool


def _build_test_graph(text_responses, structured_responses, search_results=None):
    llm = FakeLLMClient(text_responses=text_responses, structured_responses=structured_responses)
    search_tool = FakeSearchTool(results=search_results or [])
    # MemorySaver, not Postgres: this file tests the API contract, not
    # persistence — Step 10 already proved persistence works.
    return build_graph(llm, search_tool, checkpointer=MemorySaver())


def test_create_run_returns_202_and_a_run_id():
    graph = _build_test_graph(["Draft v1"], [CritiqueResult(verdict="pass", issues=[])])
    app.dependency_overrides[get_graph] = lambda: graph
    client = TestClient(app)

    response = client.post("/runs", json={"topic": "quantum computing"})

    assert response.status_code == 202
    assert "run_id" in response.json()
    app.dependency_overrides.clear()


def test_get_run_returns_404_for_unknown_run_id():
    graph = _build_test_graph([], [])
    app.dependency_overrides[get_graph] = lambda: graph
    client = TestClient(app)

    response = client.get("/runs/does-not-exist")

    assert response.status_code == 404
    app.dependency_overrides.clear()


def test_full_flow_create_then_poll_until_completed():
    graph = _build_test_graph(
        ["Draft v1"],
        [CritiqueResult(verdict="pass", issues=[])],
        search_results=[Citation(url="https://example.com", title="Example")],
    )
    app.dependency_overrides[get_graph] = lambda: graph
    client = TestClient(app)

    create_response = client.post("/runs", json={"topic": "quantum computing"})
    run_id = create_response.json()["run_id"]

    # Poll briefly for completion — works whether TestClient happens to run
    # background tasks synchronously or genuinely in the background.
    deadline = time.time() + 5
    status = None
    while time.time() < deadline:
        poll = client.get(f"/runs/{run_id}")
        assert poll.status_code == 200
        status = poll.json()["status"]
        if status != "running":
            break
        time.sleep(0.05)

    assert status == "completed"
    final = client.get(f"/runs/{run_id}").json()
    assert "Draft v1" in final["final_document"]
    app.dependency_overrides.clear()
