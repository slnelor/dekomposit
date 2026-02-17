from pathlib import Path

import pytest

from dekomposit.llm.prompts import PromptRegistry


@pytest.mark.unit
def test_prompt_registry_discovers_markdown_files(tmp_path: Path) -> None:
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "routing.md").write_text("route prompt", encoding="utf-8")
    nested = prompts_dir / "sub"
    nested.mkdir()
    (nested / "detect.md").write_text("detect prompt", encoding="utf-8")
    (prompts_dir / "ignore.txt").write_text("nope", encoding="utf-8")

    registry = PromptRegistry(prompts_dir=prompts_dir)

    assert registry.has("routing")
    assert registry.has("sub.detect")
    assert registry.get("routing") == "route prompt"
    assert registry.get("sub.detect") == "detect prompt"
    assert "ignore" not in registry.list_all()


@pytest.mark.unit
def test_prompt_registry_missing_directory_is_safe(tmp_path: Path) -> None:
    missing_dir = tmp_path / "does_not_exist"

    registry = PromptRegistry(prompts_dir=missing_dir)

    assert registry.list_all() == []
    assert registry.get("routing") is None
