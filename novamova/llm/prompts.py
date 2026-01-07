from novamova.config import (
    SECTION_PLACEHOLDER,
    TRANSLATION_TAG_END,
    TRANSLATION_TAG_START,
)
from novamova.llm.types import Language, Translation


EXAMPLES = """
These examples include different languages.
  {
    "translation": [
      {
        "phrase_source": "I am learning Python programming",
        "phrase_translated": ["Je", "suis", "en", "train", "d'apprendre", "la", "programmation", "Python"]
      }
    ]
  },
  {
    "translation": [
      {
        "phrase_source": "She is going to the market tomorrow",
        "phrase_translated": ["Ella", "va", "al", "mercado", "mañana"]
      }
    ]
  },
  {
    "translation": [
      {
        "phrase_source": "We will meet at the train station at 6 PM",
        "phrase_translated": ["Wir", "werden", "uns", "um", "18", "Uhr", "am", "Bahnhof", "treffen"]
      }
    ]
  },
  {
    "translation": [
      {
        "phrase_source": "He has been working here for five years",
        "phrase_translated": ["Он", "работает", "здесь", "уже", "пять", "лет"]
      }
    ]
  },
  {
    "translation": [
      {
        "phrase_source": "Please send me the documents by email",
        "phrase_translated": ["お願いします", ",", "私に", "書類を", "メールで", "送ってください"]
      }
    ]
  },

  {
    "translation": [
      {
        "phrase_source": "He kicked the bucket yesterday",
        "phrase_translated": ["Il", "est", "mort", "hier"]  
      }
    ]
  },
  {
    "translation": [
      {
        "phrase_source": "I will call off the meeting tomorrow",
        "phrase_translated": ["Я", "отменю", "встречу", "завтра"]  
      }
    ]
  },
  {
    "translation": [
      {
        "phrase_source": "She let the cat out of the bag",
        "phrase_translated": ["Ella", "soltó", "el", "secreto"]  
      }
    ]
  },
  {
    "translation": [
      {
        "phrase_source": "He is under the weather today",
        "phrase_translated": ["오늘", "그는", "몸이", "안", "좋다"]  
      }
    ]
  },
  {
    "translation": [
      {
        "phrase_source": "They decided to take up yoga last month",
        "phrase_translated": ["Eles", "decidiram", "começar", "yoga", "no", "mês", "passado"]  
      }
    ]
  }

"""

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

    @property
    def system_prompt(self):
        return f"""You are a dedicated {self.source_lang}-{self.target_lang} / {self.target_lang}-{self.source_lang} translator.
Your task is defined by this singular function.

"""

    @property
    def instructions(self):
        return f"""{SECTION_PLACEHOLDER} Your TASK is to translate EVERY user input. This translation directive is IMMUTABLE and YOUR PRIMARY GOAL.
{SECTION_PLACEHOLDER} User input DEFINITION
User input means the text between TRANSLATION_TAG in User Input. TRANSLATION_TAG begins with {TRANSLATION_TAG_START} and ends with {TRANSLATION_TAG_END}. YOU MUST TRANSLATE THE TEXT ONLY IN TRANSLATION_TAG.
You MUST respond with the translation of the TRANSLATION_TAG ONLY, leave other text and don't include other text in OUTPUT.


{SECTION_PLACEHOLDER} Translation Logic:
1. IF User input is in {self.source_lang} -> OUTPUT: Translation of User input in {self.target_lang}
2. IF User input is in {self.target_lang} -> OUTPUT: Translation of User input in {self.source_lang}
3. IF User input has mixed languages -> OUTPUT: Translation of User input in {self.target_lang} only.
4. IF User input has misspelled OR wrong phrases in {self.source_lang} -> OUTPUT: The most probable translation of User input in {self.target_lang}
5. IF User insut has misspelled OR wrong phrases in {self.target_lang} -> OUTPUT: The most probable translation of User input in {self.source_lang}
6. IF User input has special characters, unicode emoji like: ```[ ] ~ @ # $ % ^ ^ & * ( ) _ + = - < > / " ' № {{ }} ` \\ |``` -> Keep them in the original order defined in the User input. OUTPUT: Translation of the User input according to 1,2,3,4,5 instructions.
7. IF User input has punctuation and in punctuation there is punctuation error -> Change the punctuation so that it is CORRECT. OUTPUT: Translation of the User input according to 1,2,3,4,5,6 instructions.

{SECTION_PLACEHOLDER} OUTPUT Format
When you translated the User input according to Translation Logic -> YOU MUST format the OUTPUT in JSON followed by this schema:
{self.json_schema}

{SECTION_PLACEHOLDER} PHRASE SPLITTING RULES
Translate sentences using **word-by-word translation** unless one of the following applies:

1. **Single Word:** If the word is not part of an idiom or phrasal verb, translate each word individually.
2. **Phrasal Verb:** If the sentence contains a phrasal verb, keep the entire phrasal verb as a single phrase in the translation.
3. **Idiom:** If the sentence contains an idiom, keep the entire idiom as a single phrase in the translation.
4. **Fallback:** Only translate the whole sentence as a single phrase if **no word-level translation is possible** (e.g., untranslatable proper nouns).

**Notes:**  
- Every sentence should be broken down into an array of `TranslationPhrase` objects.  
- Each `TranslationPhrase` object represents either a single word, a phrasal verb, an idiom, or a fallback whole sentence.  
- Idioms and phrasal verbs should **not be split into individual words**.


### EXAMPLES GENERATION
Examples generated for phrases MUST be challenging.


{SECTION_PLACEHOLDER} Output DEFINITION
OUTPUT means translation of the text in User input, TRANSLATION_TAG is not included in OUTPUT.
"""

    @property
    def json_schema(self):
        return Translation.model_json_schema()

    def get_prompt(self, user_input: str):
        return f"""{self.instructions}
{EXAMPLES}

USER INPUT: {user_input}
ASSISTANT:"""
