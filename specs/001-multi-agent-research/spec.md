# Feature Specification: Multi-Agent Research System

**Feature Branch**: `001-multi-agent-research`

**Created**: 2026-06-24

**Status**: Draft

**Input**: User description: "Implement the Multi-Agent Research System using LangGraph with LLM client, search mock, routing, and benchmarking against a single-agent baseline."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Single-Agent Baseline Execution (Priority: P1)

The user wants to run a simple, single-agent baseline search query to get a quick summary. This serves as our comparative baseline for the multi-agent system.

**Why this priority**: Crucial MVP milestone. Establishing a baseline first allows us to compare performance, quality, and latency.

**Independent Test**: Can be run via CLI using `python -m multi_agent_research_lab.cli baseline --query "Research GraphRAG state-of-the-art"`, which invokes a single LLM call and outputs the result.

**Acceptance Scenarios**:

1. **Given** a valid `.env` with Nvidia API credentials, **When** the user runs the baseline command with a query, **Then** the system returns a coherent research response from the LLM, logs latency/cost, and displays the output.
2. **Given** a query under 5 characters, **When** the user executes the command, **Then** the system rejects it with a validation error.

---

### User Story 2 - Multi-Agent Workflow Execution (Priority: P2)

The user wants to run a comprehensive research task where specialized agents collaborate (Supervisor routes, Researcher gathers sources, Analyst compares views, Writer synthesizes).

**Why this priority**: Core value of the multi-agent lab. Demonstrates specialized role division and cooperative state handoffs.

**Independent Test**: Can be run via CLI using `python -m multi_agent_research_lab.cli multi-agent --query "Research GraphRAG state-of-the-art"`.

**Acceptance Scenarios**:

1. **Given** a multi-agent run command, **When** the workflow is initiated, **Then** the Supervisor agent routes the query to the Researcher, the Researcher adds mock search results to state, the Analyst extracts key claims, and the Writer synthesizes the final report with citations.
2. **Given** the workflow is executing, **When** a step is called, **Then** it respects the Nvidia rate limit of 40 RPM by throttling/delaying if necessary.
3. **Given** an agent loop exceeds 6 iterations, **When** execution is running, **Then** the system terminates gracefully using iteration guardrails to prevent infinite loops.

---

### User Story 3 - Trace and Benchmarking Report (Priority: P3)

The user wants to evaluate the quality, cost, and latency difference between single-agent and multi-agent runs.

**Why this priority**: Required for lab evaluation and verification of the system's benefits.

**Independent Test**: Running the benchmark suite produces a detailed `reports/benchmark_report.md` comparing both methods.

**Acceptance Scenarios**:

1. **Given** both baseline and multi-agent runs have completed, **When** the benchmark script runs, **Then** a markdown table is generated with Latency, Token Cost, Citation Coverage, and Quality Score, and is saved to `reports/benchmark_report.md`.

---

### Edge Cases

- **Nvidia API Rate Limit (429):** The LLM client must automatically handle rate limits of 40 RPM via backing off and retrying using tenacity or delays, preventing execution crash.
- **Search Client Mock Behavior:** When `TAVILY_API_KEY` is not present, the system MUST gracefully fall back to mock search data and continue, rather than failing on key errors.
- **State Handoff Failures:** If an agent returns invalid schemas or fails to produce output, the Supervisor must catch the exception and log the error into the state.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: LLM Client implementation MUST connect to `https://integrate.api.nvidia.com/v1` using `openai/gpt-oss-120b` and handle completions using environment credentials.
- **FR-002**: Search Client implementation MUST fallback to local mock data (producing realistic technical snippets for `SourceDocument`) when Tavily search API key is not configured.
- **FR-003**: System MUST implement a routing agent (Supervisor) that reads the current `ResearchState` and returns the next agent node or finish signal.
- **FR-004**: System MUST implement worker nodes (Researcher, Analyst, Writer) using the `LLMClient` to process prompts and update state fields (`research_notes`, `analysis_notes`, `final_answer`).
- **FR-005**: LangGraph Workflow MUST compile the supervisor and worker nodes into a state graph with conditional edges.
- **FR-006**: System MUST enforce guardrails, limiting execution to `MAX_ITERATIONS` (6) and a total run timeout of `TIMEOUT_SECONDS` (60) to prevent runaway processes.
- **FR-007**: LLM Client calls MUST be rate-limited/throttled to remain strictly under the 40 Requests Per Minute (RPM) ceiling.
- **FR-008**: System MUST support local JSON logging/tracing for each execution step, tracking agent name, duration, and token usage metrics.
- **FR-009**: Benchmark suite MUST execute baseline and multi-agent queries, compile performance stats, and write them to `reports/benchmark_report.md`.

### Key Entities

- **ResearchState**: The shared, mutable state containing the original `request` query, `iteration` counter, `sources` list, individual agent outputs (`research_notes`, `analysis_notes`, `final_answer`), logs/traces, and any errors.
- **SourceDocument**: A structure representing a single reference source, containing `title`, `url`, `snippet`, and optional metadata.
- **AgentResult**: Recorded results of a single agent invocation, tracking agent identity, text output, and metadata.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `make test` runs and all unit tests pass with 100% success rate.
- **SC-002**: The baseline command terminates in under 10 seconds for a typical query, showing a single LLM response.
- **SC-003**: The multi-agent command finishes successfully in under 60 seconds, staying within the 40 RPM rate limit without triggering any HTTP 429 responses.
- **SC-004**: The benchmark suite compiles and correctly outputs `reports/benchmark_report.md` comparing latency, estimated cost, and citation quality.

## Assumptions

- Python 3.11 with `uv` package manager is available on the machine.
- Nvidia API key is valid and configured in the `.env` file.
- Tracing tools (LangSmith/Langfuse) are optional; local file-based and terminal tracing is the fallback default.
