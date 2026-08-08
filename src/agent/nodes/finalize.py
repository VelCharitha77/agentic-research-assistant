from agent.state import AgentState


def finalize_node(state: AgentState) -> dict:
    sources_section = "\n".join(f"- {c.title} ({c.url})" for c in state.sources) or "(no sources)"
    final_document = f"{state.draft}\n\nSources:\n{sources_section}"
    return {"final_document": final_document, "status": "completed"}
