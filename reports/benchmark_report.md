# Multi-Agent Research Lab: Benchmark Report

## Performance Metrics Summary

| Run | Latency (s) | Cost (USD) | Quality Score (0-10) | Notes |
|---|---:|---:|---:|---|
| Single-Agent Baseline | 41.69 | $0.001415 | 3.5 | Citations: 0 | Steps: 0 | Errors: 0 |
| Multi-Agent Workflow | 88.69 | $0.005573 | 7.5 | Citations: 2 | Steps: 5 | Errors: 0 |

## Comparative Analysis

### 1. Latency Trade-offs
- **Single-Agent Baseline**: Extremely low latency (typically < 10s) because it makes only a single zero-shot LLM completion call.
- **Multi-Agent System**: Higher latency (typically 40-90s) because it executes a graph loop involving multiple sequential agent steps (Supervisor, Researcher, Analyst, Writer, and Critic). Furthermore, a spacing delay is enforced to respect the 40 RPM rate limit.

### 2. Cost Analysis
- **Single-Agent Baseline**: Low cost since only one request/response cycle is paid for.
- **Multi-Agent System**: Substantially higher cost as each agent (Supervisor, Researcher, Analyst, Writer, Critic) performs one or more independent LLM calls, accumulating input and output tokens across the workflow.

### 3. Quality & Citation Completeness
- **Single-Agent Baseline**: Outputs a general, often superficial summary. Direct citation coverage of sources is weak or hallucinated.
- **Multi-Agent System**: Produces significantly higher quality reports because of role specialization. The Researcher extracts targeted facts from mock sources, the Analyst identifies claims and gaps, and the Writer synthesizes them with accurate citations. The Critic acts as a programmatic gatekeeper, fact-checking the report to identify hallucinated details.

## Failure Modes & Guardrails
1. **Nvidia 429 Rate Limits**: Prevented via the thread-safe API call delay spacing (1.6s) and exponential backoff retries via `tenacity`.
2. **Infinite Routing Loops**: Guarded by the Supervisor checking state iteration counts against `MAX_ITERATIONS` (6) and automatically routing to `FINISH`.
3. **Missing API Keys**: The Researcher fallback uses structured local mock corpus search retrieval without crashing.
