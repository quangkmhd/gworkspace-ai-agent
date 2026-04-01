"""Unit tests for response envelope formatting."""

from __future__ import annotations

from backend.schemas.envelope import ResponseEnvelope


class TestResponseEnvelope:
    def test_success(self):
        resp = ResponseEnvelope.success(data={"key": "value"})
        assert resp.ok is True
        assert resp.data == {"key": "value"}
        assert resp.error is None
        assert resp.meta.request_id.startswith("req_")

    def test_fail(self):
        resp = ResponseEnvelope.fail("ERR_CODE", "Something went wrong")
        assert resp.ok is False
        assert resp.error["code"] == "ERR_CODE"
        assert resp.error["message"] == "Something went wrong"
        assert resp.data is None

    def test_fail_with_details(self):
        resp = ResponseEnvelope.fail("ERR", "msg", details={"field": "invalid"})
        assert resp.error["details"] == {"field": "invalid"}

    def test_custom_request_id(self):
        resp = ResponseEnvelope.success(data=None, request_id="req_custom_123")
        assert resp.meta.request_id == "req_custom_123"
