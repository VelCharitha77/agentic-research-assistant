import asyncio
import json
import uuid
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from agent.checkpointer import get_checkpointer
from agent.events import broadcaster
from agent.graph import build_graph
from agent.llm_client import get_llm_client
from agent.state import create_initial_state
from agent.tools.search import RetryingSearchTool, TavilySearchTool


class CreateRunRequest(BaseModel):
    topic: str


class CreateRunResponse(BaseModel):
    run_id: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    with get_checkpointer() as checkpointer:
        llm_client = get_llm_client()
        search_tool = RetryingSearchTool(TavilySearchTool())
        app.state.graph = build_graph(llm_client, search_tool, checkpointer=checkpointer)
        yield


app = FastAPI(title="Agentic Research Assistant", lifespan=lifespan)


def get_graph(request: Request):
    return request.app.state.graph


def _run_graph(graph, run_id: str, topic: str):
    config = {"configurable": {"thread_id": run_id}}
    try:
        for step in graph.stream(
            create_initial_state(run_id, topic), config=config, stream_mode="updates"
        ):
            for node_name, node_update in step.items():
                event = {"node": node_name}
                if isinstance(node_update, dict) and "revision_count" in node_update:
                    event["revision_count"] = node_update["revision_count"]
                broadcaster.publish(run_id, event)
    except Exception as exc:
        graph.update_state(config, {"status": "failed", "error": f"Unhandled error: {exc}"})
        broadcaster.publish(run_id, {"node": "failed", "error": str(exc)})
    finally:
        broadcaster.close(run_id)


@app.post("/runs", response_model=CreateRunResponse, status_code=202)
def create_run(
    request: CreateRunRequest, background_tasks: BackgroundTasks, graph=Depends(get_graph)
):
    run_id = uuid.uuid4().hex
    background_tasks.add_task(_run_graph, graph, run_id, request.topic)
    return CreateRunResponse(run_id=run_id)


@app.get("/runs/{run_id}")
def get_run(run_id: str, graph=Depends(get_graph)):
    config = {"configurable": {"thread_id": run_id}}
    snapshot = graph.get_state(config)
    if not snapshot.values:
        raise HTTPException(status_code=404, detail="Run not found")
    return snapshot.values


@app.get("/runs/{run_id}/stream")
async def stream_run(run_id: str, graph=Depends(get_graph)):
    config = {"configurable": {"thread_id": run_id}}
    snapshot = graph.get_state(config)

    # If the run already finished before the client connected, there's no
    # live queue to subscribe to — reply immediately instead of hanging.
    if snapshot.values and snapshot.values.get("status") in ("completed", "failed"):

        async def already_done():
            yield f"data: {json.dumps({'node': 'done', 'status': snapshot.values['status']})}\n\n"
            yield "event: done\ndata: {}\n\n"

        return StreamingResponse(already_done(), media_type="text/event-stream")

    q = broadcaster.subscribe(run_id)

    async def event_generator():
        while True:
            event = await asyncio.to_thread(q.get)  # blocking get, off the event loop
            if event is None:
                yield "event: done\ndata: {}\n\n"
                break
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/", include_in_schema=False)
def serve_frontend():
    return FileResponse("frontend/index.html")
