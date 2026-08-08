from agent.state import AgentState


def route_after_research(state: AgentState) -> str:
    if state.status == "failed":
        return "failed"
    return "draft"


def make_route_after_critique(max_revisions: int = 3):
    def route_after_critique(state: AgentState) -> str:
        if state.critique is None:
            raise ValueError("route_after_critique called before critique was set")
        if state.critique.verdict == "pass":
            return "finalize"
        if state.revision_count < max_revisions:
            return "revise"
        return "finalize"

    return route_after_critique
