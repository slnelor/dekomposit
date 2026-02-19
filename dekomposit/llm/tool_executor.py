import json
import logging
from typing import Any, TypedDict

from dekomposit.llm.tools.registry import ToolRegistry


logger = logging.getLogger(__name__)


class ToolCallRecord(TypedDict):
    tool_name: str
    arguments: dict[str, Any]
    result: dict[str, Any]


class ToolExecutor:
    """Execute model tool calls and normalize results."""

    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    async def execute(self, tool_call: Any) -> ToolCallRecord:
        tool_name = tool_call.function.name
        tool_args = self.safe_parse_tool_arguments(tool_call.function.arguments)

        logger.info("Executing tool: %s with args: %s", tool_name, tool_args)

        tool = self._registry.get(tool_name)
        if tool is None:
            return {
                "tool_name": tool_name,
                "arguments": tool_args,
                "result": {"error": f"Tool not found: {tool_name}"},
            }

        try:
            raw_result = await tool(**tool_args)
            result = self.normalize_tool_result(raw_result)
        except Exception as exc:
            logger.exception("Tool execution failed for %s", tool_name)
            result = {
                "error": "Tool execution failed",
                "details": str(exc),
            }

        return {
            "tool_name": tool_name,
            "arguments": tool_args,
            "result": result,
        }

    @staticmethod
    def safe_parse_tool_arguments(arguments: str) -> dict[str, Any]:
        try:
            parsed = json.loads(arguments)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}

    @staticmethod
    def normalize_tool_result(raw_result: Any) -> dict[str, Any]:
        if isinstance(raw_result, dict):
            return raw_result
        return {"result": raw_result}

    @staticmethod
    def build_assistant_tool_message(
        content: str, tool_calls: list[Any]
    ) -> dict[str, Any]:
        return {
            "role": "assistant",
            "content": content,
            "tool_calls": [
                {
                    "id": tc.id if tc.id else tc.function.name,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in tool_calls
            ],
        }

    @staticmethod
    def build_tool_message(
        tool_call: Any,
        tool_name: str,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        tool_call_id = tool_call.id if tool_call.id else tool_name
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": json.dumps(result, ensure_ascii=False),
        }
