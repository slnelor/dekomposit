import importlib
import logging
import pkgutil
from pathlib import Path
from typing import Any, Callable, Iterable

from dekomposit.llm.tools.base import BaseTool


logger = logging.getLogger(__name__)


class ToolRegistry:
    """Central registry for managing agent tools with auto-discovery."""

    def __init__(
        self,
        auto_discover: bool = True,
        include_disabled_in_schema: bool = False,
    ) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._aliases: dict[str, str] = {}
        self._include_disabled_in_schema = include_disabled_in_schema

        if auto_discover:
            self._auto_discover()

    def _auto_discover(self) -> None:
        tools_dir = Path(__file__).parent
        package_name = "dekomposit.llm.tools"
        discovered = 0

        for _, module_name, _ in pkgutil.iter_modules([str(tools_dir)]):
            if module_name in {"base", "registry", "__init__"}:
                continue

            full_module_name = f"{package_name}.{module_name}"
            try:
                module = importlib.import_module(full_module_name)
            except Exception as exc:
                logger.warning("Failed to import module %s: %s", full_module_name, exc)
                continue

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if not isinstance(attr, type):
                    continue
                if not issubclass(attr, BaseTool) or attr is BaseTool:
                    continue

                try:
                    tool = attr()
                except Exception as exc:
                    logger.warning("Failed to instantiate tool %s: %s", attr_name, exc)
                    continue

                alias = attr_name.lower()
                self.register(tool, aliases=[alias])
                discovered += 1

        logger.info("Auto-discovered %s tools", discovered)

    def register(self, tool: BaseTool, aliases: Iterable[str] | None = None) -> None:
        """Register a tool instance."""
        self._tools[tool.name] = tool

        if aliases:
            for alias in aliases:
                if alias and alias != tool.name:
                    self._aliases[alias] = tool.name

        logger.debug("Registered tool: %s", tool.name)

    def register_factory(
        self,
        name: str,
        factory: type[BaseTool] | Callable[[], BaseTool],
    ) -> None:
        """Compatibility API: build tool once and register under alias."""
        tool = factory() if callable(factory) else factory  # pragma: no cover
        self.register(tool, aliases=[name])

    def bind_agent(self, agent: Any) -> None:
        """Bind agent context to tools that support set_agent()."""
        for tool in self._tools.values():
            setter = getattr(tool, "set_agent", None)
            if callable(setter):
                setter(agent)

    def _resolve_name(self, name: str) -> str:
        return self._aliases.get(name, name)

    def get(self, name: str) -> BaseTool | None:
        """Get a tool by canonical name or alias."""
        return self._tools.get(self._resolve_name(name))

    def has(self, name: str) -> bool:
        """Check if a tool exists by canonical name or alias."""
        return self.get(name) is not None

    def list_tools(self) -> list[str]:
        """List all registered canonical tool names."""
        return sorted(self._tools.keys())

    def list_enabled_tools(self) -> list[str]:
        """List tool names that are enabled."""
        return sorted(name for name, tool in self._tools.items() if tool.enabled)

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        """Get OpenAI-compatible schemas for tools exposed to the model."""
        schemas: list[dict[str, Any]] = []
        for name in self.list_tools():
            tool = self._tools[name]
            if not tool.enabled and not self._include_disabled_in_schema:
                continue
            schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.get_schema(),
                    },
                }
            )
        return schemas

    async def execute(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """Execute a tool by canonical name or alias."""
        tool = self.get(name)
        if tool is None:
            raise ValueError(f"Tool not found: {name}")
        return await tool(*args, **kwargs)

    def clear(self) -> None:
        """Clear all registered tools and aliases."""
        self._tools.clear()
        self._aliases.clear()
