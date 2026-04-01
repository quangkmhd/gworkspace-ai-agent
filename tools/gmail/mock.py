"""Gmail mock data for testing without credentials."""

from __future__ import annotations

MOCK_MESSAGES = [
    {
        "id": "msg_001",
        "threadId": "thread_001",
        "from": "alice@example.com",
        "to": "user@example.com",
        "subject": "Weekly Report",
        "snippet": "Here is the weekly report for Q1...",
        "date": "2024-01-15T10:30:00Z",
        "labels": ["INBOX"],
    },
    {
        "id": "msg_002",
        "threadId": "thread_002",
        "from": "bob@example.com",
        "to": "user@example.com",
        "subject": "Meeting Tomorrow",
        "snippet": "Let's discuss the project status...",
        "date": "2024-01-16T14:00:00Z",
        "labels": ["INBOX", "IMPORTANT"],
    },
]

MOCK_THREAD = {
    "thread_id": "thread_001",
    "messages": [
        {"id": "msg_001", "from": "alice@example.com", "body": "Original message"},
        {"id": "msg_003", "from": "user@example.com", "body": "Reply to original"},
    ],
}

MOCK_DRAFT = {"draft_id": "draft_001", "status": "created"}
MOCK_SENT = {"message_id": "sent_001", "status": "sent"}
