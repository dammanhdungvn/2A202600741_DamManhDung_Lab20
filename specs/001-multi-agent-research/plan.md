# Implementation Plan: Multi-Agent Research System

**Branch**: `001-multi-agent-research` | **Date**: 2026-06-24 | **Spec**: [specs/001-multi-agent-research/spec.md](file:///home/dammanhdungvn/workspace/ai-in-action/day20/phase2-day5-multi-agent-lab/specs/001-multi-agent-research/spec.md)

**Input**: Feature specification from `specs/001-multi-agent-research/spec.md`

## Summary

We are building a Multi-Agent Research System using LangGraph. The system features a routing Supervisor coordinating three worker agents: Researcher (queries mock search service), Analyst (analyzes sources), and Writer (synthesizes the final response). We will benchmark this multi-agent workflow against a single-agent baseline using latency, cost, and citation quality metrics.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: `pydantic>=2.7`, `pydantic-settings>=2.3`, `typer>=0.12`, `rich>=13.7`, `tenacity>=8.3`, `langgraph>=0.2`, `openai>=1.40`

**Storage**: In-memory `ResearchState`

**Testing**: `pytest>=8.2`, `ruff>=0.5`, `mypy>=1.10`

**Target Platform**: Linux Server / CLI

**Project Type**: CLI / Python Library

**Performance Goals**:
- Single-agent baseline execution: < 10 seconds.
- Multi-agent workflow execution: < 60 seconds.

**Constraints**:
- Must strictly stay under the Nvidia API rate limit of 40 Requests Per Minute (RPM) by introducing throttling/sleep intervals between LLM requests.
- Loop execution must be bounded by `MAX_ITERATIONS` (6).
- Search API calls must fallback to mock data since external search keys are unavailable.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Gate I (Specialized Role Separation):** Passed. The roles (Supervisor, Researcher, Analyst, Writer) have distinct schemas and execution contexts.
- **Gate II (Shared State Integrity):** Passed. All data is passed via `ResearchState` rather than direct agent calling.
- **Gate III (Production-Grade Observability):** Passed. Step latency, inputs, outputs, token counts, and routing path are recorded in the state's `trace` and `route_history`.
- **Gate IV (Robust Guardrails & Rate Limits):** Passed. The implementation will include rate-limiting sleep logic (staying below 40 RPM) and a maximum of 6 loops limit.
- **Gate V (Mock and Environment Constraints):** Passed. Packages are managed via `uv` and `SearchClient.search` will return static mock results without making network requests.

## Project Structure

### Documentation (this feature)

```text
specs/001-multi-agent-research/
├── spec.md              # Feature specification
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks command)
```

### Source Code (repository root)

```text
src/multi_agent_research_lab/
├── agents/
│   ├── __init__.py
│   ├── supervisor.py
│   ├── researcher.py
│   ├── analyst.py
│   ├── writer.py
│   └── critic.py
├── core/
│   ├── __init__.py
│   ├── config.py
│   ├── errors.py
│   ├── schemas.py
│   └── state.py
├── graph/
│   ├── __init__.py
│   └── workflow.py
├── services/
│   ├── __init__.py
│   ├── llm_client.py
│   └── search_client.py
├── evaluation/
│   ├── __init__.py
│   ├── benchmark.py
│   └── report.py
├── observability/
│   ├── __init__.py
│   ├── logging.py
│   └── tracing.py
└── cli.py

tests/
├── test_agents_todo.py
├── test_config.py
├── test_report.py
└── test_state.py
```

**Structure Decision**: Single project layout matching the existing skeletal repository structure.

## Complexity Tracking

*No violations detected. All requirements align with the constitution.*
