import json
from pathlib import Path

import pytest

from dekomposit.llm.formatting.registry import FormatRegistry


@pytest.mark.unit
def test_format_registry_renders_active_default_preset() -> None:
    registry = FormatRegistry()

    rendered = registry.render(None, source="EN", target="RU", translation="Privet")

    assert rendered == "<translation>[EN → RU] Privet</translation>"


@pytest.mark.unit
def test_format_registry_falls_back_to_active_when_name_missing() -> None:
    registry = FormatRegistry()

    rendered = registry.render("missing", source="EN", target="SK", translation="Ahoj")

    assert rendered == "<translation>[EN → SK] Ahoj</translation>"


@pytest.mark.unit
def test_format_registry_raises_when_active_preset_missing(tmp_path: Path) -> None:
    broken = {
        "active": "missing_active",
        "presets": {
            "existing": {
                "name": "existing",
                "description": "x",
                "open_tag": "<x>",
                "close_tag": "</x>",
                "template": "{translation}",
                "metadata": {},
            }
        },
    }
    config_path = tmp_path / "formats.json"
    config_path.write_text(json.dumps(broken), encoding="utf-8")

    registry = FormatRegistry(file_path=str(config_path))

    with pytest.raises(ValueError, match="Active preset"):
        registry.get_active()
