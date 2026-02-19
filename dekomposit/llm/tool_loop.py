import logging
from typing import Any, TypedDict

from dekomposit.llm.base_client import Client
from dekomposit.llm.tool_executor import ToolCallRecord, ToolExecutor
from dekomposit.llm.tools.registry import ToolRegistry


logger = logging.getLogger(__name__)


class AgentResult(TypedDict):
    type: str
    message: str
    tool_calls: list[ToolCallRecord]


class ToolLoopRunner:
    """Run iterative tool-calling loop until model returns final response."""

    def __init__(self, client: Client, registry: ToolRegistry) -> None:
        self._client = client
        self._registry = registry
        self._executor = ToolExecutor(registry)

    async def run(
        self,
        text: str,
        system_prompt: str,
        max_iterations: int = 5,
    ) -> AgentResult:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ]
        tool_call_history: list[ToolCallRecord] = []

        for iteration in range(max_iterations):
            logger.debug("Agent loop iteration %s/%s", iteration + 1, max_iterations)
            response = await self._client.request_with_tools(
                messages=messages,
                tools=self._registry.get_tool_schemas() or None,
            )
            message = response.choices[0].message
            tool_calls = message.tool_calls

            if not tool_calls:
                return {
                    "type": "response",
                    "message": message.content or "",
                    "tool_calls": tool_call_history,
                }

            assistant_content = message.content or "[TOOL CALL]"
            messages.append(
                self._executor.build_assistant_tool_message(
                    assistant_content, tool_calls
                )
            )
            logger.info("LLM requested %s tool call(s)", len(tool_calls))

            for tool_call in tool_calls:
                record = await self._executor.execute(tool_call)
                tool_call_history.append(record)
                messages.append(
                    self._executor.build_tool_message(
                        tool_call=tool_call,
                        tool_name=record["tool_name"],
                        result=record["result"],
                    )
                )

        logger.warning("Max iterations reached in agent loop")
        return {
            "type": "error",
            "message": "Maximum iterations reached",
            "tool_calls": tool_call_history,
        }
