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
    status: Literal["running", "completed", "failed"] = "running"
    error: Optional[str] = None
