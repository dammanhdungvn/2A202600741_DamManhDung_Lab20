from typing import Any

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.critic import CriticAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.core.state import ResearchState


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph."""

    def __init__(self) -> None:
        self.compiled_graph: CompiledStateGraph[Any, Any, Any, Any] | None = None

    def build(self) -> CompiledStateGraph[Any, Any, Any, Any]:
        """Create a LangGraph graph."""
        graph = StateGraph(ResearchState)

        # 1. Add agent nodes
        graph.add_node("supervisor", lambda state: SupervisorAgent().run(state))
        graph.add_node("researcher", lambda state: ResearcherAgent().run(state))
        graph.add_node("analyst", lambda state: AnalystAgent().run(state))
        graph.add_node("writer", lambda state: WriterAgent().run(state))
        graph.add_node("critic", lambda state: CriticAgent().run(state))

        # 2. Set entry point
        graph.set_entry_point("supervisor")

        # 3. Define conditional routing function
        def route_decision(state: ResearchState) -> str:
            if not state.route_history:
                return "researcher"  # Safe default if somehow empty
            last_route = state.route_history[-1]
            if last_route == "FINISH":
                return "END"
            return last_route

        # 4. Add conditional edges
        graph.add_conditional_edges(
            "supervisor",
            route_decision,
            {
                "researcher": "researcher",
                "analyst": "analyst",
                "writer": "writer",
                "critic": "critic",
                "END": END,
            },
        )

        # 5. Add direct edges from worker nodes back to supervisor
        graph.add_edge("researcher", "supervisor")
        graph.add_edge("analyst", "supervisor")
        graph.add_edge("writer", "supervisor")
        graph.add_edge("critic", "supervisor")

        self.compiled_graph = graph.compile()
        return self.compiled_graph

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state."""
        compiled = self.compiled_graph if self.compiled_graph is not None else self.build()

        # Invoke compiled LangGraph
        result: Any = compiled.invoke(state)

        # Convert result back to ResearchState safely
        if isinstance(result, ResearchState):
            return result
        if isinstance(result, dict):
            return ResearchState(**result)

        raise TypeError(f"Unexpected result type from graph: {type(result)}")
