# Design Template: Multi-Agent Research System

## Problem

The system needs to process complex research queries that require: (1) gathering multi-source information, (2) critically analyzing conflicting or complementary viewpoints, and (3) synthesizing a well-cited final report. A single LLM call cannot do all three reliably in one pass — it tends to either hallucinate citations, lack depth in analysis, or miss contradictions between sources.

## Why multi-agent?

A single-agent approach issues one zero-shot LLM call with a large prompt. The model must simultaneously retrieve knowledge, analyze it, and write — leading to:
- Shallow analysis depth
- Hallucinated or absent citations
- No validation step for factual accuracy

A multi-agent approach distributes this cognitive load across specialized roles:
- **Researcher**: focused on sourcing (uses SearchClient)
- **Analyst**: focused on critical thinking (uses LLM over notes)
- **Writer**: focused on synthesis (uses LLM over analysis)
- **Critic**: focused on fact-checking (validates against sources)

Each step improves on the previous, producing a higher-quality, better-cited output at the cost of more LLM calls and latency.

## Agent roles

| Agent | Responsibility | Input | Output | Failure mode |
|---|---|---|---|---|
| Supervisor | Routes query to correct next agent; enforces iteration cap | `ResearchState` (full) | Updated `route_history`, new `iteration` | LLM parse error → deterministic fallback routing |
| Researcher | Searches sources; generates research notes with citations | `request.query`, `SearchClient` | `state.sources`, `state.research_notes` | Search fails → empty sources; LLM error → error logged |
| Analyst | Analyzes research notes; extracts claims & flags gaps | `state.research_notes` | `state.analysis_notes` | Empty notes → skips with error; LLM error → error logged |
| Writer | Synthesizes final report with inline citations | `state.research_notes`, `state.analysis_notes`, `state.sources` | `state.final_answer` | Missing notes → skips with error; LLM error → error logged |
| Critic | Fact-checks final report against source snippets | `state.final_answer`, `state.sources` | Critique appended to `state.agent_results` | Empty answer → skips; LLM error → error logged |

## Shared state

`ResearchState` fields and their purpose:

| Field | Type | Purpose |
|---|---|---|
| `request` | `ResearchQuery` | Original query, max_sources, audience level |
| `iteration` | `int` | Track loop count for guardrail enforcement |
| `route_history` | `list[str]` | Full audit trail of routing decisions |
| `sources` | `list[SourceDocument]` | Mock search results for researcher |
| `research_notes` | `str \| None` | Researcher's structured output |
| `analysis_notes` | `str \| None` | Analyst's structured output |
| `final_answer` | `str \| None` | Writer's synthesized report |
| `agent_results` | `list[AgentResult]` | Per-agent content + token/cost metadata |
| `trace` | `list[dict]` | Span events with latency timestamps |
| `errors` | `list[str]` | Non-fatal errors captured during execution |

## Routing policy

```
START
  └─► Supervisor
        ├── research_notes missing? → Researcher → (back to Supervisor)
        ├── analysis_notes missing? → Analyst → (back to Supervisor)
        ├── final_answer missing?   → Writer → (back to Supervisor)
        ├── no Critic run yet?      → Critic → (back to Supervisor)
        └── all done?               → FINISH
```

Programmatic fallback is used when the LLM routing response cannot be parsed as valid JSON `{"next_agent": "..."}`.

## Guardrails

- **Max iterations:** 6 (configurable via `MAX_ITERATIONS` env var). Supervisor routes to FINISH immediately when `state.iteration >= max_iterations`.
- **Timeout:** 60 seconds total (configurable via `TIMEOUT_SECONDS`). LangGraph handles the overall call, individual agents implement fast-fail error catching.
- **Retry:** `tenacity` wraps each LLM API call with 3 retries and exponential backoff (2–10s delay).
- **Fallback:** If Supervisor LLM call fails, deterministic programmatic routing is applied based on current state fields.
- **Validation:** Each agent validates that its required input fields are present before making LLM calls. If inputs are missing, errors are logged and state is returned unchanged.

## Benchmark plan

**Queries tested:**
1. `"Research GraphRAG state-of-the-art and write a 500-word summary"`

**Metrics:**

| Metric | Measurement Method |
|---|---|
| Latency (s) | `wall-clock time from start to final state` |
| Cost (USD) | Sum of `cost_usd` from all `agent_results.metadata` |
| Quality Score (0-10) | LLM-as-a-judge: scores factual accuracy, clarity, citations |
| Citation Coverage | Count of `[N]` inline citation markers in `final_answer` |
| Failure Rate | Count of entries in `state.errors` |
| Route Steps | Length of `state.route_history` |

**Expected outcomes:**
- Single-agent: lower latency (~30s), lower cost (<$0.003), lower citation count (0-2), quality ~7/10
- Multi-agent: higher latency (~120s), higher cost (~$0.01), higher citation count (3-5), quality ~8.5/10
