from abc import ABC, abstractmethod
import logging
from typing import Any


logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """Abstract base class for all tools."""

    def __init__(self, name: str, description: str, enabled: bool = True) -> None:
        self.name = name
        self.description = description
        self.enabled = enabled
        logger.debug("Initialized tool: %s", self.name)

    @abstractmethod
    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Execute tool logic."""
        raise NotImplementedError

    def validate_input(self, *args: Any, **kwargs: Any) -> bool:
        """Validate input parameters before execution."""
        return True

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"

    def __str__(self) -> str:
        return f"{self.name}: {self.description}"

    def get_schema(self) -> dict[str, Any]:
        """Return OpenAI function-calling schema for this tool."""
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }
