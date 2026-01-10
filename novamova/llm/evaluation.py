import logging
import json
import asyncio
import torch

from bert_score import BERTScorer
from .features import translate

EXAMPLES = """
{"translation": [{"phrase_source": "Ми", "phrase_translated": "We"}, {"phrase_source": "повинні", "phrase_translated": "must"}, {"phrase_source": "закінчити", "phrase_translated": "finish"}, {"phrase_source": "цей", "phrase_translated": "this"}, {"phrase_source": "проект", "phrase_translated": "project"}, {"phrase_source": "до", "phrase_translated": "by"}, {"phrase_source": "п'ятниці", "phrase_translated": "Friday"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Він", "phrase_translated": "He"}, {"phrase_source": "вивчає", "phrase_translated": "has been studying"}, {"phrase_source": "китайську", "phrase_translated": "Chinese"}, {"phrase_source": "мову", "phrase_translated": "language"}, {"phrase_source": "вже", "phrase_translated": "for"}, {"phrase_source": "три", "phrase_translated": "three"}, {"phrase_source": "роки", "phrase_translated": "years"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Чи", "phrase_translated": "Can"}, {"phrase_source": "можете", "phrase_translated": "you"}, {"phrase_source": "ви", "phrase_translated": ""}, {"phrase_source": "допомогти", "phrase_translated": "help"}, {"phrase_source": "мені", "phrase_translated": "me"}, {"phrase_source": "з", "phrase_translated": "with"}, {"phrase_source": "цим", "phrase_translated": "this"}, {"phrase_source": "завданням", "phrase_translated": "task"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Вони", "phrase_translated": "They"}, {"phrase_source": "переїхали", "phrase_translated": "moved"}, {"phrase_source": "до", "phrase_translated": "to"}, {"phrase_source": "нового", "phrase_translated": "a new"}, {"phrase_source": "будинку", "phrase_translated": "house"}, {"phrase_source": "минулого", "phrase_translated": "last"}, {"phrase_source": "місяця", "phrase_translated": "month"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Моя", "phrase_translated": "My"}, {"phrase_source": "сестра", "phrase_translated": "sister"}, {"phrase_source": "працює", "phrase_translated": "works"}, {"phrase_source": "в", "phrase_translated": "at"}, {"phrase_source": "міжнародній", "phrase_translated": "an international"}, {"phrase_source": "компанії", "phrase_translated": "company"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Ці", "phrase_translated": "These"}, {"phrase_source": "квіти", "phrase_translated": "flowers"}, {"phrase_source": "потребують", "phrase_translated": "need"}, {"phrase_source": "багато", "phrase_translated": "a lot of"}, {"phrase_source": "сонячного", "phrase_translated": "sunlight"}, {"phrase_source": "світла", "phrase_translated": ""}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Він", "phrase_translated": "He"}, {"phrase_source": "зателефонував", "phrase_translated": "called"}, {"phrase_source": "мені", "phrase_translated": "me"}, {"phrase_source": "вчора", "phrase_translated": "yesterday"}, {"phrase_source": "ввечері", "phrase_translated": "evening"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Ми", "phrase_translated": "We"}, {"phrase_source": "збираємося", "phrase_translated": "are going"}, {"phrase_source": "відвідати", "phrase_translated": "to visit"}, {"phrase_source": "музей", "phrase_translated": "the museum"}, {"phrase_source": "наступного", "phrase_translated": "next"}, {"phrase_source": "тижня", "phrase_translated": "week"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Вона", "phrase_translated": "She"}, {"phrase_source": "забула", "phrase_translated": "forgot"}, {"phrase_source": "взяти", "phrase_translated": "to take"}, {"phrase_source": "парасольку", "phrase_translated": "an umbrella"}, {"phrase_source": "і", "phrase_translated": "and"}, {"phrase_source": "промокла", "phrase_translated": "got wet"}, {"phrase_source": "під", "phrase_translated": "in"}, {"phrase_source": "дощем", "phrase_translated": "the rain"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Діти", "phrase_translated": "The children"}, {"phrase_source": "граються", "phrase_translated": "have been playing"}, {"phrase_source": "в", "phrase_translated": "in"}, {"phrase_source": "саду", "phrase_translated": "the garden"}, {"phrase_source": "з", "phrase_translated": "since"}, {"phrase_source": "ранку", "phrase_translated": "morning"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Я", "phrase_translated": "I"}, {"phrase_source": "ніколи", "phrase_translated": "have never"}, {"phrase_source": "не", "phrase_translated": ""}, {"phrase_source": "був", "phrase_translated": "been"}, {"phrase_source": "у", "phrase_translated": "to"}, {"phrase_source": "Японії", "phrase_translated": "Japan"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Вони", "phrase_translated": "They"}, {"phrase_source": "обговорювали", "phrase_translated": "were discussing"}, {"phrase_source": "важливі", "phrase_translated": "important"}, {"phrase_source": "питання", "phrase_translated": "issues"}, {"phrase_source": "протягом", "phrase_translated": "for"}, {"phrase_source": "двох", "phrase_translated": "two"}, {"phrase_source": "годин", "phrase_translated": "hours"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Чи", "phrase_translated": "Do"}, {"phrase_source": "знаєш", "phrase_translated": "you"}, {"phrase_source": "ти", "phrase_translated": ""}, {"phrase_source": "де", "phrase_translated": "where"}, {"phrase_source": "знаходиться", "phrase_translated": "is located"}, {"phrase_source": "найближча", "phrase_translated": "the nearest"}, {"phrase_source": "аптека", "phrase_translated": "pharmacy"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Моїй", "phrase_translated": "My"}, {"phrase_source": "бабусі", "phrase_translated": "grandmother"}, {"phrase_source": "вісімдесят", "phrase_translated": "eighty"}, {"phrase_source": "п'ять", "phrase_translated": "five"}, {"phrase_source": "років", "phrase_translated": "years old"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Якби", "phrase_translated": "If"}, {"phrase_source": "я", "phrase_translated": "I"}, {"phrase_source": "мав", "phrase_translated": "had"}, {"phrase_source": "більше", "phrase_translated": "more"}, {"phrase_source": "часу", "phrase_translated": "time"}, {"phrase_source": "я", "phrase_translated": "I"}, {"phrase_source": "б", "phrase_translated": "would"}, {"phrase_source": "навчився", "phrase_translated": "learn"}, {"phrase_source": "грати", "phrase_translated": "to play"}, {"phrase_source": "на", "phrase_translated": "the"}, {"phrase_source": "гітарі", "phrase_translated": "guitar"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Вона", "phrase_translated": "She"}, {"phrase_source": "завжди", "phrase_translated": "has always"}, {"phrase_source": "мріяла", "phrase_translated": "dreamed"}, {"phrase_source": "стати", "phrase_translated": "of becoming"}, {"phrase_source": "відомою", "phrase_translated": "a famous"}, {"phrase_source": "письменницею", "phrase_translated": "writer"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Студенти", "phrase_translated": "Students"}, {"phrase_source": "здають", "phrase_translated": "take"}, {"phrase_source": "іспити", "phrase_translated": "exams"}, {"phrase_source": "в", "phrase_translated": "at"}, {"phrase_source": "кінці", "phrase_translated": "the end"}, {"phrase_source": "семестру", "phrase_translated": "of the semester"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Ми", "phrase_translated": "We"}, {"phrase_source": "не", "phrase_translated": "have not"}, {"phrase_source": "бачилися", "phrase_translated": "seen"}, {"phrase_source": "з", "phrase_translated": "my"}, {"phrase_source": "моїми", "phrase_translated": ""}, {"phrase_source": "двоюрідними", "phrase_translated": "cousins"}, {"phrase_source": "братами", "phrase_translated": ""}, {"phrase_source": "більше", "phrase_translated": "for more than"}, {"phrase_source": "року", "phrase_translated": "a year"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Якщо", "phrase_translated": "If"}, {"phrase_source": "завтра", "phrase_translated": "tomorrow"}, {"phrase_source": "буде", "phrase_translated": "is"}, {"phrase_source": "гарна", "phrase_translated": "nice"}, {"phrase_source": "погода", "phrase_translated": "the weather"}, {"phrase_source": "ми", "phrase_translated": "we"}, {"phrase_source": "підемо", "phrase_translated": "will go"}, {"phrase_source": "на", "phrase_translated": "on"}, {"phrase_source": "пікнік", "phrase_translated": "a picnic"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Мій", "phrase_translated": "My"}, {"phrase_source": "батько", "phrase_translated": "father"}, {"phrase_source": "ремонтує", "phrase_translated": "is repairing"}, {"phrase_source": "машину", "phrase_translated": "the car"}, {"phrase_source": "в", "phrase_translated": "in"}, {"phrase_source": "гаражі", "phrase_translated": "the garage"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Вони", "phrase_translated": "They"}, {"phrase_source": "вже", "phrase_translated": "have already"}, {"phrase_source": "закінчили", "phrase_translated": "finished"}, {"phrase_source": "читати", "phrase_translated": "reading"}, {"phrase_source": "ту", "phrase_translated": "that"}, {"phrase_source": "книгу", "phrase_translated": "book"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Я", "phrase_translated": "I"}, {"phrase_source": "повинен", "phrase_translated": "must"}, {"phrase_source": "піти", "phrase_translated": "go"}, {"phrase_source": "до", "phrase_translated": "to"}, {"phrase_source": "лікаря", "phrase_translated": "the doctor"}, {"phrase_source": "наступного", "phrase_translated": "next"}, {"phrase_source": "вівторка", "phrase_translated": "Tuesday"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Чому", "phrase_translated": "Why"}, {"phrase_source": "ти", "phrase_translated": "you"}, {"phrase_source": "не", "phrase_translated": "did not"}, {"phrase_source": "відповів", "phrase_translated": "reply"}, {"phrase_source": "на", "phrase_translated": "to"}, {"phrase_source": "моє", "phrase_translated": "my"}, {"phrase_source": "повідомлення", "phrase_translated": "message"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Ця", "phrase_translated": "This"}, {"phrase_source": "вулиця", "phrase_translated": "street"}, {"phrase_source": "веде", "phrase_translated": "leads"}, {"phrase_source": "прямо", "phrase_translated": "directly"}, {"phrase_source": "до", "phrase_translated": "to"}, {"phrase_source": "центральної", "phrase_translated": "the central"}, {"phrase_source": "площі", "phrase_translated": "square"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Вона", "phrase_translated": "She"}, {"phrase_source": "готує", "phrase_translated": "cooks"}, {"phrase_source": "дуже", "phrase_translated": "very"}, {"phrase_source": "смачні", "phrase_translated": "delicious"}, {"phrase_source": "страви", "phrase_translated": "dishes"}, {"phrase_source": "італійської", "phrase_translated": "Italian"}, {"phrase_source": "кухні", "phrase_translated": "cuisine"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Мені", "phrase_translated": "I"}, {"phrase_source": "потрібно", "phrase_translated": "need"}, {"phrase_source": "купити", "phrase_translated": "to buy"}, {"phrase_source": "нові", "phrase_translated": "new"}, {"phrase_source": "туфлі", "phrase_translated": "shoes"}, {"phrase_source": "для", "phrase_translated": "for"}, {"phrase_source": "весілля", "phrase_translated": "the wedding"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Він", "phrase_translated": "He"}, {"phrase_source": "працював", "phrase_translated": "worked"}, {"phrase_source": "над", "phrase_translated": "on"}, {"phrase_source": "дисертацією", "phrase_translated": "his dissertation"}, {"phrase_source": "протягом", "phrase_translated": "for"}, {"phrase_source": "трьох", "phrase_translated": "three"}, {"phrase_source": "років", "phrase_translated": "years"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Чи", "phrase_translated": "Could"}, {"phrase_source": "могли", "phrase_translated": "you"}, {"phrase_source": "б", "phrase_translated": ""}, {"phrase_source": "ви", "phrase_translated": ""}, {"phrase_source": "говорити", "phrase_translated": "speak"}, {"phrase_source": "трохи", "phrase_translated": "a little"}, {"phrase_source": "повільніше", "phrase_translated": "slower"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Ми", "phrase_translated": "We"}, {"phrase_source": "зустрілися", "phrase_translated": "met"}, {"phrase_source": "випадково", "phrase_translated": "accidentally"}, {"phrase_source": "в", "phrase_translated": "in"}, {"phrase_source": "кафе", "phrase_translated": "a cafe"}, {"phrase_source": "на", "phrase_translated": "on"}, {"phrase_source": "розі", "phrase_translated": "the"}, {"phrase_source": "вулиці", "phrase_translated": "street corner"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Її", "phrase_translated": "Her"}, {"phrase_source": "молодший", "phrase_translated": "younger"}, {"phrase_source": "брат", "phrase_translated": "brother"}, {"phrase_source": "захоплюється", "phrase_translated": "is passionate"}, {"phrase_source": "футболом", "phrase_translated": "about football"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Температура", "phrase_translated": "The temperature"}, {"phrase_source": "опустилася", "phrase_translated": "dropped"}, {"phrase_source": "нижче", "phrase_translated": "below"}, {"phrase_source": "нуля", "phrase_translated": "zero"}, {"phrase_source": "минулої", "phrase_translated": "last"}, {"phrase_source": "ночі", "phrase_translated": "night"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Вони", "phrase_translated": "They"}, {"phrase_source": "планують", "phrase_translated": "plan"}, {"phrase_source": "відкрити", "phrase_translated": "to open"}, {"phrase_source": "власний", "phrase_translated": "their own"}, {"phrase_source": "ресторан", "phrase_translated": "restaurant"}, {"phrase_source": "наступного", "phrase_translated": "next"}, {"phrase_source": "року", "phrase_translated": "year"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Я", "phrase_translated": "I"}, {"phrase_source": "не", "phrase_translated": "cannot"}, {"phrase_source": "можу", "phrase_translated": ""}, {"phrase_source": "знайти", "phrase_translated": "find"}, {"phrase_source": "свої", "phrase_translated": "my"}, {"phrase_source": "окуляри", "phrase_translated": "glasses"}, {"phrase_source": "ніде", "phrase_translated": "anywhere"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Ця", "phrase_translated": "This"}, {"phrase_source": "стара", "phrase_translated": "old"}, {"phrase_source": "церква", "phrase_translated": "church"}, {"phrase_source": "була", "phrase_translated": "was"}, {"phrase_source": "побудована", "phrase_translated": "built"}, {"phrase_source": "в", "phrase_translated": "in"}, {"phrase_source": "дванадцятому", "phrase_translated": "the twelfth"}, {"phrase_source": "столітті", "phrase_translated": "century"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Якби", "phrase_translated": "If"}, {"phrase_source": "вона", "phrase_translated": "she"}, {"phrase_source": "знала", "phrase_translated": "had known"}, {"phrase_source": "правду", "phrase_translated": "the truth"}, {"phrase_source": "вона", "phrase_translated": "she"}, {"phrase_source": "б", "phrase_translated": "would not"}, {"phrase_source": "не", "phrase_translated": ""}, {"phrase_source": "вчинила", "phrase_translated": "have acted"}, {"phrase_source": "так", "phrase_translated": "like that"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Мій", "phrase_translated": "My"}, {"phrase_source": "дідусь", "phrase_translated": "grandfather"}, {"phrase_source": "розповідав", "phrase_translated": "told"}, {"phrase_source": "цікаві", "phrase_translated": "interesting"}, {"phrase_source": "історії", "phrase_translated": "stories"}, {"phrase_source": "зі", "phrase_translated": "from"}, {"phrase_source": "своєї", "phrase_translated": "his"}, {"phrase_source": "молодості", "phrase_translated": "youth"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Поїзд", "phrase_translated": "The train"}, {"phrase_source": "відправляється", "phrase_translated": "departs"}, {"phrase_source": "о", "phrase_translated": "at"}, {"phrase_source": "восьмій", "phrase_translated": "eight"}, {"phrase_source": "годині", "phrase_translated": "o'clock"}, {"phrase_source": "ранку", "phrase_translated": "in the morning"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Вона", "phrase_translated": "She"}, {"phrase_source": "носить", "phrase_translated": "is wearing"}, {"phrase_source": "червону", "phrase_translated": "a red"}, {"phrase_source": "сукню", "phrase_translated": "dress"}, {"phrase_source": "на", "phrase_translated": "at"}, {"phrase_source": "вечірці", "phrase_translated": "the party"}]}
"""


torch._logging.set_logs(all=logging.CRITICAL)
logging.basicConfig(
    filename="j.log",
    level="INFO",
    datefmt="%d/%m/%Y %H:%M",
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)

json_examples = [
    json.loads(e.strip()) for e in EXAMPLES.split("NEXT EXAMPLE") if e.strip()
]

text_examples = []
text_questions = []

for ex in json_examples:
    full_translation = " ".join([p["phrase_translated"] for p in ex["translation"]])
    full_reference = " ".join([p["phrase_source"] for p in ex["translation"]])
    text_examples.append(full_translation)
    text_questions.append(full_reference)


def bert_evaluate(refs, candidates, lang="en"):
    """
    Evaluate candidate texts against reference texts using BERTScore.

    Args:
        refs (list of str): List of reference texts.
        candidates (list of str): List of candidate texts to evaluate.
        lang (str): Language code for BERTScore model selection.

    Returns:
        list of float: BERTScore F1 scores for each candidate-reference pair.
    """
    scorer = BERTScorer(lang=lang, rescale_with_baseline=True)
    P, R, F1 = scorer.score(candidates, refs)

    return F1.tolist()


async def ask_llm(
    questions: list[str] = text_questions, raw_results=False
) -> list[str]:
    """
    Generate LLM answers to questions
    """

    predicitons = []

    for q in questions:
        answer_obj = (
            await translate(q, source_lang="ukrainian", target_lang="english")
        )[0]
        answer = " ".join([p.phrase_translated for p in answer_obj.translation])

        if raw_results:
            predicitons.append(answer_obj)
        else:
            predicitons.append(answer)

    return predicitons


async def test_llm(
    questions: list[str] = text_questions,
    references: list[str] = text_examples,
    raw_results=False,
) -> None:
    predictions = await ask_llm(questions, raw_results=raw_results)
    if raw_results:
        predictions = [str(i) for i in predictions]
    evaluation = bert_evaluate(references, predictions)
    for i, e in enumerate(evaluation):
        print(f"{questions[i]} | {e}")
    logger.info(f"BERTEVALUATION\t{sum(evaluation) / len(evaluation)}")


asyncio.run(test_llm(text_questions, EXAMPLES.split("NEXT EXAMPLE"), raw_results=True))
