# Technical Research: Multi-Agent Research System

This document outlines key technical decisions and architectures chosen for the implementation of the Multi-Agent Research System.

## Decisions

### 1. Search Mock Implementation for Offline Execution

*   **Decision:** Build a keyword-based mock search system inside `SearchClient.search`.
*   **Rationale:** We do not have a Tavily or Google Search API key. To ensure the Researcher agent can "search" and obtain realistic sources, the client will parse query keywords (e.g., "GraphRAG", "Agent", "LangGraph") and return pre-defined, high-quality, technically detailed snippets from a static corpus of mock documents.
*   **Alternatives considered:** 
    *   *Web scraping without API keys:* Flaky, high latency, subject to IP blocks.
    *   *Completely random mock data:* Hard to test and degrades analyst/writer outputs.

### 2. Nvidia API Rate Limit (40 RPM) Guardrail

*   **Decision:** Implement a minimum call spacing delay and tenacity-based retries in `LLMClient.complete`.
*   **Rationale:** The Nvidia API key is rate-limited to 40 Requests Per Minute. Multi-agent loops can generate many requests rapidly, which would trigger 429 exceptions. A mandatory sleep of 1.5 seconds between subsequent requests ensures we never exceed 40 RPM. `tenacity` will be used to automatically retry with exponential backoff if a 429 error occurs.
*   **Alternatives considered:** 
    *   *Simple sleep only:* May not handle unexpected spikes or concurrent tasks.
    *   *No rate limit:* Leads to random failures when running multi-agent benchmarks.

### 3. LangGraph Workflow Routing & State Management

*   **Decision:** Build a LangGraph `StateGraph` with a centralized Supervisor node.
*   **Rationale:** The Supervisor agent inspects the shared state (`ResearchState`) and outputs the name of the next worker node to execute, or `"FINISH"`. The router will map:
    *   `"researcher"` -> calls Researcher agent
    *   `"analyst"` -> calls Analyst agent
    *   `"writer"` -> calls Writer agent
    *   `"FINISH"` -> terminates the graph
*   **Alternatives considered:** 
    *   *Linear chain (Researcher -> Analyst -> Writer):* Lacks dynamism. If the Researcher fails or needs more data, the analyst cannot ask for more research.
