"""Command-line entrypoint for the lab starter."""

from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console()


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a minimal single-agent baseline."""

    import time

    from multi_agent_research_lab.core.schemas import AgentName, AgentResult
    from multi_agent_research_lab.services.llm_client import LLMClient

    _init()
    request = ResearchQuery(query=query)
    state = ResearchState(request=request)

    console.print("[blue]Running single-agent baseline (1 LLM call)...[/blue]")
    start_time = time.perf_counter()
    
    try:
        llm = LLMClient()
        system_prompt = (
            "You are a professional research assistant. Research the user query, analyze findings, "
            "and write a detailed, synthesized final response with citations to sources."
        )
        user_prompt = f"Query: {query}"
        
        response = llm.complete(system_prompt, user_prompt)
        latency = time.perf_counter() - start_time
        
        state.final_answer = response.content
        state.add_trace_event("baseline_run", {
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
        
        console.print(Panel.fit(state.final_answer, title="Single-Agent Baseline Result"))
        console.print(f"[green]Latency:[/green] {latency:.2f}s | [green]Tokens:[/green] In:{response.input_tokens} Out:{response.output_tokens} | [green]Cost:[/green] ${response.cost_usd:.6f}")
    except Exception as e:
        console.print(Panel.fit(f"Error during baseline run: {e}", title="Error", style="red"))
        raise typer.Exit(code=1) from e



@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow and save a local trace file."""
    from multi_agent_research_lab.observability.tracing import save_trace_to_json

    _init()
    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    try:
        result = workflow.run(state)
    except StudentTodoError as exc:
        console.print(Panel.fit(str(exc), title="Expected TODO", style="yellow"))
        raise typer.Exit(code=2) from exc

    # Save local trace
    trace_path = save_trace_to_json(result.trace, run_name="multi_agent")
    console.print(result.model_dump_json(indent=2))
    console.print(f"\n[green]Trace saved to:[/green] {trace_path}")
    console.print(f"[green]Route path:[/green] {' -> '.join(result.route_history)}")


@app.command("benchmark")
def benchmark(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run both single-agent and multi-agent, compare, and save report."""
    
    import os
    import time

    from multi_agent_research_lab.core.schemas import AgentName, AgentResult, ResearchQuery
    from multi_agent_research_lab.evaluation.benchmark import run_benchmark
    from multi_agent_research_lab.evaluation.report import render_markdown_report
    from multi_agent_research_lab.services.llm_client import LLMClient

    _init()
    console.print("[bold green]Starting Benchmark Suite...[/bold green]")
    
    # Define Baseline Runner
    def run_baseline(q: str) -> ResearchState:
        llm = LLMClient()
        system_prompt = (
            "You are a professional research assistant. Research the user query, analyze findings, "
            "and write a detailed, synthesized final response with citations to sources."
        )
        user_prompt = f"Query: {q}"
        state = ResearchState(request=ResearchQuery(query=q))
        
        start_time = time.perf_counter()
        response = llm.complete(system_prompt, user_prompt)
        latency = time.perf_counter() - start_time
        
        state.final_answer = response.content
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
        return state

    # Define Multi-Agent Runner
    def run_multi_agent(q: str) -> ResearchState:
        state = ResearchState(request=ResearchQuery(query=q))
        workflow = MultiAgentWorkflow()
        return workflow.run(state)

    try:
        # 1. Run Baseline
        console.print("[blue]Running Single-Agent Baseline...[/blue]")
        state_baseline, metrics_baseline = run_benchmark("Single-Agent Baseline", query, run_baseline)
        
        # 2. Run Multi-Agent
        console.print("[blue]Running Multi-Agent Workflow...[/blue]")
        state_multi, metrics_multi = run_benchmark("Multi-Agent Workflow", query, run_multi_agent)
        
        # Render markdown report
        report_markdown = render_markdown_report([metrics_baseline, metrics_multi])
        
        # Ensure reports/ directory exists
        os.makedirs("reports", exist_ok=True)
        report_path = "reports/benchmark_report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_markdown)
            
        console.print(Panel.fit(report_markdown, title="Benchmark Report Results"))
        console.print(f"[bold green]Report saved successfully to {report_path}[/bold green]")
        
    except Exception as e:
        console.print(Panel.fit(f"Error during benchmark: {e}", title="Error", style="red"))
        raise typer.Exit(code=1) from e


if __name__ == "__main__":
    app()

