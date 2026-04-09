# API Reference: Google Workspace AI Agent

This document outlines the core Python classes, methods, and the REST API endpoints provided by the `gworkspace-ai-agent` system.

## 1. REST API (FastAPI)

The backend provides a RESTful interface for integrating the agent into other applications.

### 1.1. `POST /api/v1/workflows/{workflow_name}`
Starts a new agent workflow based on a predefined template or a generic query.

**Parameters:**
- `workflow_name` (path parameter): The type of workflow (e.g., `email-triage`, `generic`).
- Body (JSON):
  ```json
  {
    "user_query": "Draft a response to the client asking for a delay.",
    "context": {}
  }
  ```

**Response (200 OK):**
```json
{
  "workflow_id": "uuid-1234-5678",
  "status": "running",
  "message": "Workflow started successfully."
}
```

### 1.2. `GET /api/v1/workflows/{workflow_id}/status`
Polls the current status of the workflow.

**Response (200 OK - Pending):**
```json
{
  "workflow_id": "uuid-1234-5678",
  "status": "pending_approval",
  "pending_action": {
    "tool_name": "gmail_send",
    "arguments": {
      "to": "client@example.com",
      "subject": "Re: Project Timeline",
      "body": "Hello, we need a slight delay..."
    }
  }
}
```

### 1.3. `POST /api/v1/approve/{workflow_id}`
Submits a human approval decision for a pending workflow.

**Parameters:**
- Body (JSON):
  ```json
  {
    "approved": true,
    "feedback": "Looks good, send it."
  }
  ```

**Response (200 OK):**
```json
{
  "workflow_id": "uuid-1234-5678",
  "status": "resumed",
  "message": "Action approved. Workflow resuming."
}
```

## 2. Core Python SDK (`agent.core`)

For developers building directly on the Python SDK rather than the REST API.

### `class WorkspaceAgent`
The primary controller for the LangGraph-based agent.

#### `__init__(self, checkpointer=None, tools=None)`
Initializes the agent graph.
- `checkpointer`: A LangGraph checkpointer instance (defaults to MemorySaver for testing).
- `tools`: A list of instantiated tool objects to provide to the LLM.

#### `run(self, query: str, thread_id: str = None) -> dict`
Executes the agent synchronously until it finishes or hits a HITL interruption.
- `query`: The natural language instruction.
- `thread_id`: Optional identifier to resume a previous session. If None, a new UUID is generated.
- **Returns**: A dictionary containing the final state or the pending action details.

#### `approve_action(self, thread_id: str, approved: bool, feedback: str = "") -> dict`
Injects the human decision into the graph state and resumes execution.
- `thread_id`: The ID of the pending workflow.
- `approved`: `True` to execute the action, `False` to abort or ask the LLM to rewrite.
- `feedback`: Optional text feedback provided back to the LLM (useful if `approved=False`).

## 3. Tool Reference (`tools/`)

### `GmailTools`
- `search_emails(query: str, max_results: int = 10) -> List[dict]`: Wraps `gmail.users.messages.list`.
- `read_email(message_id: str) -> dict`: Wraps `gmail.users.messages.get`.
- `send_email(to: str, subject: str, body: str) -> str`: Requires HITL. Wraps `gmail.users.messages.send`.

### `CalendarTools`
- `list_events(time_min: str, time_max: str) -> List[dict]`: Retrieves schedule.
- `create_event(summary: str, start_time: str, end_time: str, attendees: List[str]) -> str`: Requires HITL.

### `DriveTools`
- `search_files(query: str) -> List[dict]`: Uses Google Drive query syntax.
- `delete_file(file_id: str) -> bool`: Requires HITL. Trashes a file.

## 4. State Schema

The internal LangGraph state is represented by `AgentState`:

```python
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    pending_approval: bool
    current_tool_call: dict
    workspace_context: dict
```