import json
from datetime import datetime


class StreamParser:
    """Parse Claude Code stream-json (NDJSON) output into structured events."""

    def parse_line(self, line: str) -> dict | None:
        if not line.strip():
            return None
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            return {
                "event_type": "parse_error",
                "content": line,
                "is_error": True,
                "timestamp": datetime.utcnow().isoformat(),
            }

        event_type = data.get("type", "unknown")

        event = {
            "event_type": event_type,
            "role": data.get("role"),
            "content": self._extract_content(data),
            "tool_name": None,
            "tool_input": None,
            "tool_output": None,
            "raw_json": line,
            "is_error": False,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Extract session_id from system/init or result events
        if event_type == "system" and data.get("subtype") == "init":
            event["session_id"] = data.get("session_id")
            event["event_type"] = "system_init"
        elif event_type == "assistant":
            event["role"] = "assistant"
            event["event_type"] = "message"
        elif event_type == "tool_use":
            event["tool_name"] = data.get("name")
            event["tool_input"] = json.dumps(data.get("input", {}))
        elif event_type == "tool_result":
            event["tool_output"] = self._extract_content(data) or ""
            if isinstance(event["tool_output"], str) and "error" in event["tool_output"].lower():
                event["is_error"] = True
        elif event_type == "result":
            event["content"] = self._extract_content(data)
            event["session_id"] = data.get("session_id")
            cost = data.get("total_cost_usd")
            if cost is not None:
                event["cost_usd"] = cost
            if data.get("is_error"):
                event["is_error"] = True

        return event

    def _extract_content(self, data: dict) -> str | None:
        # Handle content blocks (list of {type, text})
        content = data.get("content")
        if isinstance(content, list):
            texts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
            return "\n".join(texts) if texts else None
        if isinstance(content, str):
            return content
        # Handle message wrapper
        message = data.get("message")
        if isinstance(message, dict):
            return self._extract_content(message)
        return None
