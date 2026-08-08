# Agentic Research Assistant

A production-grade LangGraph agent that takes a topic, researches it via a
search tool, drafts a document, critiques its own draft, and revises until
the critique passes or a revision cap is hit.

## Status

Step 1 of 14: project scaffolding. Build log below tracks engineering
decisions as the project progresses.

## Architecture

- **Orchestrator**: LangGraph `StateGraph` (Research -> Draft -> Critique ->
  Revise/Finalize loop, with a retry edge on tool failure)
- **API**: FastAPI, async, job-based (`POST /runs`, `GET /runs/{id}`)
- **Persistence**: Postgres-backed LangGraph checkpointer
- **LLM**: Anthropic Claude

## Build Log

- Step 1: scaffolding, repo created.
- Step 2: dependencies + typed config (pydantic-settings), pytest wired to src/ layout.
- Step 3: state schema (AgentState, CritiqueResult, Citation) as Pydantic models for runtime validation.
- Step 4: LLM client abstraction (LLMClient interface, AnthropicLLMClient, FakeLLMClient) — nodes never touch the SDK directly.
- Step 5: search tool abstraction (SearchTool interface, TavilySearchTool, FakeSearchTool, RetryingSearchTool decorator with exponential backoff).
- Step 6: Research node (factory-injected SearchTool, fails cleanly to status="failed" when the retrying tool exhausts attempts — no duplicate retry logic at the graph level).
