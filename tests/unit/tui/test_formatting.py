import pytest

from dekomposit.tui.formatting import parse_assistant_text
from dekomposit.tui.models import MessageKind


@pytest.mark.unit
def test_parse_translated_tag() -> None:
    parsed = parse_assistant_text("<translated>Привет</translated>")

    assert parsed.kind == MessageKind.TRANSLATED
    assert parsed.text == "Привет"


@pytest.mark.unit
def test_parse_translation_alias_tag() -> None:
    parsed = parse_assistant_text("<translation>Ahoj</translation>")

    assert parsed.kind == MessageKind.TRANSLATED
    assert parsed.text == "Ahoj"


@pytest.mark.unit
def test_extracts_embedded_translation_tag() -> None:
    parsed = parse_assistant_text(
        "Here is result: <translated>Как это сделать?</translated>",
        default_kind=MessageKind.PLAIN,
    )

    assert parsed.kind == MessageKind.TRANSLATED
    assert parsed.text == "Как это сделать?"


@pytest.mark.unit
def test_keeps_plain_text_when_no_tags_found() -> None:
    parsed = parse_assistant_text("Just a normal reply")

    assert parsed.kind == MessageKind.PLAIN
    assert parsed.text == "Just a normal reply"
