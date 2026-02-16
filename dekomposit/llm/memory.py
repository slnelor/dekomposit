import logging


logging.basicConfig(
    datefmt="%d/%m/%Y %H:%M",
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class UserMemory:
    def __init__(self, user_id: int | None = None) -> None:
        self.user_id = user_id
        self.learning_gaps: list[str] = []
        self.topics: list[str] = []
        self.teaching_style: str = "balanced"
        self.speaking_style: str = "casual"
        self.tone_vibe: str = "chill"
        self.conversation_history: list[dict[str, str]] = []
        self.mistake_count: dict[str, int] = {}

    def to_markdown(self) -> str:
        gaps = ", ".join(self.learning_gaps) if self.learning_gaps else "Still learning..."
        topics = ", ".join(self.topics) if self.topics else "Nothing specific yet"
        history = "\n".join(
            f"- {msg.get('role', '?')}: {msg.get('content', '')[:100]}..."
            for msg in self.conversation_history[-10:]
        ) if self.conversation_history else "No history yet"

        return f"""## What I Know About You

### Learning Gaps
{gaps}

### Topics You Enjoy
{topics}

### Teaching Style Preference
{self.teaching_style}

### Speaking Style
{self.speaking_style}

### Tone & Vibe
{self.tone_vibe}

### Conversation History
{history}
"""

    def add_mistake(self, mistake_type: str) -> None:
        self.mistake_count[mistake_type] = self.mistake_count.get(mistake_type, 0) + 1
        
        if self.mistake_count[mistake_type] >= 5 and mistake_type not in self.learning_gaps:
            self.learning_gaps.append(mistake_type)
            logger.info(f"Added learning gap: {mistake_type}")

    def add_topic(self, topic: str) -> None:
        topic_lower = topic.lower().strip()
        if topic_lower and topic_lower not in [t.lower() for t in self.topics]:
            self.topics.append(topic)
            logger.debug(f"Added topic: {topic}")

    def set_teaching_style(self, style: str) -> None:
        self.teaching_style = style

    def set_speaking_style(self, style: str) -> None:
        self.speaking_style = style

    def set_tone_vibe(self, vibe: str) -> None:
        self.tone_vibe = vibe

    def add_message(self, role: str, content: str) -> None:
        self.conversation_history.append({"role": role, "content": content})
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
