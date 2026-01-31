import itertools
from textwrap import dedent

from dekomposit.config import (
    SECTION_PLACEHOLDER,
    TRANSLATION_TAG_END,
    TRANSLATION_TAG_START,
)
from dekomposit.llm.types import Language, Translation

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
                "Incorrect language. See all supported languages in dekomposit.llm.types.Language enum class"
            )
        self.source_lang = source_lang
        self.target_lang = target_lang

        self._instruction_prompt = dedent(f"""\
            1. Translate between {self.source_lang} ↔ {self.target_lang}. Auto-detect direction.
               Keep the translation natural, correct, and accurate as much as possible.
               Preserve the tone, mood, and intent.

            2. Mixed languages → translate to {self.target_lang}.
               (e.g. Привет world -> Hello world [source_lang: russian, target_lang: english])

            3. Errors (grammar/spelling/punctuation) → correct in output.

            4. Correct the punctuation and the sentence if needed so that it would be natural.
               Special characters → delete them.
               Links, names, technical jargon → keep them original.

            5. Untranslatable nonsense → keep the output empty.

            ### Examples of correct rules observation:

            1. Consider the following "hello" and translate it into russian, Gemini
               [source_lang: english, target_lang: ukrainian]
               Correct answer: The translation of the whole input including the content
               in quotes or etc... into target_lang: ukrainian
               (Розгляньте наступне "Привіт" і перекладіть його російською, Gemini)

               One more example: Translate this into russian
               (Переклади це на російську)

               One more example: Ahoj, prelož to na angličtinu
               (Привіт, переклади це на англійську)

            2. Привет мир, how are ю? [source_lang: russian, target_lang: ukrainian]
               Correct answer: The translation of the input in english only
               (Привіт світ, як справи?)

            3, 4. Прив как дела чо делаеш шо за прИДллажение Я НИ понЭЛ
               [source_lang: russian, target_lang: english]
               Correct answer: The translation of the corrected input
               (Hey, how are you doing? What are you doing? What's the deal? I don't get it at all!)

            5. Почему мой AutoParser Xd13 не работает на ts? Ведь в документации все работает - https://example.org/something
               [source_lang: russian, target_lang: slovak]
               Correct answer: Keep tech jargon, names, links while translating
               (Prečo môj AutoParser Xd13 nefunguje na ts? Veď v dokumentácii všetko funguje - https://example.org/something)

            6. 43994fd (Answer - ""), [](*&@H() (Answer - ""), link.com/hithere (Answer - ""), listasalistlolbrohow (Answer - "")
        """)

        self._system_prompt = dedent(f"""\
            You are a dedicated {self.source_lang}-{self.target_lang} / {self.target_lang}-{self.source_lang} translator.
            Your task is defined by this singular function.
        """)
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
        return dedent(f"""\
            {self.instructions}

            Examples

            {self.examples}
            USER INPUT: {user_input}
            ASSISTANT:
        """)
