import logging
import time

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

logger = logging.getLogger(__name__)


class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent."""

    name = "critic"

    def run(self, state: ResearchState) -> ResearchState:
        """Validate final answer and append findings."""
        logger.info("CriticAgent executing...")
        start_time = time.perf_counter()

        if not state.final_answer:
            logger.warning("No final answer found to critique.")
            state.errors.append("CriticAgent: final_answer is empty.")
            return state

        try:
            # Format sources text for the critic to verify
            sources_text = ""
            for idx, src in enumerate(state.sources, 1):
                sources_text += f"Source [{idx}]:\nTitle: {src.title}\nContent: {src.snippet}\n\n"

            llm = LLMClient()
            system_prompt = (
                "You are an expert fact-checker and critic. Analyze the final technical report "
                "relative to the provided source snippets. Check if the report contains any "
                "hallucinations, unsourced claims, or contradictions. Format your output as a validation critique."
            )
            user_prompt = (
                f"Source Documents:\n{sources_text}\n\n"
                f"Final Technical Report:\n{state.final_answer}\n\n"
                "Please critique the report. If there are no issues, reply with: 'PASSED fact-check verification.'"
            )

            response = llm.complete(system_prompt, user_prompt)
            latency = time.perf_counter() - start_time

            # Update trace and agent results
            state.add_trace_event("critic_execution", {
                "latency_seconds": latency,
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "cost_usd": response.cost_usd,
                "passed": "passed fact-check" in response.content.lower()
            })
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.CRITIC,
                    content=response.content,
                    metadata={
                        "latency_seconds": latency,
                        "input_tokens": response.input_tokens,
                        "output_tokens": response.output_tokens,
                        "cost_usd": response.cost_usd
                    }
                )
            )
            logger.info("CriticAgent completed successfully.")
        except Exception as e:
            logger.error(f"Error in CriticAgent: {e}")
            state.errors.append(f"CriticAgent error: {str(e)}")
            
        return state

