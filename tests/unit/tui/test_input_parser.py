import pytest

from dekomposit.tui.input_parser import parse_input


@pytest.mark.unit
def test_parse_plain_text() -> None:
    parsed = parse_input("hello there")

    assert parsed.error is None
    assert parsed.pair is None
    assert parsed.text == "hello there"


@pytest.mark.unit
def test_parse_pair_command_only() -> None:
    parsed = parse_input("/enru")

    assert parsed.error is None
    assert parsed.pair is not None
    assert parsed.pair.label == "en-ru"
    assert parsed.text is None


@pytest.mark.unit
def test_parse_pair_command_with_message() -> None:
    parsed = parse_input("/RUEn  how to do it")

    assert parsed.error is None
    assert parsed.pair is not None
    assert parsed.pair.label == "ru-en"
    assert parsed.text == "how to do it"


@pytest.mark.unit
def test_rejects_same_language_pair() -> None:
    parsed = parse_input("/enen")

    assert parsed.text is None
    assert parsed.error is not None
    assert "cannot be the same" in parsed.error


@pytest.mark.unit
def test_rejects_unknown_command() -> None:
    parsed = parse_input("/help")

    assert parsed.text is None
    assert parsed.error is not None
    assert "Unsupported language pair" in parsed.error
