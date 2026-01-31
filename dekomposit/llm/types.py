from typing import List, NamedTuple
from enum import StrEnum
from pydantic import BaseModel, Field

from typing import List
from pydantic import BaseModel, Field


class TranslationPhrase(BaseModel):
    """A translation pair object (phrase_source, phrase_translated)"""

    phrase_source: str = Field(
        description="A natural phrase chunk 1+ words. Can be: a clause, idiom, phrasal verb, or semantic unit or word. Punctuation MUST be attached to the last word - NEVER create entries like '.', '—', '!' alone."
    )
    phrase_translated: str = Field(
        description="Translation of phrase_source maintaining natural phrase boundaries. Keep idioms together. Attach all punctuation to words."
    )


class PhraseDetailed(TranslationPhrase):
    """Details for the phrase like definition, examples, synonyms"""

    phrase_source_definitions: List[str] = Field(
        description="The definitions of the source phrase"
    )
    phrase_parts_of_speech: List[str] | None = Field(
        description="Optional. If phrase is one word or phrase can be part of speech -> All possible Parts of speech of the phrase. Written in Phrase Translated Language. Else None"
    )
    phrase_synonyms: List[str] = Field(
        description="Phrase synonyms in Phrase Source Language"
    )
    phrase_antonyms: List[str] = Field(
        description="Phrase antonyms in Phrase Source Language"
    )
    phrase_examples: List[str] = Field(
        description="Examples of sentences with phrase, written in Source Phrase Language"
    )


class Translation(BaseModel):
    """Translation object - decomposes text into natural phrase chunks (typically 1+ words)"""

    translation: List[TranslationPhrase] = Field(
        description="List of natural phrase pairs. Decompose into chunks or individual words. CRITICAL: Never create separate entries for standalone punctuation marks (., —, !, ?). Always attach punctuation to the preceding word."
    )


class Language(StrEnum):
    EN = "english"
    ES = "spanish"
    FR = "french"
    DE = "german"
    IT = "italian"
    PT = "portuguese"
    PL = "polish"
    UK = "ukrainian"
    SK = "slovak"
    RU = "russian"
    CS = "czech"
    ZH = "chinese"
    JA = "japanese"
