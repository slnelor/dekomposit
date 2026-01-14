import itertools

from novamova.config import (
    SECTION_PLACEHOLDER,
    TRANSLATION_TAG_END,
    TRANSLATION_TAG_START,
)
from novamova.llm.types import Language, Translation

EXAMPLE_ANNOTATIONS = [
    "natural phrases, punctuation attached",
    "idiom kept as complete unit",
    "phrasal verb as single phrase",
    "short sentence kept whole, errors corrected",
    "grammar corrected, natural chunking",
    "misspelling corrected, punctuation attached",
    "special chars with adjacent words",
    "untranslatable article omitted",
    "em-dash attached, natural phrase boundaries",
    "whole sentence - simple input",
    "wordplay/tongue-twister kept together",
]

EXAMPLES = [
    {
        "translation": [
            {"phrase_source": "I love", "phrase_translated": "J'aime"},
            {"phrase_source": "Paris.", "phrase_translated": "Paris."},
        ],
    },
    {
        "translation": [
            {"phrase_source": "He kicked the bucket", "phrase_translated": "Il est mort"},
            {"phrase_source": "yesterday.", "phrase_translated": "hier."},
        ],
    },
    {
        "translation": [
            {"phrase_source": "She gave up", "phrase_translated": "Elle a abandonné"},
            {"phrase_source": "smoking.", "phrase_translated": "la cigarette."},
        ],
    },
    {
        "translation": [
            {"phrase_source": "Hello, world!", "phrase_translated": "Bonjour, monde!"}
        ],
    },
    {
        "translation": [
            {"phrase_source": "He go to", "phrase_translated": "Il va à"},
            {"phrase_source": "school.", "phrase_translated": "l'école."},
        ],
    },
    {
        "translation": [
            {"phrase_source": "Helo!", "phrase_translated": "Bonjour!"},
        ],
    },
    {
        "translation": [
            {"phrase_source": "I love", "phrase_translated": "Me encanta"},
            {"phrase_source": "❤️ coding!", "phrase_translated": "❤️ programar!"},
        ],
    },
    {
        "translation": [
            {"phrase_source": "Please send", "phrase_translated": "お願いします送ってください"},
            {"phrase_source": "the documents", "phrase_translated": "書類を"},
        ],
    },
    {
        "translation": [
            {"phrase_source": "Time flies —", "phrase_translated": "Le temps passe vite —"},
            {"phrase_source": "says the proverb.", "phrase_translated": "dit le proverbe."},
        ],
    },
    {
        "translation": [
            {"phrase_source": "Break a leg!", "phrase_translated": "Ні пуху ні пера!"}
        ],
    },
    {
        "translation": [
            {"phrase_source": "She sells seashells by the seashore.", "phrase_translated": "Elle vend des coquillages au bord de la mer."}
        ],
    },
]

# NOT ALL LANGUAGES AVAILABLE YET


class TranslationPrompt:
    def __init__(self, source_lang: Language | str, target_lang: Language | str):
        source_lang = str(source_lang).lower()
        target_lang = str(target_lang).lower()
        if (source_lang not in Language) or (target_lang not in Language):
            raise ValueError(
                "Incorrect language. See all supported languages at afono.llm.types.language enum class"
            )

        self.source_lang = source_lang
        self.target_lang = target_lang
        self._instruction_prompt = (
            f"Translate between {self.source_lang} ↔ {self.target_lang}. Auto-detect direction.\n"
            f"Mixed languages → translate to {self.target_lang}.\n"
            f"Errors (grammar/spelling/punctuation) → correct in output.\n"
            f"Special characters → preserve position.\n\n"
        )
        self._system_prompt = (
            f"You are a dedicated {self.source_lang}-{self.target_lang}\n"
            f"/ {self.target_lang}-{self.source_lang} translator.\n"
            f"Your task is defined by this singular function."
        )
        self._examples = EXAMPLES
        self._example_annotations = EXAMPLE_ANNOTATIONS

    @property
    def system_prompt(self):
        return self._system_prompt

    @property
    def instructions(self):
        return self._instruction_prompt

    @staticmethod
    @property
    def json_schema(self):
        return Translation.model_json_schema()

    @staticmethod
    def parse_outputs(outputs: list[Translation]):
        """Parse outputs into tuples of sentences [(translated, source)]."""

        _translation_pairs = []
        for v in outputs:
            sentences = "", ""
            for i in v["translation"]:
                sentences = (
                    f"{sentences[0]} {i['phrase_translated']}".lstrip(),
                    f"{sentences[1]} {i['phrase_source']}".lstrip(),
                )
            _translation_pairs.append(sentences)

        return _translation_pairs

    @property
    def examples(self):
        items = itertools.zip_longest(self._examples, self._example_annotations)

        _ready_str = ""
        for ex, note in items:
            _ready_str = f"{_ready_str}Next example{' (' + note + ')' + '\n' if note else '\n'}{str(ex).strip()}\n\n"

        return _ready_str

    def get_prompt(self, user_input: str):
        return (
            f"{self.instructions}\n\n"
            f"Examples\n\n{self.examples}\n"
            f"USER INPUT: {user_input}\n"
            f"ASSISTANT:"
        )
