# Tasks: Multi-Agent Research System

**Input**: Design documents from `specs/001-multi-agent-research/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Unit/integration tests are generated to verify each component.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Paths shown below assume single project structure at `src/` and `tests/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Verify project environment is ready with Python and dependencies configured in pyproject.toml
- [x] T002 Configure environment variables in .env for Nvidia API base URL, model name, and API key

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T003 [P] Implement LLMClient.complete in src/multi_agent_research_lab/services/llm_client.py using Nvidia API client with retry and latency/cost tracking
- [x] T004 Implement Nvidia rate limit logic in src/multi_agent_research_lab/services/llm_client.py to sleep/throttle requests ensuring <= 40 RPM
- [x] T005 [P] Implement mock database snippets in src/multi_agent_research_lab/services/search_client.py to return realistic source documents without API keys
- [x] T006 [P] Add state modification helper functions in src/multi_agent_research_lab/core/state.py for logging traces and routes

**Checkpoint**: ✅ Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Single-Agent Baseline (Priority: P1) 🎯 MVP

**Goal**: Establish a quick baseline command using a single LLM call

**Independent Test**: Run `python -m multi_agent_research_lab.cli baseline` and inspect output

### Implementation for User Story 1

- [x] T007 [US1] Create the baseline logic in src/multi_agent_research_lab/cli.py to call LLMClient directly for query summaries and track execution latency
- [x] T008 [US1] Add unit test for the baseline method in tests/test_agents_todo.py or new file

**Checkpoint**: ✅ User Story 1 is fully functional and testable independently

---

## Phase 4: User Story 2 - Multi-Agent Workflow (Priority: P2)

**Goal**: Implement Supervisor, Worker nodes, and LangGraph workflow

**Independent Test**: Run `python -m multi_agent_research_lab.cli multi-agent` and check JSON outputs

### Implementation for User Story 2

- [x] T009 [US2] Implement SupervisorAgent.run in src/multi_agent_research_lab/agents/supervisor.py to choose next worker or finish using structured prompts
- [x] T010 [P] [US2] Implement ResearcherAgent.run in src/multi_agent_research_lab/agents/researcher.py to call mock search and consolidate notes
- [x] T011 [P] [US2] Implement AnalystAgent.run in src/multi_agent_research_lab/agents/analyst.py to extract claims and compare viewpoints
- [x] T012 [P] [US2] Implement WriterAgent.run in src/multi_agent_research_lab/agents/writer.py to synthesize final answer with citations
- [x] T013 [P] [US2] Implement CriticAgent in src/multi_agent_research_lab/agents/critic.py to fact-check final report against source snippets
- [x] T014 [US2] Construct the LangGraph workflow structure in src/multi_agent_research_lab/graph/workflow.py compiling nodes and conditional routing edges
- [x] T015 [US2] Add unit and integration tests for multi-agent graph in tests/test_agents_todo.py

**Checkpoint**: ✅ User Stories 1 AND 2 both work independently

---

## Phase 5: User Story 3 - Trace and Benchmarking (Priority: P3)

**Goal**: Collect metrics and generate the benchmark report

**Independent Test**: Run the evaluation command or script to trigger multiple runs and output reports

### Implementation for User Story 3

- [x] T016 [US3] Create metric evaluator in src/multi_agent_research_lab/evaluation/benchmark.py to compute latency, token cost, quality score (LLM-as-judge)
- [x] T017 [US3] Implement report writer in src/multi_agent_research_lab/evaluation/report.py to generate markdown comparison tables
- [x] T018 [US3] Implement benchmark CLI subcommand in src/multi_agent_research_lab/cli.py to execute both modes and print comparative metrics
- [x] T019 [US3] Implement local JSON tracing in src/multi_agent_research_lab/observability/tracing.py with save_trace_to_json() to reports/traces/

**Checkpoint**: ✅ All user stories are independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T020 Run the full test suite (pytest) and linting (ruff check) to verify zero errors — **Result: 7/7 passed, All ruff checks passed!**
- [x] T021 Execute validation scenarios in quickstart.md and complete exit ticket — **See exit ticket answers below**

---

## Exit Ticket Answers

### 1. Case nào nên dùng multi-agent? Vì sao?

Nên dùng multi-agent khi:
- **Task phức tạp và phân tách được**: Research → Analysis → Synthesis → Review là 4 giai đoạn tự nhiên với input/output riêng biệt. Mỗi agent tập trung vào vai trò chuyên biệt → chất lượng từng bước cao hơn.
- **Chất lượng và độ chính xác ưu tiên hơn latency**: Trong benchmark thực tế, multi-agent đạt quality score 7.5/10 so với 3.5/10 của single-agent, với citation coverage từ 0 lên 2.
- **Cần khả năng fact-check và validation**: CriticAgent hoạt động như một gatekeeper độc lập, xác minh thông tin trước khi output — rất quan trọng trong domain nhạy cảm (medical, legal, financial).
- **Hệ thống cần observability và audit trail**: `route_history` và `trace` cho phép debug từng bước, xác định bottleneck.
- **Iterative refinement cần thiết**: Supervisor có thể gửi lại Researcher khi analysis không đủ, hoặc Writer khi report thiếu citations.

### 2. Case nào không nên dùng multi-agent? Vì sao?

Không nên dùng multi-agent khi:
- **Task đơn giản và self-contained**: Một câu hỏi factual ("thủ đô của Việt Nam là gì?") không cần 5 agent và 10 LLM calls.
- **Latency là yếu tố quyết định**: Multi-agent mất 88s so với 42s của single-agent (2× latency) do sequential routing và rate-limit delay. Real-time chat UI sẽ không chấp nhận điều này.
- **Budget hạn chế**: Cost tăng ~4× (từ $0.0014 lên $0.0056) vì mỗi agent gọi LLM riêng. Ở scale lớn, chi phí này tích lũy nhanh.
- **Task không phân tách được thành independent stages**: Nếu từng bước phụ thuộc chặt vào nhau mà không có clear handoff, overhead của state serialization + routing không mang lại lợi ích.
- **Độ tin cậy của LLM routing thấp**: Supervisor dùng LLM để route — nếu LLM parse sai, cần fallback deterministic. Thêm complexity mà không có benefit nếu use-case đơn giản.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Models within a story marked [P] can run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently (MVP!)
3. Add User Story 2 → Test independently
4. Add User Story 3 → Test independently
5. Each story adds value without breaking previous stories
