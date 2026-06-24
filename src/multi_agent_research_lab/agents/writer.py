import logging
import time

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

logger = logging.getLogger(__name__)


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`."""
        logger.info("WriterAgent executing...")
        start_time = time.perf_counter()

        if not state.research_notes or not state.analysis_notes:
            logger.warning("Missing research_notes or analysis_notes in state for WriterAgent.")
            state.errors.append("WriterAgent: missing research_notes or analysis_notes.")
            return state

        try:
            llm = LLMClient()
            system_prompt = (
                "You are an expert technical writer. Synthesize the provided research notes "
                "and analysis insights into a coherent, highly readable final report. "
                "The report must target the specified audience level. You MUST include explicit inline citations "
                "referencing the source documents (e.g., [1], [2]) and provide a References section at the end."
            )
            
            # Format sources metadata list for references
            sources_text = ""
            for idx, src in enumerate(state.sources, 1):
                sources_text += f"[{idx}] {src.title} - {src.url or 'No Link'}\n"

            user_prompt = (
                f"User Query: {state.request.query}\n"
                f"Audience: {state.request.audience}\n\n"
                f"Research Notes:\n{state.research_notes}\n\n"
                f"Analysis Insights:\n{state.analysis_notes}\n\n"
                f"Source Sources List:\n{sources_text}\n"
                "Please output the final synthesized report."
            )

            response = llm.complete(system_prompt, user_prompt)
            latency = time.perf_counter() - start_time

            state.final_answer = response.content
            state.add_trace_event("writer_execution", {
                "latency_seconds": latency,
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "cost_usd": response.cost_usd
            })
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.WRITER,
                    content=response.content,
                    metadata={
                        "latency_seconds": latency,
                        "input_tokens": response.input_tokens,
                        "output_tokens": response.output_tokens,
                        "cost_usd": response.cost_usd
                    }
                )
            )
            logger.info("WriterAgent completed successfully.")
        except Exception as e:
            logger.error(f"Error in WriterAgent: {e}")
            state.errors.append(f"WriterAgent error: {str(e)}")
            
        return state

