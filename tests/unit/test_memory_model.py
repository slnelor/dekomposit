import pytest

from dekomposit.llm.memory import UserMemory


@pytest.mark.unit
def test_user_memory_add_note_deduplicates_case_insensitive() -> None:
    memory = UserMemory()

    memory.add_note("Likes movies")
    memory.add_note("likes movies")

    assert memory.notes == ["Likes movies"]


@pytest.mark.unit
def test_user_memory_remove_note_returns_true_when_found() -> None:
    memory = UserMemory()
    memory.add_note("Prefers short responses")

    removed = memory.remove_note("prefers short responses")

    assert removed is True
    assert memory.notes == []


@pytest.mark.unit
def test_user_memory_history_keeps_last_50_messages() -> None:
    memory = UserMemory()

    for i in range(60):
        memory.add_message("user", f"m{i}")

    assert len(memory.conversation_history) == 50
    assert memory.conversation_history[0]["content"] == "m10"
    assert memory.conversation_history[-1]["content"] == "m59"
