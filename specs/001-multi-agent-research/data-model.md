# Data Model: Multi-Agent Research System

This document describes the structured models and shared state used across the Multi-Agent Research System.

## Entities

### 1. ResearchQuery

Input parameters representing the user's research request.

| Field | Type | Description | Validation |
|---|---|---|---|
| `query` | `str` | The research prompt/question | Minimum length: 5 characters |
| `max_sources` | `int` | Maximum number of search references to fetch | Range: 1 to 20, Default: 5 |
| `audience` | `str` | The target reading level of the final output | Default: `"technical learners"` |

### 2. SourceDocument

Represents a retrieved search result reference.

| Field | Type | Description |
|---|---|---|
| `title` | `str` | Document title |
| `url` | `str | None` | Source link |
| `snippet` | `str` | Excerpt of document contents |
| `metadata` | `dict` | Additional properties (e.g. source credibility, crawl date) |

### 3. AgentResult

Logs a single agent run output for history tracking and billing/cost calculations.

| Field | Type | Description |
|---|---|---|
| `agent` | `AgentName` | Enum value matching `supervisor`, `researcher`, `analyst`, `writer`, `critic` |
| `content` | `str` | Text content produced by the agent |
| `metadata` | `dict` | Token count usage, latency, and model settings |

### 4. ResearchState

The central shared state carried between LangGraph nodes.

| Field | Type | Description |
|---|---|---|
| `request` | `ResearchQuery` | The input research parameters |
| `iteration` | `int` | Counter tracking the number of node execution iterations |
| `route_history` | `list[str]` | Execution path of agent nodes visited |
| `sources` | `list[SourceDocument]` | Collected references accumulated by Researcher |
| `research_notes` | `str | None` | Consolidated notes from Researcher |
| `analysis_notes` | `str | None` | Extracted claims and viewpoints from Analyst |
| `final_answer` | `str | None` | Synthetic report from Writer |
| `agent_results` | `list[AgentResult]` | Complete execution trace of agent outputs |
| `trace` | `list[dict]` | Low-level tracing event timestamps and latency data |
| `errors` | `list[str]` | List of error messages captured during agent runs |

## State Transitions

```mermaid
stateflow
[*] --> request
request --> ResearchState: Initialized
ResearchState --> Supervisor: Read State
Supervisor --> Researcher: Route to "researcher"
Researcher --> ResearchState: Update "sources" & "research_notes"
ResearchState --> Supervisor: Read State
Supervisor --> Analyst: Route to "analyst" (if research exists)
Analyst --> ResearchState: Update "analysis_notes"
ResearchState --> Supervisor: Read State
Supervisor --> Writer: Route to "writer" (if analysis exists)
Writer --> ResearchState: Update "final_answer"
ResearchState --> Supervisor: Read State
Supervisor --> [*]: Route to "FINISH" or max_iterations reached
```
