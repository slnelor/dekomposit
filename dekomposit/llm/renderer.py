from typing import Any, Mapping

from dekomposit.llm.formatting import FormatRegistry


class AgentRenderer:
    """Render normalized agent results into chat output."""

    def __init__(
        self,
        formats: FormatRegistry,
        error_message: str = "Sorry, I couldn't process that.",
    ) -> None:
        self._formats = formats
        self._error_message = error_message
        self._handlers = {
            "response": self._render_response,
            "error": self._render_error,
        }

    def render(self, result: Mapping[str, Any]) -> str:
        formatted = self._try_render_format(result)
        if formatted is not None:
            return formatted

        result_type = str(result.get("type", "response"))
        handler = self._handlers.get(result_type, self._render_response)
        return handler(result)

    @staticmethod
    def _render_response(result: Mapping[str, Any]) -> str:
        return str(result.get("message", ""))

    def _render_error(self, result: Mapping[str, Any]) -> str:
        return str(result.get("message", self._error_message))

    def _try_render_format(self, result: Mapping[str, Any]) -> str | None:
        format_spec = result.get("format")
        if isinstance(format_spec, Mapping):
            preset = format_spec.get("preset")
            values = format_spec.get("values")
            if isinstance(values, Mapping):
                return self._formats.render(
                    str(preset) if preset else None, **dict(values)
                )

        preset = result.get("format_preset")
        values = result.get("format_values")
        if isinstance(values, Mapping):
            return self._formats.render(str(preset) if preset else None, **dict(values))

        return None
