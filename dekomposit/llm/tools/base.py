from abc import ABC, abstractmethod
from typing import Any
import logging


logging.basicConfig(
    datefmt="%d/%m/%Y %H:%M",
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class BaseTool(ABC):
    """Abstract base class for all tools

    Tools are callable objects that perform specific actions.
    Each tool must implement the __call__ method with its core logic.

    Attributes:
        name: Unique identifier for the tool
        description: Human-readable description of what the tool does
    """

    def __init__(self, name: str, description: str) -> None:
        """Initialize the tool

        Args:
            name: Unique name for the tool
            description: What the tool does
        """
        self.name = name
        self.description = description
        logger.debug(f"Initialized tool: {self.name}")

    @abstractmethod
    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the tool's main logic

        This method must be implemented by all concrete tool classes.

        Args:
            *args: Positional arguments for the tool
            **kwargs: Keyword arguments for the tool

        Returns:
            Tool execution result

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement __call__ method"
        )

    def validate_input(self, *args: Any, **kwargs: Any) -> bool:
        """Validate input parameters before execution

        Override this method to add custom validation logic.

        Args:
            *args: Positional arguments to validate
            **kwargs: Keyword arguments to validate

        Returns:
            True if input is valid, False otherwise
        """
        return True

    def __repr__(self) -> str:
        """String representation of the tool"""
        return f"{self.__class__.__name__}(name='{self.name}')"

    def __str__(self) -> str:
        """Human-readable string representation"""
        return f"{self.name}: {self.description}"

    def get_schema(self) -> dict[str, Any]:
        """Return OpenAI function calling schema for this tool.
        
        Override this in subclasses to define custom parameters.
        
        Returns:
            JSON Schema dict for tool parameters
        """
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }


