import logging


logger = logging.getLogger(__name__)


class UserMemory:
    def __init__(self) -> None:
        self.notes: list[str] = []
        self.conversation_history: list[dict[str, str]] = []

    def to_markdown(self) -> str:
        notes = (
            "\n".join(f"- {note}" for note in self.notes[-20:])
            if self.notes
            else "No memory notes yet"
        )
        history = (
            "\n".join(
                f"- {msg.get('role', '?')}: {msg.get('content', '')[:100]}..."
                for msg in self.conversation_history[-10:]
            )
            if self.conversation_history
            else "No history yet"
        )

        return f"""## Memory Notes
{notes}

## Recent Conversation
{history}
"""

    def add_note(self, note: str) -> None:
        cleaned = note.strip()
        if not cleaned:
            return

        existing = {item.lower() for item in self.notes}
        if cleaned.lower() in existing:
            return

        self.notes.append(cleaned)
        logger.info("Added memory note")

    def remove_note(self, note: str) -> bool:
        lowered = note.strip().lower()
        if not lowered:
            return False

        for existing in list(self.notes):
            if existing.lower() == lowered:
                self.notes.remove(existing)
                return True
        return False

    def clear_notes(self) -> None:
        self.notes.clear()

    def add_message(self, role: str, content: str) -> None:
        self.conversation_history.append({"role": role, "content": content})
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
