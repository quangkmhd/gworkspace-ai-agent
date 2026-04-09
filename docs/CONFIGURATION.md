# Configuration Guide: Google Workspace AI Agent

This document explains how to configure the environment, authenticate with Google Workspace, and tune the agent's behavior.

## 1. Environment Variables (`.env`)

The system relies on a `.env` file in the root directory. Copy `.env.example` to `.env` to get started.

### Core LLM Configuration
*   `OPENAI_API_KEY`: (Required if using OpenAI) Your OpenAI API key. e.g., `sk-proj-...`
*   `ANTHROPIC_API_KEY`: (Required if using Claude) Your Anthropic API key.
*   `GOOGLE_API_KEY`: (Required if using Gemini directly via LangChain) Your Google AI Studio key.
*   `LLM_PROVIDER`: Choose between `openai`, `anthropic`, or `google`. Default: `openai`
*   `LLM_MODEL_NAME`: The specific model to use. 
    *   *Recommended:* `gpt-4o`, `claude-3-5-sonnet-20240620`, `gemini-1.5-pro`

### API Server Configuration
*   `PORT`: Port for the FastAPI server. Default: `8000`.
*   `HOST`: Host binding. Default: `0.0.0.0`.
*   `CORS_ORIGINS`: Comma-separated list of allowed origins for the frontend. e.g., `http://localhost:3000,https://my-dashboard.com`
*   `DEBUG_MODE`: `True` or `False`. Enables verbose logging and LangSmith tracing if configured.

### LangSmith Tracing (Highly Recommended)
To debug the complex LangGraph execution, enable LangSmith:
*   `LANGCHAIN_TRACING_V2`: `true`
*   `LANGCHAIN_ENDPOINT`: `https://api.smith.langchain.com`
*   `LANGCHAIN_API_KEY`: Your LangSmith API key.
*   `LANGCHAIN_PROJECT`: `gworkspace-agent-dev`

## 2. Google Workspace Authentication

Authentication requires setting up a Google Cloud Console project and downloading OAuth client credentials.

### Steps to Configure:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. Enable the following APIs:
   - Gmail API
   - Google Calendar API
   - Google Drive API
   - Google Docs API
   - Google Sheets API
4. Configure the **OAuth Consent Screen** (External or Internal depending on your org).
5. Go to **Credentials** -> Create Credentials -> **OAuth client ID** (Application type: Desktop App).
6. Download the JSON file and rename it to `credentials.json`.
7. Place `credentials.json` into the `configs/` directory.

### Token Generation
When you first run the agent, it will prompt you to visit a URL in your browser to authorize the application. Once authorized, it will save a `token.json` file in the `configs/` directory. This file contains the access and refresh tokens. **Never commit `token.json` or `credentials.json` to version control.**

## 3. Human-in-the-Loop (HITL) Configuration

You can customize which tools require human approval in the code configuration.

In `configs/settings.py` or via a JSON config:

```python
# List of tool names that MUST halt the graph and request human approval
REQUIRE_APPROVAL_TOOLS = [
    "gmail_send",
    "gmail_trash",
    "calendar_create_event",
    "calendar_delete_event",
    "drive_delete_file",
    "drive_share_file"
]

# Time-to-live for a pending approval state before it auto-rejects
APPROVAL_TIMEOUT_HOURS = 24
```

## 4. Checkpointer Configuration

By default, the SDK uses an in-memory checkpointer (`MemorySaver`). For production, you must configure a persistent backend (e.g., PostgreSQL or Redis).

Set the `CHECKPOINTER_URL` in your `.env`:
*   `CHECKPOINTER_URL=sqlite:///./configs/state.db` (For local testing)
*   `CHECKPOINTER_URL=postgresql://user:pass@localhost:5432/agent_state` (For production)

The backend will automatically instantiate the appropriate `AsyncPostgresSaver` or `SqliteSaver` based on this connection string.