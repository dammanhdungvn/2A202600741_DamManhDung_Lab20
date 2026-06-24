import json
import logging
import time

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import AgentName
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

logger = logging.getLogger(__name__)


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def run(self, state: ResearchState) -> ResearchState:
        """Update `state.route_history` with the next route."""
        logger.info(f"SupervisorAgent executing (Iteration: {state.iteration})...")
        start_time = time.perf_counter()

        settings = get_settings()
        
        # Enforce max iterations guardrail
        if state.iteration >= settings.max_iterations:
            logger.warning("Max iterations reached. Supervisor forcing FINISH.")
            state.record_route("FINISH")
            return state

        # Determine default programmatic route for fallback
        if not state.research_notes:
            default_next = "researcher"
        elif not state.analysis_notes:
            default_next = "analyst"
        elif not state.final_answer:
            default_next = "writer"
        elif not any(res.agent == AgentName.CRITIC for res in state.agent_results):
            default_next = "critic"
        else:
            default_next = "FINISH"

        next_agent = default_next

        try:
            llm = LLMClient()
            system_prompt = (
                "You are the Supervisor coordinator for a Multi-Agent Research System.\n"
                "Your job is to inspect the current state of the research task and choose the next node.\n"
                "Available nodes:\n"
                "- 'researcher': gathers search source documents and drafts research notes.\n"
                "- 'analyst': processes research notes into structured insights.\n"
                "- 'writer': synthesizes research and analysis notes into a final technical report.\n"
                "- 'critic': reviews and fact-checks the final report against the sources.\n"
                "- 'FINISH': terminate the workflow and output the final result.\n\n"
                "Strict Prompt Instructions:\n"
                "You MUST select from the available options. Output ONLY a valid JSON object in the format: "
                '{"next_agent": "<agent_name>"}. Keep explanations out of the response.'
            )
            
            # Format high-level state representation for the LLM
            state_summary = {
                "has_sources": len(state.sources) > 0,
                "has_research_notes": state.research_notes is not None,
                "has_analysis_notes": state.analysis_notes is not None,
                "has_final_answer": state.final_answer is not None,
                "critic_run": any(res.agent == AgentName.CRITIC for res in state.agent_results)
            }
            
            user_prompt = (
                f"Original User Request: {state.request.query}\n"
                f"State Summary: {json.dumps(state_summary)}\n"
                f"Route History: {state.route_history}\n\n"
                "Which agent node should execute next?"
            )

            response = llm.complete(system_prompt, user_prompt)
            latency = time.perf_counter() - start_time
            
            # Parse next agent from JSON response
            try:
                data = json.loads(response.content.strip())
                selected_agent = data.get("next_agent", "").lower()
                
                # Validation of selection
                valid_selections = {"researcher", "analyst", "writer", "critic", "finish"}
                if selected_agent in valid_selections:
                    # Map 'finish' string to standard FINISH
                    next_agent = "FINISH" if selected_agent == "finish" else selected_agent
                    logger.info(f"Supervisor agentically routed to: {next_agent}")
                else:
                    logger.warning(f"Invalid agent selection: {selected_agent}. Using fallback: {default_next}")
            except Exception as parse_err:
                logger.warning(f"Could not parse supervisor output: {response.content}. Error: {parse_err}. Using fallback.")

            # Update trace events
            state.add_trace_event("supervisor_decision", {
                "latency_seconds": latency,
                "input_tokens": response.input_tokens,
                "outputs_tokens": response.output_tokens,
                "cost_usd": response.cost_usd,
                "route_decision": next_agent
            })
            
        except Exception as e:
            logger.error(f"Error in SupervisorAgent API call: {e}. Defaulting to fallback: {default_next}")
            state.errors.append(f"SupervisorAgent warning: {str(e)}")

        state.record_route(next_agent)
        return state

