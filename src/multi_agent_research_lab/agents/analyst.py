import logging
import time

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

logger = logging.getLogger(__name__)


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`."""
        logger.info("AnalystAgent executing...")
        start_time = time.perf_counter()

        if not state.research_notes:
            logger.warning("No research notes found in state for AnalystAgent.")
            state.errors.append("AnalystAgent: research_notes is empty.")
            return state

        try:
            llm = LLMClient()
            system_prompt = (
                "You are an expert technical analyst. Your task is to process technical research notes "
                "relative to a user query. Extract key technical claims, analyze underlying assumptions, "
                "synthesize insights, and explicitly flag any weak evidence or areas needing "
                "further verification."
            )
            user_prompt = (
                f"User Query: {state.request.query}\n\n"
                f"Research Notes:\n{state.research_notes}\n\n"
                "Please analyze the research notes and produce structured analysis insights."
            )

            response = llm.complete(system_prompt, user_prompt)
            latency = time.perf_counter() - start_time

            state.analysis_notes = response.content
            state.add_trace_event("analyst_execution", {
                "latency_seconds": latency,
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "cost_usd": response.cost_usd
            })
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.ANALYST,
                    content=response.content,
                    metadata={
                        "latency_seconds": latency,
                        "input_tokens": response.input_tokens,
                        "output_tokens": response.output_tokens,
                        "cost_usd": response.cost_usd
                    }
                )
            )
            logger.info("AnalystAgent completed successfully.")
        except Exception as e:
            logger.error(f"Error in AnalystAgent: {e}")
            state.errors.append(f"AnalystAgent error: {str(e)}")
            
        return state

