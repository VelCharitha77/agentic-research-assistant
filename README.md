# Agentic Research Assistant

A production-grade LangGraph agent that takes a topic, researches it via a
search tool, drafts a document, critiques its own draft, and revises until
the critique passes or a revision cap is hit — served as a real API with
persistence, streaming progress, structured logging, and guardrails.

## Status

Complete — v0.1. Built in 14 incremental steps, each independently tested
and committed. Build log below tracks the actual engineering decisions
(including the mistakes and fixes) as the project progressed.

## Architecture

- **Orchestrator**: LangGraph `StateGraph` — Research -> Draft -> Critique ->
  Revise/Finalize loop, with a Fail path routed after Research exhausts its
  own retries (retry logic lives in the tool layer, not duplicated at the
  graph level).
- **API**: FastAPI, async, job-based (`POST /runs` returns immediately;
  `GET /runs/{id}` polls status; `GET /runs/{id}/stream` streams live
  per-node progress over SSE, with a 60s timeout guard against orphaned runs).
- **Persistence**: Postgres-backed LangGraph checkpointer — proven to
  survive a mid-run crash and resume without re-executing completed nodes.
- **LLM**: Anthropic Claude by default, OpenAI supported behind the same
  `LLMClient` interface via one config value (`LLM_PROVIDER`).
- **Observability**: structured JSON logs correlated by `run_id`, wrapped
  once around every node rather than scattered per-node.
- **Guardrails**: input validation on the topic field, a revision cap that's
  a hard safety limit (tested), and an explicit prompt-injection defense
  clause in every node that consumes untrusted web content.
- **Frontend**: a single static page with a live SSE-driven progress log.

## Quick Start (Docker)

The fastest way to run the whole stack — API, Postgres, everything:

```bash
cp .env.example .env   # then fill in your real ANTHROPIC_API_KEY and TAVILY_API_KEY
docker compose up -d --build
```

Open `http://localhost:8001/` in a browser.

## Local Development

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements-dev.txt
cp .env.example .env   # fill in real keys
docker compose up -d postgres
uvicorn agent.api.main:app --reload --app-dir src --port 8001
```

## Environment Variables

| Variable | Purpose | Default |
|---|---|---|
| `LLM_PROVIDER` | `anthropic` or `openai` | `anthropic` |
| `ANTHROPIC_API_KEY` | Required if using Anthropic | — |
| `ANTHROPIC_MODEL` | Anthropic model id | `claude-sonnet-4-5-20250929` |
| `OPENAI_API_KEY` | Required if using OpenAI | — |
| `OPENAI_MODEL` | OpenAI model id | `gpt-4o-2024-08-06` |
| `TAVILY_API_KEY` | Required — powers the Research node | — |
| `DATABASE_URL` | Postgres connection string | local docker-compose Postgres |
| `LOG_LEVEL` | Python logging level | `INFO` |

## Running Tests

```bash
pytest -v
```

The full suite runs against fakes only — zero real API calls, zero network
dependency — except `tests/test_checkpoint_resume.py`, which needs the local
Postgres container running (`docker compose up -d postgres`).

## Build Log

- Step 1: scaffolding, repo created.
- Step 2: dependencies + typed config (pydantic-settings), pytest wired to src/ layout.
- Step 3: state schema (AgentState, CritiqueResult, Citation) as Pydantic models for runtime validation.
- Step 4: LLM client abstraction (LLMClient interface, AnthropicLLMClient, FakeLLMClient) — nodes never touch the SDK directly.
- Step 5: search tool abstraction (SearchTool interface, TavilySearchTool, FakeSearchTool, RetryingSearchTool decorator with exponential backoff).
- Step 6: Research node (factory-injected SearchTool, fails cleanly to status="failed" when the retrying tool exhausts attempts — no duplicate retry logic at the graph level).
- Step 7: Draft node (complete()) and Critique node (complete_structured() -> CritiqueResult) — both fully unit-tested against FakeLLMClient, zero API calls in the test suite.
- Step 8: Revise node (increments revision_count), Finalize node (no factory needed, no external deps), and the two routing functions implementing the "approved? and iter<max?" decision logic.
- Step 9: assembled the full StateGraph end-to-end against fakes for the first time. Hit a real bug here: LangGraph only guarantees output keys that were in the initial input or written by an executed node — untouched schema defaults (e.g. revision_count on the no-revision happy path) silently vanished from invoke() results. Fixed with a create_initial_state() helper that always seeds the full state, not a partial dict.
- Step 10: Postgres-backed checkpointer (local via docker-compose) + a test that proves crash-recovery actually works — kills the run mid-Draft, restarts with a fresh process, and confirms Research does not re-execute.
- Step 11: FastAPI service layer — POST /runs returns 202 + run_id immediately, GET /runs/{id} polls status via LangGraph's own checkpointed state (no separate runs table needed). Graph injected via Depends() so tests never touch real Anthropic/Tavily/Postgres.
- Verified live end-to-end: real Tavily search + real Claude calls, self-critique triggered exactly one revision cycle before passing, final document correctly assembled with sources.
- Added OpenAI as a second LLMClient implementation behind the same interface, selected via LLM_PROVIDER — then made its SDK import lazy once it became clear Anthropic, not OpenAI, was the actual provider in use, so the dependency is architecturally optional rather than hard-required.
- Step 12: SSE streaming (/runs/{id}/stream) via an in-memory thread-safe broadcaster, plus a minimal browser frontend showing live node-by-node progress.
- Step 13: structured JSON logging (run_id-correlated, wrapped once around all nodes), input validation on the topic field, and a prompt-injection guardrail clause added to every node that consumes untrusted research content.
- Found and fixed a real reliability gap in the stream endpoint: a client reconnecting to a run orphaned by a server restart would hang forever waiting for events that could never arrive. Added a 60s timeout that surfaces a clear message instead.
- Restyled the frontend (forest/library theme: bark-textured background, parchment panel, SVG vine illustrations in two corners, Metamorphous display font) — and fixed a self-inflicted bug where `overflow: hidden` on body (added to contain the vine graphics) also silently broke page scrolling on long results.
- Step 14: Dockerized the full stack (non-root user, secrets injected via env_file at runtime rather than baked into the image, DATABASE_URL overridden for container networking), final README pass.
