"""Tests for StreamParser — NDJSON line parsing."""
import json
import pytest

from backend.services.stream_parser import StreamParser


@pytest.fixture
def parser():
    return StreamParser()


def test_empty_line(parser):
    assert parser.parse_line("") is None
    assert parser.parse_line("   ") is None


def test_invalid_json(parser):
    result = parser.parse_line("not json at all")
    assert result is not None
    assert result["event_type"] == "parse_error"
    assert result["is_error"] is True
    assert result["content"] == "not json at all"


def test_system_init(parser):
    line = json.dumps({
        "type": "system",
        "subtype": "init",
        "session_id": "abc-123",
    })
    result = parser.parse_line(line)
    assert result["event_type"] == "system_init"
    assert result["session_id"] == "abc-123"


def test_assistant_message(parser):
    line = json.dumps({
        "type": "assistant",
        "content": [{"type": "text", "text": "Hello world"}],
    })
    result = parser.parse_line(line)
    assert result["event_type"] == "message"
    assert result["role"] == "assistant"
    assert result["content"] == "Hello world"


def test_tool_use(parser):
    line = json.dumps({
        "type": "tool_use",
        "name": "Read",
        "input": {"file_path": "/tmp/test.py"},
    })
    result = parser.parse_line(line)
    assert result["event_type"] == "tool_use"
    assert result["tool_name"] == "Read"
    assert '"file_path"' in result["tool_input"]


def test_tool_result(parser):
    line = json.dumps({
        "type": "tool_result",
        "content": "file contents here",
    })
    result = parser.parse_line(line)
    assert result["event_type"] == "tool_result"
    assert result["tool_output"] == "file contents here"
    assert result["is_error"] is False


def test_tool_result_error(parser):
    line = json.dumps({
        "type": "tool_result",
        "content": "Error: file not found",
    })
    result = parser.parse_line(line)
    assert result["is_error"] is True


def test_result_with_cost(parser):
    line = json.dumps({
        "type": "result",
        "session_id": "sess-456",
        "total_cost_usd": 0.42,
        "content": [{"type": "text", "text": "Done"}],
    })
    result = parser.parse_line(line)
    assert result["event_type"] == "result"
    assert result["session_id"] == "sess-456"
    assert result["cost_usd"] == 0.42
    assert result["content"] == "Done"


def test_result_is_error(parser):
    line = json.dumps({
        "type": "result",
        "is_error": True,
        "content": "Something failed",
    })
    result = parser.parse_line(line)
    assert result["is_error"] is True


def test_content_extraction_string(parser):
    line = json.dumps({"type": "unknown", "content": "plain string"})
    result = parser.parse_line(line)
    assert result["content"] == "plain string"


def test_content_extraction_list(parser):
    line = json.dumps({
        "type": "unknown",
        "content": [
            {"type": "text", "text": "line 1"},
            {"type": "text", "text": "line 2"},
        ],
    })
    result = parser.parse_line(line)
    assert result["content"] == "line 1\nline 2"


def test_content_extraction_empty_list(parser):
    line = json.dumps({"type": "unknown", "content": []})
    result = parser.parse_line(line)
    assert result["content"] is None


def test_content_extraction_message_wrapper(parser):
    line = json.dumps({
        "type": "unknown",
        "message": {"content": [{"type": "text", "text": "nested"}]},
    })
    result = parser.parse_line(line)
    assert result["content"] == "nested"
