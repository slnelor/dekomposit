import logging
import importlib
import pkgutil
from pathlib import Path
from typing import Any, Callable

from dekomposit.llm.tools.base import BaseTool


logging.basicConfig(
    datefmt="%d/%m/%Y %H:%M",
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ToolRegistry:
    """Central registry for managing agent tools with auto-discovery.
    
    Supports:
    - Auto-discovery of tools from the tools package
    - Manual registration of tools
    - Lookup by name
    - Listing all available tools
    """

    def __init__(self, auto_discover: bool = True) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._tool_factories: dict[str, Callable[[], BaseTool]] = {}
        
        if auto_discover:
            self._auto_discover()

    def _auto_discover(self) -> None:
        tools_dir = Path(__file__).parent
        package_name = "dekomposit.llm.tools"

        for _, module_name, _ in pkgutil.iter_modules([str(tools_dir)]):
            if module_name in ("base", "registry"):
                continue

            full_module_name = f"{package_name}.{module_name}"
            try:
                module = importlib.import_module(full_module_name)
                
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, BaseTool)
                        and attr is not BaseTool
                    ):
                        self.register_factory(attr_name.lower(), attr)
                        logger.debug(f"Discovered tool: {attr_name}")
            except ImportError as e:
                logger.warning(f"Failed to import module {full_module_name}: {e}")

        logger.info(f"Auto-discovered {len(self._tool_factories)} tool factories")

    def register(self, tool: BaseTool) -> None:
        """Register a tool instance."""
        self._tools[tool.name] = tool
        logger.debug(f"Registered tool: {tool.name}")

    def register_factory(
        self, name: str, factory: type[BaseTool] | Callable[[], BaseTool]
    ) -> None:
        """Register a tool factory (class or callable)."""
        def create_tool() -> BaseTool:
            if isinstance(factory, type):
                return factory()  # type: ignore[call-arg]
            return factory()
        
        self._tool_factories[name] = create_tool
        logger.debug(f"Registered factory: {name}")

    def get(self, name: str) -> BaseTool | None:
        """Get a tool by name, creating it from factory if needed.
        
        Args:
            name: Tool name (can be registry key or tool.name)
            
        Returns:
            Tool instance or None
        """
        # First try exact match
        if name in self._tools:
            return self._tools[name]
        
        if name in self._tool_factories:
            factory = self._tool_factories[name]
            tool = factory() if callable(factory) and not isinstance(factory, type) else factory()
            self._tools[name] = tool
            return tool
        
        # Try matching by tool.name (for when LLM calls tool by its internal name)
        for key, factory in self._tool_factories.items():
            tool = factory() if callable(factory) and not isinstance(factory, type) else factory()
            if tool.name == name:
                self._tools[key] = tool
                return tool
        
        return None

    def has(self, name: str) -> bool:
        """Check if a tool exists."""
        if name in self._tools or name in self._tool_factories:
            return True
        # Also check by tool.name
        for key, factory in self._tool_factories.items():
            tool = factory() if callable(factory) and not isinstance(factory, type) else factory()
            if tool.name == name:
                return True
        return False

    def list_tools(self) -> list[str]:
        """List all available tool names."""
        names = set(self._tools.keys()) | set(self._tool_factories.keys())
        return sorted(names)

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        """Get OpenAI-compatible tool schemas for all registered tools."""
        schemas: list[dict[str, Any]] = []
        
        for name in self.list_tools():
            tool = self.get(name)
            if tool:
                schemas.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.get_schema(),
                    },
                })
        
        return schemas

    async def execute(self, name: str, *args: Any, **kwargs: Any) -> Any:
        """Execute a tool by name."""
        tool = self.get(name)
        if tool is None:
            raise ValueError(f"Tool not found: {name}")
        return await tool(*args, **kwargs)

    def clear(self) -> None:
        """Clear all registered tools and factories."""
        self._tools.clear()
        self._tool_factories.clear()
