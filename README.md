# Lab 20: Multi-Agent Research System

Hệ thống nghiên cứu đa tác nhân (**Multi-Agent Research System**) gồm **Supervisor + Researcher + Analyst + Writer + Critic** được điều phối bằng **LangGraph**, so sánh với single-agent baseline qua benchmark tự động.

## Learning Outcomes

Sau khi hoàn thành lab, học viên có thể:

1. Thiết kế **role rõ ràng** cho từng agent với input/output riêng biệt.
2. Xây dựng **shared state** (`ResearchState`) đủ thông tin cho handoff giữa các agent.
3. Thêm **guardrail**: max iterations, timeout, retry/fallback, validation.
4. **Trace** luồng chạy từng bước và giải thích agent nào làm gì.
5. **Benchmark** single-agent vs multi-agent theo quality, latency, cost.

---

## Architecture

```text
User Query
   |
   v
Supervisor (LLM-based routing + deterministic fallback)
   |──────> Researcher Agent  → state.sources + state.research_notes
   |──────> Analyst Agent     → state.analysis_notes
   |──────> Writer Agent      → state.final_answer
   |──────> Critic Agent      → fact-check + agent_results
   |
   v
LangGraph END → Trace JSON + Benchmark Report (reports/benchmark_report.md)
```

### Routing Policy

```
START → Supervisor
  ├── research_notes is None? → Researcher → (back to Supervisor)
  ├── analysis_notes is None? → Analyst   → (back to Supervisor)
  ├── final_answer is None?   → Writer    → (back to Supervisor)
  ├── no Critic run yet?      → Critic    → (back to Supervisor)
  └── all done?               → FINISH
```

---

## Kết quả Benchmark (Live Run)

| Metric | Single-Agent | Multi-Agent |
|---|---:|---:|
| Latency | 41.69s | 88.69s |
| Cost | $0.001415 | $0.005573 |
| **Quality Score (0-10)** | 3.5 | **7.5** |
| Citations | 0 | 2 |
| Errors | 0 | 0 |
| Route Steps | 0 | 5 |

> **+4.0 điểm chất lượng** nhờ role specialization: mỗi agent tập trung vào một giai đoạn, CriticAgent fact-check kết quả trước khi output.

---

## Cấu trúc Repo

```text
.
├── src/multi_agent_research_lab/
│   ├── agents/
│   │   ├── supervisor.py     # LLM-based routing + deterministic fallback
│   │   ├── researcher.py     # Mock search + research notes synthesis
│   │   ├── analyst.py        # Claim extraction + gap analysis
│   │   ├── writer.py         # Final report with inline citations
│   │   └── critic.py         # Fact-check against source snippets
│   ├── core/
│   │   ├── config.py         # Settings (Pydantic + .env)
│   │   ├── schemas.py        # All Pydantic data models
│   │   ├── state.py          # ResearchState + helper methods
│   │   └── errors.py         # Custom error types
│   ├── graph/
│   │   └── workflow.py       # LangGraph StateGraph compilation
│   ├── services/
│   │   ├── llm_client.py     # Nvidia API client, 40 RPM rate limit, tenacity retry
│   │   └── search_client.py  # Mock search corpus (offline, no API key needed)
│   ├── evaluation/
│   │   ├── benchmark.py      # run_benchmark(), LLM-as-judge quality scorer
│   │   └── report.py         # render_markdown_report()
│   ├── observability/
│   │   ├── logging.py        # Structured logging setup
│   │   └── tracing.py        # Local JSON trace persistence to reports/traces/
│   └── cli.py                # CLI: baseline | multi-agent | benchmark
├── specs/001-multi-agent-research/
│   ├── spec.md               # Feature specification
│   ├── plan.md               # Implementation plan
│   ├── tasks.md              # Task checklist (21/21 ✅)
│   └── quickstart.md         # Validation scenarios + actual results
├── reports/
│   └── benchmark_report.md   # Auto-generated comparison report
├── docs/
│   ├── lab_guide.md          # Lab milestones + exit ticket
│   ├── design_template.md    # Architecture decisions + routing policy
│   └── openai-call-api.md    # API call reference
├── tests/                    # 7 unit tests (7/7 passing)
├── .env.example              # Environment variables template
├── pyproject.toml            # Python project config (uv)
├── Dockerfile                # Containerized dev/runtime
└── Makefile                  # Common commands
```

---

## Quickstart

### 1. Cài đặt môi trường (dùng `uv`)

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev,llm]"   # Chú ý dấu chấm (.) trước [dev,llm]
cp .env.example .env
```

> Nếu dùng `pip` thông thường (không có `uv`):
> ```bash
> pip install -e ".[dev,llm]"
> ```
> ⚠️ Lỗi phổ biến: `pip install -e "[dev]"` (thiếu dấu `.`) → báo lỗi *not a valid editable requirement*.

### 2. Cấu hình API keys trong `.env`

```bash
OPENAI_API_KEY=nvapi-...          # Nvidia API key
OPENAI_BASE_URL=https://integrate.api.nvidia.com/v1
OPENAI_MODEL_NAME=meta/llama-3.1-8b-instruct
MAX_ITERATIONS=6
LOG_LEVEL=INFO
```

> **SearchClient** dùng mock data tĩnh — không cần Tavily/Google API key.

### 3. Chạy smoke test

```bash
uv run pytest -v
# Expected: 7/7 passed
```

### 4. Chạy Single-Agent Baseline

```bash
uv run python -m multi_agent_research_lab.cli baseline \
  --query "Research GraphRAG state-of-the-art and write a 500-word summary"
```

Output: Panel styled với summary + latency/token/cost stats.

### 5. Chạy Multi-Agent Workflow

```bash
uv run python -m multi_agent_research_lab.cli multi-agent \
  --query "Research GraphRAG state-of-the-art and write a 500-word summary"
```

Output: Full `ResearchState` JSON + route path + trace file path.

### 6. Chạy Benchmark (so sánh cả hai)

```bash
uv run python -m multi_agent_research_lab.cli benchmark \
  --query "Research GraphRAG state-of-the-art and write a 500-word summary"
```

Output: Comparative markdown table + saves `reports/benchmark_report.md`.

---

## Guardrails được triển khai

| Guardrail | Cơ chế |
|---|---|
| Rate limit (40 RPM) | Thread-safe spacing delay (1.6s/call) trong `LLMClient` |
| Max iterations | `SupervisorAgent` buộc `FINISH` khi `iteration >= MAX_ITERATIONS` (default: 6) |
| Retry on failure | `tenacity`: 3 lần thử, exponential backoff 2–10s |
| LLM parse failure | JSON parse error → deterministic fallback routing |
| Missing state fields | Mỗi agent validate input trước khi call LLM; log error nếu thiếu |
| Infinite loop | `route_history` audit trail + iteration counter |

---

## Deliverables

| # | Deliverable | Status |
|---|---|---|
| 1 | GitHub repo cá nhân | ✅ |
| 2 | `reports/benchmark_report.md` | ✅ Generated |
| 3 | Trace logs | ✅ `reports/traces/*.json` |
| 4 | Exit ticket (2 câu hỏi) | ✅ Trong `specs/001-multi-agent-research/tasks.md` |
| 5 | 7/7 unit tests passing | ✅ |

---

## Exit Ticket

**1. Case nào nên dùng multi-agent? Vì sao?**

Khi task có nhiều giai đoạn độc lập (research → analyze → write → review), khi chất lượng/fact-accuracy quan trọng hơn latency, khi cần observability và audit trail rõ ràng, hoặc khi một LLM call đơn lẻ không đủ context window để xử lý toàn bộ.

**2. Case nào không nên dùng multi-agent? Vì sao?**

Khi task đơn giản và self-contained (không cần phân tách giai đoạn), khi latency là yếu tố quyết định (real-time chat UI), hoặc khi budget hạn chế — multi-agent tốn ~4× chi phí LLM và 2× latency so với single-agent.

---

## References

- [Building effective agents — Anthropic](https://www.anthropic.com/engineering/building-effective-agents)
- [LangGraph concepts — LangChain](https://langchain-ai.github.io/langgraph/concepts/)
- [OpenAI Agents SDK orchestration](https://developers.openai.com/api/docs/guides/agents/orchestration)
- [GraphRAG — Microsoft](https://github.com/microsoft/graphrag)
- [LangSmith tracing](https://docs.smith.langchain.com/)
