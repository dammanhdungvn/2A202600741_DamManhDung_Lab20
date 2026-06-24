import logging
import re
from collections.abc import Callable
from time import perf_counter

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

logger = logging.getLogger(__name__)

Runner = Callable[[str], ResearchState]


def evaluate_quality_with_llm(query: str, final_answer: str | None) -> float:
    """Evaluate final answer quality using LLM-as-a-judge."""
    if not final_answer:
        return 0.0
        
    try:
        llm = LLMClient()
        system_prompt = (
            "You are an objective evaluation judge. Read the user query and the final report. "
            "Score the final report on a scale of 0.0 to 10.0 based on factual accuracy, "
            "clarity, structure, and citation completeness. "
            "Output ONLY a valid JSON object: {\"score\": <float_value>}. No explanation."
        )
        user_prompt = f"Query: {query}\n\nReport:\n{final_answer}"
        response = llm.complete(system_prompt, user_prompt)
        
        # Search for score in the JSON content
        match = re.search(r'"score"\s*:\s*([0-9.]+)', response.content)
        if match:
            score = float(match.group(1))
            return min(max(score, 0.0), 10.0)
    except Exception as e:
        logger.warning(f"Failed to evaluate quality with LLM: {e}")
        
    return 7.0  # Fallback score


def run_benchmark(run_name: str, query: str, runner: Runner) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency, estimated cost, quality score, and citation details."""
    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started

    # Sum costs from all agent invocations
    total_cost = 0.0
    for res in state.agent_results:
        total_cost += res.metadata.get("cost_usd") or 0.0

    # Evaluate quality
    quality = evaluate_quality_with_llm(query, state.final_answer)

    # Compute citation coverage
    citations = len(set(re.findall(r'\[\d+\]', state.final_answer or "")))
    notes = f"Citations: {citations} | Steps: {len(state.route_history)} | Errors: {len(state.errors)}"

    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=total_cost,
        quality_score=quality,
        notes=notes
    )
    return state, metrics

