import pytest

from dekomposit.llm.tools.base import BaseTool
from dekomposit.llm.tools.registry import ToolRegistry


class DummyTool(BaseTool):
    def __init__(self) -> None:
        super().__init__(name="dummy_tool", description="Dummy test tool")

    async def __call__(self, **kwargs):
        return {"ok": True, **kwargs}


@pytest.mark.unit
def test_registry_auto_discovers_core_tools() -> None:
    registry = ToolRegistry(auto_discover=True)

    assert registry.has("adaptive_translation")
    assert registry.has("detect_language")
    assert registry.has("memory")
    assert registry.has("reverso_api")


@pytest.mark.unit
def test_registry_get_supports_factory_key_and_tool_name() -> None:
    registry = ToolRegistry(auto_discover=False)
    registry.register_factory("dummyfactory", DummyTool)

    by_key = registry.get("dummyfactory")
    by_name = registry.get("dummy_tool")

    assert by_key is not None
    assert by_name is not None
    assert by_key.name == "dummy_tool"
    assert by_name.name == "dummy_tool"


@pytest.mark.unit
def test_registry_produces_openai_tool_schemas() -> None:
    registry = ToolRegistry(auto_discover=False)
    registry.register(DummyTool())

    schemas = registry.get_tool_schemas()

    assert len(schemas) == 1
    assert schemas[0]["type"] == "function"
    function_schema = schemas[0]["function"]
    assert function_schema["name"] == "dummy_tool"
    assert "description" in function_schema
    assert "parameters" in function_schema


@pytest.mark.unit
def test_registry_excludes_disabled_tools_from_schema() -> None:
    registry = ToolRegistry(auto_discover=True)

    schema_names = [item["function"]["name"] for item in registry.get_tool_schemas()]

    assert "reverso_api" not in schema_names
