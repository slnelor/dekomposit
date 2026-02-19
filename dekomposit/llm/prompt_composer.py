import logging
from pathlib import Path
from typing import Mapping


logger = logging.getLogger(__name__)


class PromptComposer:
    """Compose deterministic base prompt from prompt files and memory."""

    def __init__(self, base_prompts_dir: Path | None = None) -> None:
        self._base_prompts_dir = (
            base_prompts_dir or Path(__file__).parent / "base_prompts"
        )

    def load_base_prompts(self) -> dict[str, str]:
        prompts: dict[str, str] = {}
        if not self._base_prompts_dir.exists():
            logger.warning(
                "Base prompts directory not found: %s", self._base_prompts_dir
            )
            return prompts

        for file_path in self._base_prompts_dir.glob("*.md"):
            try:
                prompts[file_path.name] = file_path.read_text(encoding="utf-8")
            except Exception as exc:
                logger.error("Failed to read %s: %s", file_path.name, exc)

        return prompts

    def compose(
        self,
        prompts: Mapping[str, str],
        custom_personality: Mapping[str, str],
        memory_markdown: str,
    ) -> str:
        sections: list[str] = []

        soul = prompts.get("SOUL.md", "").strip()
        if soul:
            soul = soul.replace(
                "{custom_personality['SOUL.md']}",
                custom_personality.get("SOUL.md", ""),
            )
            sections.append(soul)

        memory = prompts.get("MEMORY.md", "").strip()
        if memory:
            memory = memory.replace(
                "{custom_personality['MEMORY.md']}",
                custom_personality.get("MEMORY.md", ""),
            )
            memory = memory.replace("{memory_markdown}", memory_markdown)
            sections.append(memory)

        return "\n\n".join(part for part in sections if part).strip()
