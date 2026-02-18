import json
import logging
from pathlib import Path
from typing import Any, AsyncGenerator, Mapping, TypedDict

from dekomposit.llm.base_client import Client
from dekomposit.llm.formatting import FormatRegistry
from dekomposit.llm.memory import UserMemory
from dekomposit.llm.prompts import PromptRegistry
from dekomposit.llm.tools.registry import ToolRegistry


logging.basicConfig(
    datefmt="%d/%m/%Y %H:%M",
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ToolCallRecord(TypedDict):
    tool_name: str
    arguments: dict[str, Any]
    result: dict[str, Any]


class AgentResult(TypedDict):
    type: str
    message: str
    tool_calls: list[ToolCallRecord]


class Agent:
    """Agent orchestrator for tool-calling language coaching interactions."""

    def __init__(
        self,
        model: str | None = None,
        server: str | None = None,
        user_id: int | None = None,
    ) -> None:
        self.client = Client(model=model, server=server)
        self.registry = ToolRegistry(auto_discover=True)
        self.formats = FormatRegistry()
        self.prompts = PromptRegistry()

        self.user_id = user_id
        self.memory = UserMemory(user_id=user_id)

        self._load_memory()
        self.custom_personality: dict[str, str] = {}
        self.base_prompts = self._load_base_prompts()
        self.base_prompt = self._build_base_prompt(self.base_prompts)

        logger.info("Agent initialized with model: %s", self.client.model)
        logger.info("Available tools: %s", self.registry.list_tools())
        logger.info("Tool schemas available: %s", len(self.registry.get_tool_schemas()))

    async def execute_tools(self, text: str, max_iterations: int = 5) -> AgentResult:
        """Public compatibility method for the tool loop."""
        return await self._run_tool_loop(text=text, max_iterations=max_iterations)

    async def handle_message(self, text: str) -> AgentResult | None:
        """Process one user message through the unified tool-loop pipeline."""
        self.memory.add_message("user", text)

        result = await self._run_tool_loop(text=text)

        message = result.get("message", "")
        if result.get("type") == "response" and message:
            self.memory.add_message("assistant", message)
            self._rebuild_base_prompt()

        return result

    async def chat(self, text: str) -> str:
        """Entrypoint for chat: returns formatted response string."""
        result = await self.handle_message(text)
        if result is None:
            return "Sorry, I couldn't process that."

        if result.get("type") == "translation":
            return self.format_translation(result)

        return result.get("message", "")

    async def stream_chat(self, text: str) -> AsyncGenerator[str, None]:
        """Unified streaming entrypoint based on the same core pipeline."""
        result = await self.handle_message(text)
        if result is None:
            yield "Sorry, I couldn't process that."
            return

        if result.get("type") == "translation":
            yield self.format_translation(result)
            return

        yield result.get("message", "")

    async def _run_tool_loop(self, text: str, max_iterations: int = 5) -> AgentResult:
        """Run iterative tool-calling loop until final assistant response."""
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self.base_prompt},
            {"role": "user", "content": text},
        ]
        tool_call_history: list[ToolCallRecord] = []

        for iteration in range(max_iterations):
            logger.debug("Agent loop iteration %s/%s", iteration + 1, max_iterations)

            tools = self.registry.get_tool_schemas()
            response = await self.client.request_with_tools(
                messages=messages,
                tools=tools if tools else None,
            )

            message = response.choices[0].message
            tool_calls = message.tool_calls

            if not tool_calls:
                final_message = message.content or ""
                return {
                    "type": "response",
                    "message": final_message,
                    "tool_calls": tool_call_history,
                }

            assistant_content = message.content or "[TOOL CALL]"
            messages.append(
                self._build_assistant_tool_message(
                    content=assistant_content,
                    tool_calls=tool_calls,
                )
            )

            logger.info("LLM requested %s tool call(s)", len(tool_calls))

            for tool_call in tool_calls:
                record = await self._execute_tool_call(tool_call)
                tool_call_history.append(record)

                messages.append(
                    self._build_tool_message(
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

    def _build_assistant_tool_message(
        self, content: str, tool_calls: list[Any]
    ) -> dict[str, Any]:
        """Build assistant message containing tool call descriptors."""
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

    async def _execute_tool_call(self, tool_call: Any) -> ToolCallRecord:
        """Execute one tool call and normalize result/error payload."""
        tool_name = tool_call.function.name
        tool_args = self._safe_parse_tool_arguments(tool_call.function.arguments)

        logger.info("Executing tool: %s with args: %s", tool_name, tool_args)

        tool = self.registry.get(tool_name)
        if tool is None:
            logger.warning("Tool not found: %s", tool_name)
            tool_result: dict[str, Any] = {"error": f"Tool not found: {tool_name}"}
            return {
                "tool_name": tool_name,
                "arguments": tool_args,
                "result": tool_result,
            }

        try:
            raw_result = await tool(**tool_args)
            tool_result = self._normalize_tool_result(raw_result)
        except Exception as exc:
            logger.exception("Tool execution failed for %s", tool_name)
            tool_result = {
                "error": "Tool execution failed",
                "details": str(exc),
            }

        return {
            "tool_name": tool_name,
            "arguments": tool_args,
            "result": tool_result,
        }

    def _build_tool_message(
        self,
        tool_call: Any,
        tool_name: str,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        """Build tool response message to feed back to the model."""
        tool_call_id = tool_call.id if tool_call.id else tool_name
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": json.dumps(result, ensure_ascii=False),
        }

    @staticmethod
    def _safe_parse_tool_arguments(arguments: str) -> dict[str, Any]:
        """Parse tool arguments payload safely."""
        try:
            parsed = json.loads(arguments)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}

    @staticmethod
    def _normalize_tool_result(raw_result: Any) -> dict[str, Any]:
        """Ensure tool result is JSON-serializable dict payload."""
        if isinstance(raw_result, dict):
            return raw_result
        return {"result": raw_result}

    def _load_memory(self) -> None:
        """Load user memory from storage. Currently a stub."""
        logger.debug("Loaded memory for user %s", self.user_id or "anonymous")

    def _load_base_prompts(self) -> dict[str, str]:
        """Read all prompt files from base_prompts/ directory."""
        prompts: dict[str, str] = {}
        prompting_dir = Path(__file__).parent / "base_prompts"

        if not prompting_dir.exists():
            logger.warning("Base prompts directory not found: %s", prompting_dir)
            return prompts

        for file_path in prompting_dir.glob("*.md"):
            try:
                with open(file_path, "r", encoding="utf-8") as prompt_file:
                    prompts[file_path.name] = prompt_file.read()
            except Exception as exc:
                logger.error("Failed to read %s: %s", file_path.name, exc)

        logger.info("Loaded %s prompt files: %s", len(prompts), list(prompts.keys()))
        return prompts

    def _build_base_prompt(self, prompts: dict[str, str]) -> str:
        """Aggregate SOUL and MEMORY prompts into a single system prompt."""
        sections: list[str] = []

        soul_content = prompts.get("SOUL.md", "").strip()
        if soul_content:
            try:
                custom_soul = self.custom_personality.get("SOUL.md", "")
                soul_content = soul_content.replace(
                    "{custom_personality['SOUL.md']}",
                    custom_soul,
                )
                soul_content = soul_content.format(
                    custom_personality=self.custom_personality
                )
            except Exception as exc:
                logger.warning("Failed to format SOUL: %s", exc)
            sections.append(soul_content)

        memory_content = prompts.get("MEMORY.md", "").strip()
        if memory_content:
            try:
                custom_memory = self.custom_personality.get("MEMORY.md", "")
                memory_content = memory_content.replace(
                    "{custom_personality['MEMORY.md']}",
                    custom_memory,
                )

                memory_content = memory_content.replace(
                    "{learning_gaps}",
                    ", ".join(self.memory.learning_gaps)
                    if self.memory.learning_gaps
                    else "Still learning...",
                )
                memory_content = memory_content.replace(
                    "{topics}",
                    ", ".join(self.memory.topics)
                    if self.memory.topics
                    else "Nothing specific yet",
                )
                memory_content = memory_content.replace(
                    "{teaching_style}", self.memory.teaching_style
                )
                memory_content = memory_content.replace(
                    "{speaking_style}", self.memory.speaking_style
                )
                memory_content = memory_content.replace(
                    "{tone_vibe}", self.memory.tone_vibe
                )
                memory_content = memory_content.replace(
                    "{conversation_history}", self._get_conversation_summary()
                )
            except Exception as exc:
                logger.warning("Failed to format memory: %s", exc)
                memory_content = ""

            if memory_content.strip():
                sections.append(memory_content)

        return "\n\n".join(sections).strip()

    def _get_conversation_summary(self) -> str:
        """Get a summary of recent conversation for memory injection."""
        if not self.memory.conversation_history:
            return "No history yet"

        recent = self.memory.conversation_history[-10:]
        lines: list[str] = []
        for msg in recent:
            role = msg.get("role", "?")
            content = msg.get("content", "")
            if len(content) > 100:
                content = f"{content[:100]}..."
            lines.append(f"- {role}: {content}")

        return "\n".join(lines)

    def _rebuild_base_prompt(self) -> None:
        """Rebuild base prompt with updated memory."""
        self.base_prompt = self._build_base_prompt(self._load_base_prompts())
        logger.debug("Rebuilt base prompt with updated memory")

    def format_translation(self, result: Mapping[str, Any]) -> str:
        """Format translation result using format registry."""
        source = result.get("source_lang", "").upper()
        target = result.get("target_lang", "").upper()
        translation = result.get("translation", "")

        return self.formats.render(
            None,
            source=source,
            target=target,
            translation=translation,
        )
