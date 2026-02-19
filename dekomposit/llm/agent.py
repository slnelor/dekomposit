import logging
from typing import Any

from dekomposit.llm.base_client import Client
from dekomposit.llm.formatting import FormatRegistry
from dekomposit.llm.memory import UserMemory
from dekomposit.llm.prompt_composer import PromptComposer
from dekomposit.llm.renderer import AgentRenderer
from dekomposit.llm.tool_loop import AgentResult, ToolLoopRunner
from dekomposit.llm.tools.registry import ToolRegistry


logger = logging.getLogger(__name__)


class Agent:
    """Agent orchestrator for tool-calling language coaching interactions."""

    def __init__(
        self,
        model: str | None = None,
        provider: str | None = None,
    ) -> None:
        self.client = Client(model=model, provider=provider)
        self.registry = ToolRegistry(auto_discover=True)
        self.registry.bind_agent(self)
        self.formats = FormatRegistry()

        self.memory = UserMemory()
        self.custom_personality: dict[str, str] = {}
        self.prompt_composer = PromptComposer()
        self.base_prompts = self.prompt_composer.load_base_prompts()
        self.base_prompt = self._compose_base_prompt()
        self.renderer = AgentRenderer(formats=self.formats)

        logger.info("Agent initialized with model: %s", self.client.model)
        logger.info("Available tools: %s", self.registry.list_tools())
        logger.info(
            "Enabled tools exposed to model: %s", self.registry.list_enabled_tools()
        )

    async def execute_tools(self, text: str, max_iterations: int = 5) -> AgentResult:
        """Public compatibility method for the tool loop."""
        return await self._loop_runner().run(
            text=text,
            system_prompt=self.base_prompt,
            max_iterations=max_iterations,
        )

    async def handle_message(self, text: str) -> AgentResult:
        """Process one user message through the unified tool-loop pipeline."""
        self.memory.add_message("user", text)

        result = await self._loop_runner().run(
            text=text,
            system_prompt=self.base_prompt,
        )

        message = result.get("message", "")
        if result.get("type") == "response" and message:
            self.memory.add_message("assistant", message)
            self._rebuild_base_prompt()

        return result

    async def chat(self, text: str) -> str:
        """Entrypoint for chat responses."""
        result = await self.handle_message(text)
        return self.renderer.render(result)

    def _compose_base_prompt(self) -> str:
        memory_markdown = self.memory.to_markdown()
        return self.prompt_composer.compose(
            prompts=self.base_prompts,
            custom_personality=self.custom_personality,
            memory_markdown=memory_markdown,
        )

    def _loop_runner(self) -> ToolLoopRunner:
        return ToolLoopRunner(client=self.client, registry=self.registry)

    def _rebuild_base_prompt(self) -> None:
        self.base_prompt = self._compose_base_prompt()
        logger.debug("Rebuilt base prompt with updated memory")
