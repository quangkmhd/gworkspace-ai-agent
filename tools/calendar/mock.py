"""Calendar mock data for testing without credentials."""

MOCK_CALENDARS = [
    {"id": "primary", "summary": "My Calendar", "primary": True},
    {"id": "work@group.calendar.google.com", "summary": "Work", "primary": False},
]

MOCK_EVENT = {
    "id": "event_001",
    "summary": "Team Standup",
    "start": {"dateTime": "2024-01-15T09:00:00+07:00"},
    "end": {"dateTime": "2024-01-15T09:15:00+07:00"},
}
