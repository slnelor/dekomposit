import os
from types import SimpleNamespace


def make_tool_call(
    name: str, arguments: str, call_id: str = "call_1"
) -> SimpleNamespace:
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(name=name, arguments=arguments),
    )


def make_chat_response(
    content: str | None,
    tool_calls: list[SimpleNamespace] | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=content,
                    tool_calls=tool_calls,
                )
            )
        ]
    )


def live_llm_available() -> bool:
    selected_key_name = os.getenv("CURRENT_API_KEY", "GEMINI_API_KEY")
    selected_key_value = os.getenv(selected_key_name)
    return bool(selected_key_value)
