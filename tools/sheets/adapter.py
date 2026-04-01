"""Sheets tool adapters — uses Google Sheets API via googleapiclient.

9 tools covering CRUD operations on Google Sheets.
"""

from __future__ import annotations

from typing import Any

import structlog

from tools.base import BaseTool

logger = structlog.get_logger("tools.sheets")


def _build_sheets_service(credentials: Any) -> Any:
    """Build Google Sheets API resource from credentials."""
    from googleapiclient.discovery import build

    return build("sheets", "v4", credentials=credentials)


class SheetsCreateSpreadsheetTool(BaseTool):
    name = "sheets.create_spreadsheet"
    description = "Create spreadsheet"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        service = _build_sheets_service(credentials)
        body = {"properties": {"title": args["title"]}}
        result = service.spreadsheets().create(body=body).execute()
        return {"spreadsheet_id": result["spreadsheetId"], "url": result.get("spreadsheetUrl", "")}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"spreadsheet_id": "mock_spreadsheet_001", "url": "https://docs.google.com/spreadsheets/d/mock"}


class SheetsGetSpreadsheetInfoTool(BaseTool):
    name = "sheets.get_spreadsheet_info"
    description = "Get spreadsheet metadata"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        service = _build_sheets_service(credentials)
        result = service.spreadsheets().get(spreadsheetId=args["spreadsheet_id"]).execute()
        sheets = [{"title": s["properties"]["title"], "index": s["properties"]["index"]} for s in result.get("sheets", [])]
        return {"title": result["properties"]["title"], "sheets": sheets}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"title": "Mock Spreadsheet", "sheets": [{"title": "Sheet1", "index": 0}]}


class SheetsReadDataTool(BaseTool):
    name = "sheets.read_data"
    description = "Read sheet range"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        service = _build_sheets_service(credentials)
        result = service.spreadsheets().values().get(
            spreadsheetId=args["spreadsheet_id"], range=args["range"]
        ).execute()
        return {"values": result.get("values", []), "range": result.get("range", args["range"])}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {
            "values": [["Name", "Email", "Score"], ["Alice", "alice@ex.com", "95"], ["Bob", "bob@ex.com", "87"]],
            "range": args.get("range", "Sheet1!A1:C3"),
        }


class SheetsBatchReadDataTool(BaseTool):
    name = "sheets.batch_read_data"
    description = "Read multiple ranges"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        service = _build_sheets_service(credentials)
        result = service.spreadsheets().values().batchGet(
            spreadsheetId=args["spreadsheet_id"], ranges=args["ranges"]
        ).execute()
        value_ranges = result.get("valueRanges", [])
        return {"value_ranges": [{"range": vr.get("range"), "values": vr.get("values", [])} for vr in value_ranges]}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {
            "value_ranges": [
                {"range": r, "values": [["mock_data_1"], ["mock_data_2"]]}
                for r in args.get("ranges", ["Sheet1!A1:A2"])
            ]
        }


class SheetsFilteredReadDataTool(BaseTool):
    name = "sheets.filtered_read_data"
    description = "Read with filter criteria"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        service = _build_sheets_service(credentials)
        result = service.spreadsheets().values().get(
            spreadsheetId=args["spreadsheet_id"], range=args["range"]
        ).execute()
        values = result.get("values", [])
        criteria = args.get("criteria", {})
        if values and criteria:
            header = values[0]
            filtered = [values[0]]
            for row in values[1:]:
                match = True
                for col_name, expected in criteria.items():
                    if col_name in header:
                        idx = header.index(col_name)
                        if idx < len(row) and row[idx] != str(expected):
                            match = False
                            break
                if match:
                    filtered.append(row)
            values = filtered
        return {"values": values, "range": args["range"]}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"values": [["Name", "Status"], ["Alice", "Active"]], "range": args.get("range", "Sheet1!A:B")}


class SheetsUpdateValuesTool(BaseTool):
    name = "sheets.update_values"
    description = "Update a sheet range"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        service = _build_sheets_service(credentials)
        result = service.spreadsheets().values().update(
            spreadsheetId=args["spreadsheet_id"],
            range=args["range"],
            valueInputOption=args.get("value_input_option", "USER_ENTERED"),
            body={"values": args["values"]},
        ).execute()
        return {"updated_cells": result.get("updatedCells", 0), "updated_range": result.get("updatedRange", "")}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        num_cells = sum(len(row) for row in args.get("values", []))
        return {"updated_cells": num_cells, "updated_range": args.get("range", "")}


class SheetsAppendValuesTool(BaseTool):
    name = "sheets.append_values"
    description = "Append rows to sheet"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        service = _build_sheets_service(credentials)
        result = service.spreadsheets().values().append(
            spreadsheetId=args["spreadsheet_id"],
            range=args["range"],
            valueInputOption=args.get("value_input_option", "USER_ENTERED"),
            body={"values": args["values"]},
        ).execute()
        updates = result.get("updates", {})
        return {"updated_cells": updates.get("updatedCells", 0), "updated_range": updates.get("updatedRange", "")}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"updated_cells": len(args.get("values", [])), "updated_range": args.get("range", "")}


class SheetsClearValuesTool(BaseTool):
    name = "sheets.clear_values"
    description = "Clear values in range"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        service = _build_sheets_service(credentials)
        result = service.spreadsheets().values().clear(
            spreadsheetId=args["spreadsheet_id"],
            range=args["range"],
            body={},
        ).execute()
        return {"cleared_range": result.get("clearedRange", args["range"])}

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"cleared_range": args.get("range", "Sheet1!A:Z")}


class SheetsBatchUpdateValuesTool(BaseTool):
    name = "sheets.batch_update_values"
    description = "Batch update ranges"

    def execute(self, args: dict[str, Any], credentials: Any = None) -> dict[str, Any]:
        service = _build_sheets_service(credentials)
        result = service.spreadsheets().values().batchUpdate(
            spreadsheetId=args["spreadsheet_id"],
            body={
                "valueInputOption": args.get("value_input_option", "USER_ENTERED"),
                "data": args["data"],
            },
        ).execute()
        return {
            "total_updated_cells": result.get("totalUpdatedCells", 0),
            "total_updated_rows": result.get("totalUpdatedRows", 0),
        }

    def mock_execute(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"total_updated_cells": 10, "total_updated_rows": 2}
