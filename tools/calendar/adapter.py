"""Calendar tool adapters — wraps LangChain Google Calendar tools.

Uses langchain_google_community calendar tools for:
  - CreateEvent, SearchEvents, UpdateEvent, MoveEvent, DeleteEvent,
    GetCalendarsInfo, GetCurrentDatetime
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import structlog

from tools.base import BaseTool

logger = structlog.get_logger("tools.calendar")


def _build_calendar_service(credentials: Any) -> Any:
    """Build Google Calendar API resource from credentials."""
    from googleapiclient.discovery import build

    return build("calendar", "v3", credentials=credentials)


class CalendarGetCalendarsInfoTool(BaseTool):
    name = "calendar.get_calendars_info"
    description = "List calendar metadata"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        service = _build_calendar_service(credentials)
        result = service.calendarList().list().execute()
        calendars = [
            {
                "id": cal["id"],
                "summary": cal.get("summary", ""),
                "primary": cal.get("primary", False),
                "timeZone": cal.get("timeZone", ""),
            }
            for cal in result.get("items", [])
        ]
        return {"calendars": calendars}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {
            "calendars": [
                {"id": "primary", "summary": "My Calendar", "primary": True, "timeZone": "Asia/Ho_Chi_Minh"},
                {"id": "work@group.calendar.google.com", "summary": "Work", "primary": False, "timeZone": "Asia/Ho_Chi_Minh"},
            ]
        }


class CalendarSearchEventsTool(BaseTool):
    name = "calendar.search_events"
    description = "Search calendar events"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        service = _build_calendar_service(credentials)
        calendar_id = args.get("calendar_id", "primary")
        events_result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=args.get("time_min"),
                timeMax=args.get("time_max"),
                q=args.get("query", ""),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])
        return {"events": events}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {
            "events": [
                {
                    "id": "mock_event_001",
                    "summary": "Mock Meeting",
                    "start": {"dateTime": args.get("time_min", "2024-01-15T09:00:00+07:00")},
                    "end": {"dateTime": args.get("time_max", "2024-01-15T10:00:00+07:00")},
                    "attendees": [{"email": "colleague@example.com"}],
                }
            ]
        }


class CalendarCreateEventTool(BaseTool):
    name = "calendar.create_event"
    description = "Create calendar event"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        service = _build_calendar_service(credentials)
        calendar_id = args.get("calendar_id", "primary")
        event_body: dict[str, Any] = {
            "summary": args["summary"],
            "start": {"dateTime": args["start"]},
            "end": {"dateTime": args["end"]},
        }
        if args.get("description"):
            event_body["description"] = args["description"]
        if args.get("attendees"):
            event_body["attendees"] = [{"email": e} for e in args["attendees"]]
        if args.get("timezone"):
            event_body["start"]["timeZone"] = args["timezone"]
            event_body["end"]["timeZone"] = args["timezone"]

        event = service.events().insert(calendarId=calendar_id, body=event_body).execute()
        return {"event_id": event.get("id", "")}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"event_id": "mock_event_created_001", "summary": args.get("summary", "")}


class CalendarUpdateEventTool(BaseTool):
    name = "calendar.update_event"
    description = "Update calendar event"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        service = _build_calendar_service(credentials)
        calendar_id = args.get("calendar_id", "primary")
        event_id = args["event_id"]
        patch = args.get("patch", {})
        updated = service.events().patch(
            calendarId=calendar_id, eventId=event_id, body=patch
        ).execute()
        return {"event_id": updated.get("id", event_id), "updated": True}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"event_id": args.get("event_id", "mock"), "updated": True}


class CalendarMoveEventTool(BaseTool):
    name = "calendar.move_event"
    description = "Move event between calendars"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        service = _build_calendar_service(credentials)
        event_id = args["event_id"]
        source = args["source_calendar_id"]
        destination = args["target_calendar_id"]
        moved = service.events().move(
            calendarId=source, eventId=event_id, destination=destination
        ).execute()
        return {"event_id": moved.get("id", event_id), "moved": True}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"event_id": args.get("event_id", "mock"), "moved": True}


class CalendarDeleteEventTool(BaseTool):
    name = "calendar.delete_event"
    description = "Delete calendar event"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        service = _build_calendar_service(credentials)
        calendar_id = args.get("calendar_id", "primary")
        event_id = args["event_id"]
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        return {"deleted": True, "event_id": event_id}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"deleted": True, "event_id": args.get("event_id", "mock")}


class CalendarGetCurrentDatetimeTool(BaseTool):
    name = "calendar.get_current_datetime"
    description = "Get current datetime with timezone"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        tz_name = args.get("timezone", "UTC")
        try:
            import zoneinfo
            tz = zoneinfo.ZoneInfo(tz_name)
        except Exception:
            tz = timezone.utc
        now = datetime.now(tz)
        return {"datetime": now.isoformat(), "timezone": tz_name}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {
            "datetime": "2024-01-15T10:30:00+07:00",
            "timezone": args.get("timezone", "Asia/Ho_Chi_Minh"),
        }
