# GWorkspace AI Agent - Backend Implementation Plan

## Documents Read & Summary

### Files Read (12/12)
1. `docs/1. PRODUCT OVERVIEW.md` — Product vision, MVP features, core value props
2. `docs/2. SYSTEM ARCHITECTURE.md` — High-level flow, components, data flow
3. `docs/3.AUTH & SECURITY.md` — OAuth 2.0, token management, policy, audit
4. `docs/4. AGENT DESIGN.md` — Agent loop, action model, planning, risk evaluation
5. `docs/5. HITL DESIGN (CORE INNOVATION).md` — Approval gate, risk levels, payload, audit
6. `docs/6.API SPEC.md` — Full API spec (46+ endpoints across 7 groups)
7. `docs/7.REPO STRUCTURE.md` — Proposed monorepo structure
8. `docs/8. TASK BREAKDOWN.md` — 7-phase task breakdown (T1–T32)
9. `docs/9. PROMPT SPEC.md` — System/developer/user prompts, schemas
10. `docs/10. LANGCHAIN GOOGLE WORKSPACE CAPABILITIES.md` — LangChain tool matrix
11. `docs/11. TOOL ACTION CATALOG.md` — 33 tools, risk mapping, JSON schemas
12. `docs/13. MCP TOOL MANIFEST.md` — Full tool manifest with input/output schemas

### Context7 Research Completed
- **LangChain Google** (`langchain-google-community`): Gmail, Calendar, Sheets toolkits confirmed. Docs via Drive. No native Docs toolkit → custom adapter needed.
- **LangGraph** (`langgraph`): `interrupt()` + `Command(resume=...)` pattern for HITL. SqliteSaver/MemorySaver for checkpoints. Supports approve/edit/reject flows.
- **FastAPI**: OAuth2PasswordBearer, Security deps, Pydantic models, automatic OpenAPI docs.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Server                        │
│  /v1/system/*  /v1/agent/*  /v1/tools/*  /v1/hitl/*    │
│  /v1/auth/*    /v1/workspace/*  /v1/audit/*            │
├─────────────────────────────────────────────────────────┤
│  Middleware: request_id, auth, idempotency, logging     │
├─────────────────────────────────────────────────────────┤
│  Agent Core (LangGraph)                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐        │
│  │ Planner  │→│ Executor │→│ Risk Evaluator   │        │
│  └──────────┘ └──────────┘ └──────────────────┘        │
├─────────────────────────────────────────────────────────┤
│  HITL Engine                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐        │
│  │ Queue    │ │ Policy   │ │ State Machine    │        │
│  └──────────┘ └──────────┘ └──────────────────┘        │
├─────────────────────────────────────────────────────────┤
│  Tools Layer                                            │
│  ┌───────┐ ┌──────────┐ ┌──────┐ ┌────────┐ ┌───────┐ │
│  │ Gmail │ │ Calendar │ │ Docs │ │ Sheets │ │ Drive │ │
│  └───────┘ └──────────┘ └──────┘ └────────┘ └───────┘ │
│  (LangChain native)     (custom)  (LangChain) (mixed) │
├─────────────────────────────────────────────────────────┤
│  Auth & Token Management (Google OAuth 2.0)             │
└─────────────────────────────────────────────────────────┘
```

---

## Technology Decisions

| Component | Technology | Justification |
|-----------|-----------|---------------|
| Language | **Python 3.11+** | LangChain ecosystem is Python-first, all official Google Workspace tools available |
| API Server | **FastAPI** | Auto OpenAPI/Swagger, async, Pydantic, Security deps |
| Agent Framework | **LangGraph** | `interrupt()` for HITL, checkpointing, stateful agent workflows |
| Google Tools | **langchain-google-community** | GmailToolkit, CalendarToolkit (Python), SheetsToolkit |
| Docs Tools | **Custom adapter** (googleapis-python) | No LangChain toolkit for Docs |
| Drive Tools | **langchain-googledrive** + custom | Search via LangChain, upload/share/delete custom |
| Checkpointer | **SqliteSaver** (dev) | Local persistence for HITL state |
| Testing | **pytest** + **httpx** (AsyncClient) | Native FastAPI test support |
| Config | **pydantic-settings** | Type-safe env config |

---

## User Review Required

> [!IMPORTANT]
> **Python vs Node.js**: The docs repo structure shows `package.json` in each directory (suggesting Node.js). However, LangChain Google Workspace tools are fully available only in **Python** (Gmail, Calendar, Sheets, Drive toolkits). The JS/TS equivalents are limited (no Sheets/Drive/Docs toolkits). **I strongly recommend Python** to maximize LangChain native tool usage. This changes the repo structure from `package.json` to `pyproject.toml`.

> [!IMPORTANT]
> **Mock mode**: The plan includes a `MOCK_MODE=true` environment variable that replaces real Google API calls with deterministic mock responses. This lets you test all flows without Google credentials.

> [!WARNING]
> **Auth simplification for local dev**: For local-only use, the `Authorization: Bearer <token>` will use a simple API key check (configurable). Google OAuth is for Workspace API access, not for protecting the local API itself.

---

## Proposed Changes

### Phase A: Skeleton + Shared Schemas + Logging + Health

> **Goal**: Project runnable locally with `uvicorn`, health endpoints working.

#### [NEW] `pyproject.toml`
Root project config with all dependencies: `fastapi`, `uvicorn`, `langchain-google-community`, `langgraph`, `pydantic-settings`, `pytest`, `httpx`.

#### [NEW] `backend/__init__.py`
#### [NEW] `backend/main.py`
FastAPI app creation, router registration, middleware setup, lifespan events.

#### [NEW] `backend/config.py`
Pydantic Settings: `MOCK_MODE`, `LOG_LEVEL`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `API_KEY`, `LLM_MODEL`, etc.

#### [NEW] `backend/middleware/`
- `request_id.py` — Generate `X-Request-ID`, attach to state
- `logging_middleware.py` — Structured JSON logging per request
- `idempotency.py` — `Idempotency-Key` header check for write endpoints

#### [NEW] `backend/schemas/`
- `envelope.py` — `ResponseEnvelope(ok, data, error, meta)` 
- `action.py` — `ActionSchema(action_id, tool, args, risk_level, requires_approval, reason)`
- `common.py` — `RiskLevel` enum, `PaginationParams`, ID generators

#### [NEW] `backend/routes/system.py`
- `GET /v1/system/health` — Returns `{ok: true, version, uptime}`
- `GET /v1/system/readiness` — Checks DB, config, tool registry loaded

#### [NEW] `configs/`
- `risk_policy.yaml` — Default risk levels per tool
- `oauth_scopes.yaml` — Scope definitions per tool
- `settings.env.example` — Environment variable template

#### [NEW] `scripts/dev.sh`
One-command dev startup: `uvicorn backend.main:app --reload --port 8000`

---

### Phase B: Auth / OAuth / Token / Policy

> **Goal**: Google OAuth flow, token storage/refresh, authorization policy checks.

#### [NEW] `backend/routes/auth.py`
- `GET /v1/auth/google/start` — Redirect to Google OAuth consent
- `GET /v1/auth/google/callback` — Exchange code for tokens
- `POST /v1/auth/google/refresh` — Refresh access token
- `POST /v1/auth/google/revoke` — Revoke tokens
- `GET /v1/auth/google/scopes` — List granted scopes
- `GET /v1/auth/google/connections` — List active connections

#### [NEW] `backend/services/oauth_service.py`
Google OAuth 2.0 flow implementation using `google-auth-oauthlib`.

#### [NEW] `backend/services/token_store.py`
Encrypted local token storage (SQLite + Fernet encryption).

#### [NEW] `backend/middleware/auth.py`
Bearer token validation middleware. In mock mode, accepts any token.

#### [NEW] `backend/services/policy_service.py`
Authorization policy check: scope verification, risk evaluation, HITL requirement check.

---

### Phase C: Tools + Registry + Invoke

> **Goal**: All 33 tools registered, invokable via generic `POST /v1/tools/{tool_name}/invoke`, workspace-specific endpoints working.

#### [NEW] `tools/__init__.py`
#### [NEW] `tools/registry.py`
Tool registry: loads manifest from `configs/tool_manifest.json`, provides lookup, schema validation (via `jsonschema`).

#### [NEW] `tools/base.py`
Abstract `BaseTool` class with `validate_args()`, `execute()`, `mock_execute()`.

#### [NEW] `tools/gmail/`
- `adapter.py` — Wraps `GmailToolkit` tools (`GmailSearch`, `GmailGetMessage`, `GmailGetThread`, `GmailCreateDraft`, `GmailSendMessage`)
- `mock.py` — Mock responses for each Gmail tool

#### [NEW] `tools/calendar/`
- `adapter.py` — Wraps Calendar tools (`CalendarCreateEvent`, `CalendarSearchEvents`, `CalendarUpdateEvent`, `CalendarMoveEvent`, `CalendarDeleteEvent`, `GetCalendarsInfo`, `GetCurrentDatetime`)
- `mock.py` — Mock responses

#### [NEW] `tools/sheets/`
- `adapter.py` — Wraps `SheetsToolkit` tools (9 tools)
- `mock.py` — Mock responses

#### [NEW] `tools/drive/`
- `adapter.py` — `GoogleDriveSearchTool` + custom adapters for upload/move/copy/share/delete/export/get_content
- `mock.py` — Mock responses

#### [NEW] `tools/docs/`
- `adapter.py` — Custom adapter using Google Docs API directly (create, get, batch_update, insert_text, replace_text, share)
- `mock.py` — Mock responses

#### [NEW] `backend/routes/tools.py`
- `GET /v1/tools` — List all tools with schemas
- `GET /v1/tools/{tool_name}` — Get tool detail
- `POST /v1/tools/{tool_name}/invoke` — Generic invoke with policy/HITL gate

#### [NEW] `backend/routes/workspace/`
- `gmail.py` — 5 Gmail-specific endpoints
- `calendar.py` — 7 Calendar-specific endpoints
- `docs.py` — 6 Docs-specific endpoints
- `sheets.py` — 8 Sheets-specific endpoints
- `drive.py` — 8 Drive-specific endpoints

#### [NEW] `backend/services/tool_invoke_service.py`
Orchestrates: validate args → check policy → check HITL → execute/queue.

---

### Phase D: Agent Core + Risk Evaluator

> **Goal**: LangGraph-based agent that plans, evaluates risk, and routes through HITL.

#### [NEW] `agent/__init__.py`
#### [NEW] `agent/schemas.py`
Pydantic models: `AgentState`, `PlanStep`, `TaskPlan`, `ActionProposal`.

#### [NEW] `agent/planner.py`
LLM-based planner: takes user prompt → produces structured `TaskPlan` with steps mapped to tools.

#### [NEW] `agent/executor.py`
LangGraph `StateGraph`: agent node → tool node (with interrupt) → result aggregation.

#### [NEW] `agent/risk_evaluator.py`
Rule-based evaluator using `configs/risk_policy.yaml`:
- Read-only → Low
- Reversible write → Medium  
- Send/share/delete/critical overwrite → High

#### [NEW] `agent/prompts.py`
System prompt, developer prompt, user prompt template from `docs/9. PROMPT SPEC.md`.

#### [NEW] `backend/routes/agent.py`
- `POST /v1/agent/tasks` — Create task from prompt
- `GET /v1/agent/tasks/{task_id}` — Get task status/plan
- `GET /v1/agent/tasks/{task_id}/actions` — List actions
- `GET /v1/agent/actions/{action_id}` — Action detail

#### [NEW] `backend/services/agent_service.py`
Manages task lifecycle, invokes LangGraph agent, stores results.

---

### Phase E: HITL Workflow + Endpoints + Audit

> **Goal**: Full HITL approval flow with state machine, audit logging.

#### [NEW] `hitl/__init__.py`
#### [NEW] `hitl/queue.py`
In-memory + SQLite approval queue. CRUD for proposals.

#### [NEW] `hitl/state_machine.py`
States: `pending` → `approved` / `edited` / `rejected` / `expired` / `cancelled`.
Transitions with validation.

#### [NEW] `hitl/policy_engine.py`
Evaluates: tool risk_level × policy config → requires_approval boolean.

#### [NEW] `hitl/audit.py`
Structured audit log entries: `task_id`, `action_id`, `approval_id`, `user_decision`, `timestamp`, `before/after` for edits.

#### [NEW] `hitl/workflow.py`
Orchestrates: create proposal → wait for decision → execute or cancel → log.

#### [NEW] `backend/routes/hitl.py`
- `POST /v1/hitl/proposals` — Create proposal (internal)
- `GET /v1/hitl/approvals` — List approvals (filter by user/status)
- `GET /v1/hitl/approvals/{approval_id}` — Detail
- `POST /v1/hitl/approvals/{approval_id}/approve`
- `POST /v1/hitl/approvals/{approval_id}/edit-approve`
- `POST /v1/hitl/approvals/{approval_id}/reject`
- `POST /v1/hitl/approvals/{approval_id}/cancel`

#### [NEW] `backend/routes/audit.py`
- `GET /v1/audit/logs` — Query audit logs by task_id, action_id, date range
- `GET /v1/audit/approvals/{approval_id}` — Full approval audit trail

---

### Phase F: Tests + Docs + Hardening

> **Goal**: Comprehensive test suite, OpenAPI docs, production hardening.

#### [NEW] `tests/unit/`
- `test_risk_evaluator.py` — Risk level assignment for all tool categories
- `test_policy_engine.py` — Policy evaluation logic
- `test_input_validation.py` — Schema validation for all 33 tools
- `test_planner.py` — Plan generation with mocked LLM
- `test_executor.py` — Execution flow with mocked tools
- `test_state_machine.py` — HITL state transitions
- `test_envelope.py` — Response envelope formatting

#### [NEW] `tests/integration/`
- `test_tool_invoke_flow.py` — Tool invoke → policy check → execute/queue
- `test_hitl_flow.py` — Full approval lifecycle (create → approve → execute)
- `test_auth_flow.py` — OAuth start → callback → token refresh

#### [NEW] `tests/e2e/`
- `test_e2e_sheet_to_email.py` — Read sheet → create draft → approve → send
- `test_e2e_calendar_event.py` — Create event → policy check → approve if needed
- `test_e2e_docs_share.py` — Create doc → update → share → approve high-risk

#### [NEW] `tests/conftest.py`
Shared fixtures: mock app, test client, mock tools, mock auth.

#### [MODIFY] `pyproject.toml`
Add test dependencies, scripts.

---

## Repo Structure (Final)

```
gworkspace-ai-agent/
├── pyproject.toml
├── backend/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── request_id.py
│   │   ├── logging_middleware.py
│   │   ├── auth.py
│   │   └── idempotency.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── envelope.py
│   │   ├── action.py
│   │   └── common.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── system.py
│   │   ├── auth.py
│   │   ├── agent.py
│   │   ├── tools.py
│   │   ├── hitl.py
│   │   ├── audit.py
│   │   └── workspace/
│   │       ├── __init__.py
│   │       ├── gmail.py
│   │       ├── calendar.py
│   │       ├── docs.py
│   │       ├── sheets.py
│   │       └── drive.py
│   └── services/
│       ├── __init__.py
│       ├── oauth_service.py
│       ├── token_store.py
│       ├── policy_service.py
│       ├── tool_invoke_service.py
│       └── agent_service.py
├── agent/
│   ├── __init__.py
│   ├── schemas.py
│   ├── planner.py
│   ├── executor.py
│   ├── risk_evaluator.py
│   └── prompts.py
├── tools/
│   ├── __init__.py
│   ├── registry.py
│   ├── base.py
│   ├── gmail/
│   │   ├── __init__.py
│   │   ├── adapter.py
│   │   └── mock.py
│   ├── calendar/
│   │   ├── __init__.py
│   │   ├── adapter.py
│   │   └── mock.py
│   ├── sheets/
│   │   ├── __init__.py
│   │   ├── adapter.py
│   │   └── mock.py
│   ├── drive/
│   │   ├── __init__.py
│   │   ├── adapter.py
│   │   └── mock.py
│   └── docs/
│       ├── __init__.py
│       ├── adapter.py
│       └── mock.py
├── hitl/
│   ├── __init__.py
│   ├── queue.py
│   ├── state_machine.py
│   ├── policy_engine.py
│   ├── audit.py
│   └── workflow.py
├── configs/
│   ├── risk_policy.yaml
│   ├── oauth_scopes.yaml
│   ├── tool_manifest.json
│   └── settings.env.example
├── prompts/
│   ├── system_prompt.txt
│   ├── developer_prompt.txt
│   └── user_prompt_template.txt
├── tests/
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── scripts/
│   └── dev.sh
└── docs/
    └── (existing docs)
```

---

## Open Questions

> [!IMPORTANT]
> 1. **Python confirmation**: Do you agree to use Python instead of Node.js for this backend? This is critical since LangChain Google Workspace tools are fully available only in Python.

> [!IMPORTANT]
> 2. **LLM provider**: Which LLM to use for the agent planner? Options:
>    - Google Gemini (via `langchain-google-genai`) — Aligns with Google ecosystem
>    - OpenAI GPT-4 (via `langchain-openai`) — Industry standard
>    - Anthropic Claude (via `langchain-anthropic`) — Strong reasoning
>    
>    The plan will make this configurable, but need a default.

> [!NOTE]
> 3. **Database**: Using SQLite for local dev (token store, audit logs, HITL queue, LangGraph checkpoints). Is this acceptable or do you want Postgres from the start?

---

## Verification Plan

### Automated Tests
```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests (MOCK_MODE=true)
pytest tests/integration/ -v

# E2E tests (MOCK_MODE=true)  
pytest tests/e2e/ -v

# All tests
pytest --tb=short
```

### Manual Verification
1. Start server: `./scripts/dev.sh`
2. Test health: `curl http://localhost:8000/v1/system/health`
3. Test readiness: `curl http://localhost:8000/v1/system/readiness`
4. Open Swagger: `http://localhost:8000/docs`
5. Test tool listing: `curl http://localhost:8000/v1/tools`
6. Test mock tool invoke: `curl -X POST http://localhost:8000/v1/tools/gmail.search/invoke -d '{"task_id":"test","actor":"test","args":{"query":"test"}}'`

### E2E Scenarios
1. **Sheet → Email**: Read sheet → Create draft → Approval → Send email
2. **Calendar Event**: Create event → Policy check → Approval if needed
3. **Docs Share**: Create doc → Update content → Share → Approval for high-risk
