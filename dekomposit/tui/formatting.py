import re
from dataclasses import dataclass

from dekomposit.tui.models import MessageKind


_TRANSLATED_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"<translated>(?P<body>.*?)</translated>", re.IGNORECASE | re.DOTALL),
    re.compile(r"<translation>(?P<body>.*?)</translation>", re.IGNORECASE | re.DOTALL),
)


@dataclass(frozen=True, slots=True)
class ParsedAssistantText:
    text: str
    kind: MessageKind


def parse_assistant_text(
    text: str,
    default_kind: MessageKind = MessageKind.PLAIN,
) -> ParsedAssistantText:
    stripped = text.strip()
    if not stripped:
        return ParsedAssistantText(text="", kind=default_kind)

    for pattern in _TRANSLATED_PATTERNS:
        match = pattern.fullmatch(stripped)
        if match:
            body = match.group("body").strip()
            return ParsedAssistantText(text=body, kind=MessageKind.TRANSLATED)

    for pattern in _TRANSLATED_PATTERNS:
        match = pattern.search(stripped)
        if match:
            body = match.group("body").strip()
            return ParsedAssistantText(text=body, kind=MessageKind.TRANSLATED)

    return ParsedAssistantText(text=stripped, kind=default_kind)
