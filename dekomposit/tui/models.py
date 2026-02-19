from dataclasses import dataclass
from enum import StrEnum


SUPPORTED_LANGUAGES: tuple[str, ...] = ("en", "ru", "uk", "sk")


class ChatMode(StrEnum):
    NORMAL = "normal"
    TRANSLATION = "translation"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageKind(StrEnum):
    PLAIN = "plain"
    TRANSLATED = "translated"
    ERROR = "error"
    INFO = "info"


@dataclass(frozen=True, slots=True)
class LanguagePair:
    source_lang: str = "en"
    target_lang: str = "ru"

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_lang", self.source_lang.lower().strip())
        object.__setattr__(self, "target_lang", self.target_lang.lower().strip())

    @property
    def label(self) -> str:
        return f"{self.source_lang}-{self.target_lang}"

    @property
    def command(self) -> str:
        return f"/{self.source_lang}{self.target_lang}"

    def swapped(self) -> "LanguagePair":
        return LanguagePair(
            source_lang=self.target_lang,
            target_lang=self.source_lang,
        )


@dataclass(slots=True)
class ChatMessage:
    role: MessageRole
    text: str
    kind: MessageKind = MessageKind.PLAIN
    pair_label: str | None = None
