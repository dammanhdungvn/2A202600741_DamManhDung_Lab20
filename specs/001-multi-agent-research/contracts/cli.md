# CLI Interface Contract: Multi-Agent Research Lab

This document defines the CLI command syntax, options, input schemas, outputs, and exit codes.

## Commands

### 1. Baseline Run
Runs a single LLM request to handle the user query.

`python -m multi_agent_research_lab.cli baseline --query "<QUERY>"`

**Arguments:**
*   `--query` / `-q` (Required, string): The research query. Minimum 5 characters.

**Standard Output:**
Prints a formatted text panel containing the final synthesized response.

**Exit Codes:**
*   `0`: Success.
*   `1`: General failure (e.g. invalid arguments, API connection failure).

---

### 2. Multi-Agent Run
Runs the complete multi-agent LangGraph workflow.

`python -m multi_agent_research_lab.cli multi-agent --query "<QUERY>"`

**Arguments:**
*   `--query` / `-q` (Required, string): The research query. Minimum 5 characters.

**Standard Output:**
Prints the JSON-serialized representation of the final `ResearchState`. Example:
```json
{
  "request": {
    "query": "Research GraphRAG state-of-the-art",
    "max_sources": 5,
    "audience": "technical learners"
  },
  "iteration": 4,
  "route_history": ["supervisor", "researcher", "analyst", "writer"],
  "sources": [...],
  "research_notes": "...",
  "analysis_notes": "...",
  "final_answer": "...",
  "agent_results": [...],
  "trace": [...],
  "errors": []
}
```

**Exit Codes:**
*   `0`: Success.
*   `2`: Student Todo error (if TODO code remains unimplemented).
*   `1`: General run failure or rate limit failure.
