# Architecture Deep Dive: Google Workspace AI Agent with HITL

## 1. System Overview

The **Google Workspace AI Agent** is an advanced autonomous system designed to interact with Google Workspace APIs (Gmail, Calendar, Drive, Docs, Sheets) on behalf of the user. To ensure safety and compliance, it implements a robust **Human-in-the-Loop (HITL)** mechanism. The core intelligence is powered by **LangGraph**, which models the agent's decision-making process as a stateful graph, allowing it to pause execution, request human approval, and resume from the exact state.

The system is exposed as a **REST API** using **FastAPI**, enabling seamless integration into custom dashboards, Slack bots, or internal developer portals.

## 2. Core Components

### 2.1. The Agent Core (`agent/`)
This module houses the LangGraph implementation. It defines the state schema, the nodes (representing actions or LLM calls), and the edges (conditional logic dictating the flow).
- **State Schema:** A `TypedDict` or Pydantic model that holds the conversation history, pending actions, approval status, and workspace context.
- **LLM Node:** The brain of the agent, typically utilizing a powerful reasoning model (e.g., GPT-4 or Gemini 1.5 Pro) to decide the next tool call.
- **Tool Execution Node:** Responsible for invoking specific Google Workspace tools.

### 2.2. Tooling Ecosystem (`tools/`)
A collection of specific tool wrappers that interface with the Google Workspace APIs.
- `gmail_tools.py`: Tools for searching, reading, drafting, and sending emails.
- `calendar_tools.py`: Tools for creating events, finding free slots, and reading agendas.
- `drive_tools.py`: File management, searching, and permissions.
- `docs_tools.py` & `sheets_tools.py`: For content extraction and generation.

### 2.3. Human-in-the-Loop (HITL) Subsystem (`hitl/`)
The safety net. When the LLM decides to execute a mutating action (e.g., `send_email`, `delete_file`), the graph transitions to the HITL node.
- **Interrupt Mechanism:** LangGraph pauses execution using checkpoints.
- **Approval Registry:** Stores pending actions with an associated `workflow_id`.
- **Resumption:** Once the user approves or rejects via the API, the graph state is updated, and execution resumes.

### 2.4. API Server (`backend/`)
Built with **FastAPI**, providing the interface for external clients to start workflows and approve actions.
- `/api/v1/workflows`: Start new agent runs.
- `/api/v1/approve`: Endpoints to handle user approvals.
- `/api/v1/status`: Polling endpoints to check workflow state.

## 3. Data Flow Architecture

1. **Request Initiation:** The user sends a natural language prompt via the FastAPI `/workflows` endpoint.
2. **Graph Execution (Initial):**
   - The LangGraph state is initialized.
   - The LLM analyzes the prompt and determines it needs to read emails.
   - The LLM outputs a `tool_call` for `search_emails`.
3. **Read Operation:**
   - The tool executes (read-only, no HITL required).
   - Results are added to the state.
4. **Draft & Propose:**
   - The LLM drafts a reply and outputs a `tool_call` for `send_email`.
   - The `send_email` tool is flagged as "requires approval".
5. **HITL Interruption:**
   - The graph transitions to a "Pending Approval" state.
   - Execution halts. The state is serialized to a persistent checkpointer (e.g., SQLite or Redis).
   - FastAPI returns the pending status and an approval link to the user.
6. **Approval & Resumption:**
   - The user reviews the draft and calls the `/approve` endpoint.
   - The checkpointer loads the state.
   - The tool executes the actual Google API call to send the email.
   - The graph finishes execution and returns the final status.

## 4. State Persistence

To support asynchronous human approvals that might take hours or days, the system relies on LangGraph's checkpointer mechanism. 
- **Checkpointer:** Stores the full graph state (messages, variables) at every step.
- **Thread ID:** Each workflow is assigned a unique `thread_id` to correlate the API request with the persisted state.

## 5. Security & Authentication

- **OAuth 2.0:** Uses standard Google OAuth flows. Credentials (`credentials.json` and `token.json`) are securely managed.
- **Principle of Least Privilege:** Tools should be configured to request only the specific scopes required for their operation.
- **HITL Verification:** The core security principle is that the LLM cannot autonomously execute destructive or external-facing actions without explicit boolean confirmation from an authenticated user via the API.
