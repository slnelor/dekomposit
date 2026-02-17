import pytest

from dekomposit.llm.memory import UserMemory


@pytest.mark.unit
def test_user_memory_add_topic_deduplicates_case_insensitive() -> None:
    memory = UserMemory(user_id=100)

    memory.add_topic("Movies")
    memory.add_topic("movies")

    assert memory.topics == ["Movies"]


@pytest.mark.unit
def test_user_memory_add_mistake_promotes_learning_gap_at_threshold() -> None:
    memory = UserMemory(user_id=101)

    for _ in range(5):
        memory.add_mistake("verb_conjugation")

    assert memory.mistake_count["verb_conjugation"] == 5
    assert "verb_conjugation" in memory.learning_gaps


@pytest.mark.unit
def test_user_memory_history_keeps_last_50_messages() -> None:
    memory = UserMemory(user_id=102)

    for i in range(60):
        memory.add_message("user", f"m{i}")

    assert len(memory.conversation_history) == 50
    assert memory.conversation_history[0]["content"] == "m10"
    assert memory.conversation_history[-1]["content"] == "m59"
