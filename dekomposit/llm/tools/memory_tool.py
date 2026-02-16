import logging
from typing import Any

from dekomposit.llm.tools.base import BaseTool


logger = logging.getLogger(__name__)


class MemoryTool(BaseTool):
    """Tool for agent to manage its memory about the user.
    
    Allows the agent to:
    - Add learning gaps (mistakes the user makes repeatedly)
    - Add topics of interest
    - Set teaching style preference
    - Set speaking style preference
    - Set tone/vibe
    - View current memory state
    - Remove items from memory
    """

    def __init__(self, agent: Any = None) -> None:
        super().__init__(
            name="memory",
            description="Manage memory about the user. Use to record learning gaps, topics, preferences, and insights about the user. Call with action='get' to see current memory.",
        )
        self._agent = agent

    def set_agent(self, agent: Any) -> None:
        """Set the agent reference for memory access."""
        self._agent = agent

    async def __call__(
        self,
        action: str,
        learning_gap: str | None = None,
        topic: str | None = None,
        teaching_style: str | None = None,
        speaking_style: str | None = None,
        tone_vibe: str | None = None,
        remove_item: str | None = None,
        remove_type: str | None = None,
    ) -> dict[str, Any]:
        """Execute memory management action.
        
        Args:
            action: One of: 'add', 'set', 'get', 'remove', 'clear'
            learning_gap: A pattern of mistake to remember (e.g., 'verb_conjugation', 'dativ_case')
            topic: Topic of interest to add
            teaching_style: 'explanation', 'practice', or 'balanced'
            speaking_style: 'short', 'detailed', or 'casual'
            tone_vibe: 'chill', 'energetic', 'serious', etc.
            remove_item: Item to remove from a list
            remove_type: Type of item to remove: 'learning_gap', 'topic'
            
        Returns:
            Dict with status and current memory state
        """
        if self._agent is None or not hasattr(self._agent, 'memory'):
            return {
                "status": "error",
                "message": "Agent memory not available",
            }

        memory = self._agent.memory

        if action == "get":
            return {
                "status": "success",
                "learning_gaps": memory.learning_gaps,
                "topics": memory.topics,
                "teaching_style": memory.teaching_style,
                "speaking_style": memory.speaking_style,
                "tone_vibe": memory.tone_vibe,
                "mistake_count": memory.mistake_count,
            }

        if action == "add":
            if learning_gap:
                if learning_gap not in memory.learning_gaps:
                    memory.learning_gaps.append(learning_gap)
                    logger.info(f"Added learning gap: {learning_gap}")
            if topic:
                memory.add_topic(topic)

        elif action == "set":
            if teaching_style:
                memory.set_teaching_style(teaching_style)
            if speaking_style:
                memory.set_speaking_style(speaking_style)
            if tone_vibe:
                memory.set_tone_vibe(tone_vibe)

        elif action == "remove":
            if remove_type == "learning_gap" and remove_item:
                if remove_item in memory.learning_gaps:
                    memory.learning_gaps.remove(remove_item)
            elif remove_type == "topic" and remove_item:
                if remove_item in memory.topics:
                    memory.topics.remove(remove_item)

        elif action == "clear":
            if remove_type == "learning_gaps":
                memory.learning_gaps.clear()
            elif remove_type == "topics":
                memory.topics.clear()
            elif remove_type == "history":
                memory.conversation_history.clear()

        # Rebuild prompt with updated memory
        self._agent._rebuild_base_prompt()

        return {
            "status": "success",
            "message": f"Memory updated: {action}",
            "learning_gaps": memory.learning_gaps,
            "topics": memory.topics,
            "teaching_style": memory.teaching_style,
            "speaking_style": memory.speaking_style,
            "tone_vibe": memory.tone_vibe,
        }
