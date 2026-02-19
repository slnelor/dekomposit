import logging
from typing import Any

from dekomposit.llm.tools.base import BaseTool


logger = logging.getLogger(__name__)


class MemoryTool(BaseTool):
    """Tool for agent to manage its memory about the user.

    Allows the agent to:
    - Add free-form memory notes
    - View current memory state
    - Remove or clear notes
    """

    def __init__(self, agent: Any = None) -> None:
        super().__init__(
            name="memory",
            description="Manage free-form memory notes about the user. Use add/get/remove/clear actions.",
        )
        self._agent = agent

    def set_agent(self, agent: Any) -> None:
        """Set the agent reference for memory access."""
        self._agent = agent

    async def __call__(
        self,
        action: str,
        note: str | None = None,
        remove_note: str | None = None,
    ) -> dict[str, Any]:
        """Execute memory management action.

        Args:
            action: One of: 'add', 'get', 'remove', 'clear'
            note: A free-form memory note to store
            remove_note: A free-form memory note to remove

        Returns:
            Dict with status and current memory state
        """
        if self._agent is None or not hasattr(self._agent, "memory"):
            return {
                "status": "error",
                "message": "Agent memory not available",
            }

        memory = self._agent.memory

        if action == "get":
            return {
                "status": "success",
                "notes": memory.notes,
                "history_size": len(memory.conversation_history),
            }

        if action == "add":
            if not note:
                return {
                    "status": "error",
                    "message": "Missing required 'note' for add action",
                }
            memory.add_note(note)

        elif action == "remove":
            if not remove_note:
                return {
                    "status": "error",
                    "message": "Missing required 'remove_note' for remove action",
                }
            removed = memory.remove_note(remove_note)
            if not removed:
                return {
                    "status": "error",
                    "message": "Note not found",
                    "notes": memory.notes,
                }

        elif action == "clear":
            memory.clear_notes()

        else:
            return {
                "status": "error",
                "message": f"Unsupported action: {action}",
            }

        # Rebuild prompt with updated memory
        self._agent._rebuild_base_prompt()

        return {
            "status": "success",
            "message": f"Memory updated: {action}",
            "notes": memory.notes,
            "history_size": len(memory.conversation_history),
        }

    def get_schema(self) -> dict[str, Any]:
        """Return OpenAI function calling schema."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "One of: add, get, remove, clear",
                    "enum": ["add", "get", "remove", "clear"],
                },
                "note": {
                    "type": "string",
                    "description": "Free-form note to store when action=add",
                },
                "remove_note": {
                    "type": "string",
                    "description": "Existing note to remove when action=remove",
                },
            },
            "required": ["action"],
        }
