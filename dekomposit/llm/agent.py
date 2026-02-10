import logging
from pathlib import Path

from dekomposit.llm.base_client import Client


logging.basicConfig(
    datefmt="%d/%m/%Y %H:%M",
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Agent:
    """Base agent class with LLM client, memory, and prompt management"""

    def __init__(
        self,
        model: str | None = None,
        server: str | None = None,
    ) -> None:
        """Initialize agent with LLM client and empty state

        Args:
            model: LLM model to use (defaults to config)
            server: LLM server URL (defaults to config)
        """
        self.client = Client(model=model, server=server)
        self.messages: list[dict] = []
        self.custom_personality: dict[str, str] = {}

        logger.info(f"Agent initialized with model: {self.client.model}")

    def get_base_prompts(self) -> dict[str, str]:
        """Read all prompt files from prompting/ directory

        Returns:
            Dict mapping filenames to their contents
            Example: {'SOUL.md': '# SOUL.md...', 'MEMORY.md': '...'}
        """
        prompts = {}
        prompting_dir = Path(__file__).parent / "prompting"

        if not prompting_dir.exists():
            logger.warning(f"Prompting directory not found: {prompting_dir}")
            return prompts

        # Read all .md files in prompting/
        for file_path in prompting_dir.glob("*.md"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                prompts[file_path.name] = content
                logger.debug(f"Loaded prompt file: {file_path.name}")
            except Exception as e:
                logger.error(f"Failed to read {file_path.name}: {e}")

        logger.info(f"Loaded {len(prompts)} prompt files: {list(prompts.keys())}")
        return prompts
