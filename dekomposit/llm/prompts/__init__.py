import logging
from pathlib import Path


logger = logging.getLogger(__name__)


class PromptRegistry:
    """Registry for loading prompts from files.

    Auto-discovers .md files from prompts/ directory.
    Supports subdirectories for organization.
    """

    def __init__(self, prompts_dir: Path | None = None) -> None:
        self._prompts: dict[str, str] = {}
        self._prompts_dir = prompts_dir or Path(__file__).parent
        self._discover_prompts()

    def _discover_prompts(self) -> None:
        """Discover all .md files in prompts directory."""
        if not self._prompts_dir.exists():
            logger.warning(f"Prompts directory not found: {self._prompts_dir}")
            return

        for md_file in self._prompts_dir.rglob("*.md"):
            relative_path = md_file.relative_to(self._prompts_dir)
            prompt_name = str(relative_path.with_suffix("")).replace("/", ".")

            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    self._prompts[prompt_name] = f.read()
                logger.debug(f"Loaded prompt: {prompt_name}")
            except Exception as e:
                logger.error(f"Failed to load prompt {md_file}: {e}")

        logger.info(f"Discovered {len(self._prompts)} prompts")

    def get(self, name: str) -> str | None:
        """Get a prompt by name.

        Args:
            name: Prompt name (e.g., "routing", "detection", "translation.summarize")

        Returns:
            Prompt content or None if not found
        """
        return self._prompts.get(name)

    def has(self, name: str) -> bool:
        """Check if a prompt exists."""
        return name in self._prompts

    def list_all(self) -> list[str]:
        """List all available prompt names."""
        return sorted(self._prompts.keys())
