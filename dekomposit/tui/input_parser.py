from dataclasses import dataclass

from dekomposit.tui.models import LanguagePair, SUPPORTED_LANGUAGES


SUPPORTED_PAIR_COMMANDS: frozenset[str] = frozenset(
    f"{source}{target}"
    for source in SUPPORTED_LANGUAGES
    for target in SUPPORTED_LANGUAGES
    if source != target
)


@dataclass(slots=True)
class ParsedInput:
    text: str | None
    pair: LanguagePair | None = None
    error: str | None = None


def parse_input(raw_text: str) -> ParsedInput:
    stripped = raw_text.strip()
    if not stripped:
        return ParsedInput(text=None)

    if not stripped.startswith("/"):
        return ParsedInput(text=stripped)

    command_token, _, remainder = stripped.partition(" ")
    command = command_token[1:].lower()

    if command in SUPPORTED_PAIR_COMMANDS:
        pair = LanguagePair(source_lang=command[:2], target_lang=command[2:])
        message_text = remainder.strip() or None
        return ParsedInput(text=message_text, pair=pair)

    if len(command) == 4 and command.isalpha():
        source_lang = command[:2]
        target_lang = command[2:]
        if source_lang == target_lang:
            return ParsedInput(
                text=None,
                error="Source and target language cannot be the same.",
            )

        return ParsedInput(
            text=None,
            error=(
                f"Unsupported language pair '/{command}'. "
                f"Supported languages: {', '.join(SUPPORTED_LANGUAGES)}."
            ),
        )

    return ParsedInput(
        text=None,
        error=f"Unknown command '{command_token}'. Use /enru style commands.",
    )
