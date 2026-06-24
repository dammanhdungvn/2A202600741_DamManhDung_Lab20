<!--
### Sync Impact Report
- Version change: template -> 1.0.0
- List of modified principles:
  - [PRINCIPLE_1_NAME] -> I. Specialized Role Separation
  - [PRINCIPLE_2_NAME] -> II. Shared State Integrity
  - [PRINCIPLE_3_NAME] -> III. Production-Grade Observability
  - [PRINCIPLE_4_NAME] -> IV. Robust Guardrails & Rate Limits
  - [PRINCIPLE_5_NAME] -> V. Mock and Environment Constraints
- Added sections: Technical Constraints, Development Workflow
- Removed sections: None
- Templates requiring updates:
  - .specify/templates/plan-template.md: ✅ updated
  - .specify/templates/spec-template.md: ✅ updated
  - .specify/templates/tasks-template.md: ✅ updated
- Follow-up TODOs: None
-->

# Multi-Agent Research System Constitution

## Core Principles

### I. Specialized Role Separation
Every agent in the system must have a clearly defined, non-overlapping responsibility. The system consists of a Supervisor (routing and coordination), Researcher (information gathering), Analyst (critical analysis), and Writer (final synthesis). Introducing new agents requires strong architectural justification.

### II. Shared State Integrity
All agent handoffs and communications must occur strictly through the shared `ResearchState` schema. Direct agent-to-agent message passing is prohibited. The shared state must be clean, structured, and easy to audit/debug.

### III. Production-Grade Observability
Every run and agent step must log its input/output tokens, execution latency, and routing decisions. Tracing via LangSmith/Langfuse is highly recommended, and local JSON tracing must be supported at all times.

### IV. Robust Guardrails & Rate Limits
To prevent infinite loops, cost overruns, and API lockouts:
- Every loop must enforce a `MAX_ITERATIONS` limit (default 6).
- Every run must respect a timeout threshold (default 60 seconds).
- LLM client calls must respect the Nvidia API rate limit of 40 Requests Per Minute (RPM) with appropriate sleep or throttle mechanisms.

### V. Mock and Environment Constraints
- Packages must be managed via the `uv` tool.
- External dependencies like web search must support local mocks (e.g. `SearchClient.search`) when API keys (like Tavily) are unavailable.
- Secrets, model config, and base URLs must be loaded exclusively via environment variables (`.env`) rather than hardcoded.

## Technical Constraints

- **Language & Runtime:** Python >= 3.11 with `uv` for package management.
- **LLM Provider:** Nvidia API endpoint (`https://integrate.api.nvidia.com/v1`) using `openai/gpt-oss-120b`.
- **Rate Limiting:** Must implement delay or retry logic to strictly stay below 40 RPM.
- **Search Provider:** Local mock implementation for `SearchClient` to avoid dependency on paid search API keys.

## Development Workflow

- **Testing Discipline:** Run `pytest` to verify skeleton and functional components.
- **Code Quality:** Use `ruff` for formatting and linting, `mypy` for strict typechecking.
- **Verification:** Compare Single-Agent vs Multi-Agent system performance using latency, cost, and citation quality metrics.

## Governance

- The Constitution is the single source of truth for design constraints.
- Amendments to this constitution must be documented, increment the version under semantic versioning rules, and be reflected across all templates.

**Version**: 1.0.0 | **Ratified**: 2026-06-24 | **Last Amended**: 2026-06-24
