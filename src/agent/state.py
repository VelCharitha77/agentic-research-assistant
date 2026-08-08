from typing import Literal, Optional

from pydantic import BaseModel, Field


class Citation(BaseModel):
    url: str
    title: str
    snippet: str = ""


class CritiqueResult(BaseModel):
    verdict: Literal["pass", "fail"]
    issues: list[str] = Field(default_factory=list)


class AgentState(BaseModel):
    run_id: str
    topic: str
    research_notes: list[str] = Field(default_factory=list)
    sources: list[Citation] = Field(default_factory=list)
    draft: str = ""
    critique: Optional[CritiqueResult] = None
    revision_count: int = 0
    final_document: Optional[str] = None
    status: Literal["running", "completed", "failed"] = "running"
    error: Optional[str] = None


def create_initial_state(run_id: str, topic: str) -> dict:
    """The only correct way to build a graph's initial input: a full dict of
    every field's default, not a partial dict of just what the caller cares
    about. LangGraph only guarantees a key exists in the final result if it
    was in the initial input or written by some node — untouched defaults
    on a partial input can silently vanish from the output."""
    return AgentState(run_id=run_id, topic=topic).model_dump()
