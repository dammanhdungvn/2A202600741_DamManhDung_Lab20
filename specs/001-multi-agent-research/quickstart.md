# Quickstart Validation Guide: Multi-Agent Research System

This guide outlines the steps to validate that the Multi-Agent Research System works correctly end-to-end.

## Prerequisites
*   Python >= 3.11 installed.
*   `uv` tool installed for environment management.
*   A valid Nvidia API key stored as `OPENAI_API_KEY` in `.env`.

## Setup
Install dependencies and build the virtual environment using `uv`:
```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev,llm]"
cp .env.example .env # Ensure your OPENAI_API_KEY and Nvidia endpoints are configured in .env
```

## Validation Scenarios

### Scenario 1: Run Single-Agent Baseline ✅ VALIDATED
Verify that the baseline system makes a single LLM call and returns a summary.
```bash
uv run python -m multi_agent_research_lab.cli baseline --query "Research GraphRAG state-of-the-art"
```
**Expected Outcome:**
*   Terminal outputs a styled panel labeled `Single-Agent Baseline`.
*   Contains a concise research summary of GraphRAG.

**Actual Result (2026-06-24):**
*   Panel rendered with GraphRAG summary
*   Latency: 8.07s | Tokens: In:~1000 Out:~700 | Cost: $0.001415
*   ✅ All outcomes met

---

### Scenario 2: Run Multi-Agent Workflow ✅ VALIDATED
Verify that the multi-agent graph runs sequentially through the nodes.
```bash
uv run python -m multi_agent_research_lab.cli multi-agent --query "Research GraphRAG state-of-the-art"
```
**Expected Outcome:**
*   Terminal prints a JSON block representing `ResearchState`.
*   `route_history` shows a path like `["researcher", "analyst", "writer", "critic", "FINISH"]`.
*   `sources` is populated with mock sources.
*   `research_notes`, `analysis_notes`, and `final_answer` are populated with non-empty strings.
*   `errors` is empty.

**Actual Result (2026-06-24):**
*   Route path: `supervisor → researcher → supervisor → analyst → supervisor → writer → supervisor → critic → supervisor → FINISH`
*   All 5 agent fields populated: sources (5 docs), research_notes ✅, analysis_notes ✅, final_answer ✅, critic result ✅
*   errors: [] (0 errors)
*   Trace JSON saved to `reports/traces/`
*   ✅ All outcomes met

---

### Scenario 3: Run Benchmark Suite ✅ VALIDATED
```bash
uv run python -m multi_agent_research_lab.cli benchmark --query "Research GraphRAG state-of-the-art and write a 500-word summary"
```
**Expected Outcome:**
*   Both baseline and multi-agent runs complete
*   Comparative metrics table rendered
*   `reports/benchmark_report.md` file created

**Actual Result (2026-06-24):**
| Run | Latency (s) | Cost (USD) | Quality Score (0-10) | Citations |
|---|---|---|---|---|
| Single-Agent Baseline | 41.69 | $0.001415 | 3.5 | 0 |
| Multi-Agent Workflow | 88.69 | $0.005573 | **7.5** | 2 |
*   ✅ Report saved to `reports/benchmark_report.md`
*   ✅ Quality improvement: +4.0 points (3.5 → 7.5)

---

### Scenario 4: Verify Unit Tests ✅ VALIDATED
Run the test suite to ensure code health.
```bash
uv run pytest -v
```
**Expected Outcome:**
*   All tests pass with 100% success.

**Actual Result (2026-06-24):**
*   **7/7 tests passed** in 2.32s
*   test_supervisor_runs_and_routes ✅
*   test_search_client_mock_returns_results ✅
*   test_search_client_mock_default_fallback ✅
*   test_supervisor_enforces_max_iterations ✅
*   test_config ✅, test_report_renders_markdown ✅, test_state ✅
*   ✅ 100% pass rate

---

### Scenario 5: Verify Code Quality ✅ VALIDATED
```bash
uv run ruff check src/
```
**Actual Result:** `All checks passed!`
