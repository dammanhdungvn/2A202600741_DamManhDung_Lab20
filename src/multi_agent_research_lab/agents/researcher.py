import logging
import time

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient

logger = logging.getLogger(__name__)


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`."""
        logger.info("ResearcherAgent executing...")
        start_time = time.perf_counter()

        try:
            # 1. Run search query
            search_client = SearchClient()
            sources = search_client.search(state.request.query, max_results=state.request.max_sources)
            state.sources = sources

            # Format sources text for the LLM
            sources_text = ""
            for idx, src in enumerate(sources, 1):
                sources_text += f"Source [{idx}]:\nTitle: {src.title}\nURL: {src.url}\nContent: {src.snippet}\n\n"

            # 2. Call LLM to summarize research
            llm = LLMClient()
            system_prompt = (
                "You are an expert technical researcher. Analyze the provided source documents "
                "relative to the user query. Extract key facts, definitions, and technical data. "
                "Structure your response as concise, bulleted research notes with explicit citations "
                "referencing the Source IDs [1], [2], etc."
            )
            user_prompt = (
                f"User Query: {state.request.query}\n\n"
                f"Source Documents:\n{sources_text}\n"
                "Please output detailed, structured research notes."
            )

            response = llm.complete(system_prompt, user_prompt)
            latency = time.perf_counter() - start_time

            # 3. Update state
            state.research_notes = response.content
            state.add_trace_event("researcher_execution", {
                "latency_seconds": latency,
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "cost_usd": response.cost_usd,
                "sources_found": len(sources)
            })
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.RESEARCHER,
                    content=response.content,
                    metadata={
                        "latency_seconds": latency,
                        "input_tokens": response.input_tokens,
                        "output_tokens": response.output_tokens,
                        "cost_usd": response.cost_usd
                    }
                )
            )
            logger.info("ResearcherAgent completed successfully.")
        except Exception as e:
            logger.error(f"Error in ResearcherAgent: {e}")
            state.errors.append(f"ResearcherAgent error: {str(e)}")
            
        return state

