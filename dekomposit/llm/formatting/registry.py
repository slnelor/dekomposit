import json
import logging
from pathlib import Path
from typing import Any

from dekomposit.llm.formatting.models import FormatPreset


logging.basicConfig(
    datefmt="%d/%m/%Y %H:%M",
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class FormatRegistry:
    """Read-only registry for format presets.
    
    Loads presets from JSON file and provides access methods.
    """

    DEFAULT_FILE = Path(__file__).parent / "default.json"

    def __init__(self, file_path: str | None = None) -> None:
        """Initialize registry by loading presets from file.
        
        Args:
            file_path: Path to JSON file. Defaults to default.json in same directory.
        """
        self._presets: dict[str, FormatPreset] = {}
        self._active: str = "translation_default"
        
        path = Path(file_path) if file_path else self.DEFAULT_FILE
        self._load_from_file(path)

    def _load_from_file(self, path: Path) -> None:
        """Load presets from JSON file."""
        if not path.exists():
            logger.warning(f"Format presets file not found: {path}")
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._active = data.get("active", "translation_default")
            
            presets_data = data.get("presets", {})
            for name, preset_data in presets_data.items():
                try:
                    self._presets[name] = FormatPreset(**preset_data)
                except Exception as e:
                    logger.error(f"Failed to load preset '{name}': {e}")

            logger.info(f"Loaded {len(self._presets)} format presets")
            
        except Exception as e:
            logger.error(f"Failed to load format presets from {path}: {e}")

    def get_active(self) -> FormatPreset:
        """Get the currently active preset.
        
        Returns:
            The active FormatPreset
            
        Raises:
            ValueError: If active preset not found
        """
        preset = self._presets.get(self._active)
        if preset is None:
            raise ValueError(f"Active preset '{self._active}' not found")
        return preset

    def get(self, name: str) -> FormatPreset | None:
        """Get a preset by name.
        
        Args:
            name: Preset name
            
        Returns:
            FormatPreset or None if not found
        """
        return self._presets.get(name)

    def list_all(self) -> list[FormatPreset]:
        """List all available presets.
        
        Returns:
            List of all FormatPreset objects
        """
        return list(self._presets.values())

    def list_names(self) -> list[str]:
        """List all preset names.
        
        Returns:
            List of preset names
        """
        return sorted(self._presets.keys())

    def render(self, preset_name: str | None = None, **kwargs: Any) -> str:
        """Render a preset with given variables.
        
        Args:
            preset_name: Name of preset to use. If None, uses active preset.
            **kwargs: Variables to fill in template
            
        Returns:
            Formatted string with tags
        """
        if preset_name:
            preset = self.get(preset_name)
            if preset is None:
                logger.warning(f"Preset '{preset_name}' not found, using active")
                preset = self.get_active()
        else:
            preset = self.get_active()
            
        return preset.render(**kwargs)
