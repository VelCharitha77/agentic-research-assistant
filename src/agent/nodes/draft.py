from agent.llm_client import LLMClient
from agent.state import AgentState

_SYSTEM_PROMPT = (
    "You are a careful research writer. Write a clear, well-structured draft "
    "document on the given topic, grounded strictly in the provided research "
    "notes. Do not fabricate facts that aren't supported by the notes."
)


def _build_prompt(state: AgentState) -> str:
    notes = "\n".join(f"- {note}" for note in state.research_notes) or "(no research notes available)"
    return (
        f"Topic: {state.topic}\n\n"
        f"Research notes:\n{notes}\n\n"
        "Write a draft document (3-5 paragraphs) covering this topic based on "
        "the research notes above."
    )


def make_draft_node(llm_client: LLMClient):
    def draft_node(state: AgentState) -> dict:
        draft = llm_client.complete(system=_SYSTEM_PROMPT, prompt=_build_prompt(state))
        return {"draft": draft}

    return draft_node
