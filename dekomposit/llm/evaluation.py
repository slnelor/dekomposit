import logging
import json
import asyncio
import torch

from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.dataset import EvaluationDataset
from deepeval import evaluate

from bert_score import BERTScorer
from .features import translate


EXAMPLES = """
{"translation": [{"phrase_source": "Він", "phrase_translated": "He"}, {"phrase_source": "на цьому собаку з'їв", "phrase_translated": "is an expert at this"}, {"phrase_source": ",", "phrase_translated": ","}, {"phrase_source": "але", "phrase_translated": "but"}, {"phrase_source": "сів у калюжу", "phrase_translated": "made a fool of himself"}, {"phrase_source": ".", "phrase_translated": "."}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Ру|ки", "phrase_translated": "Hands"}, {"phrase_source": "не", "phrase_translated": "don't"}, {"phrase_source": "доходять", "phrase_translated": "get around to"}, {"phrase_source": "подивитися", "phrase_translated": "watching"}, {"phrase_source": "цей", "phrase_translated": "this"}, {"phrase_source": "фільм", "phrase_translated": "film"}, {"phrase_source": "...", "phrase_translated": "..."}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Да", "phrase_translated": "Well"}, {"phrase_source": "нет", "phrase_translated": "no"}, {"phrase_source": ",", "phrase_translated": ","}, {"phrase_source": "наверное", "phrase_translated": "probably"}, {"phrase_source": ".", "phrase_translated": "."}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Прівет,світ", "phrase_translated": "Hello, world"}, {"phrase_source": "!", "phrase_translated": "!"}, {"phrase_source": "!", "phrase_translated": "!"}, {"phrase_source": "!", "phrase_translated": "!"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Косив", "phrase_translated": "Mowed"}, {"phrase_source": "косий", "phrase_translated": "cross-eyed"}, {"phrase_source": "косою", "phrase_translated": "with a scythe"}, {"phrase_source": "косо", "phrase_translated": "crookedly"}, {"phrase_source": ".", "phrase_translated": "."}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Я @ тебе ❤️ 4ever", "phrase_translated": "I @ you ❤️ 4ever"}, {"phrase_source": "!", "phrase_translated": "!"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "На злодієві шапка горить", "phrase_translated": "A guilty conscience needs no accuser"}, {"phrase_source": "—", "phrase_translated": "—"}, {"phrase_source": "каже", "phrase_translated": "says"}, {"phrase_source": "народна", "phrase_translated": "folk"}, {"phrase_source": "мудрість", "phrase_translated": "wisdom"}, {"phrase_source": ".", "phrase_translated": "."}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Він", "phrase_translated": "He"}, {"phrase_source": "купив", "phrase_translated": "bought"}, {"phrase_source": "лимон", "phrase_translated": "a lemon"}, {"phrase_source": "у", "phrase_translated": "from"}, {"phrase_source": "дилера", "phrase_translated": "the dealer"}, {"phrase_source": ".", "phrase_translated": "."}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Time", "phrase_translated": "Час"}, {"phrase_source": "flies", "phrase_translated": "летить"}, {"phrase_source": "like", "phrase_translated": "як"}, {"phrase_source": "an", "phrase_translated": ""}, {"phrase_source": "arrow", "phrase_translated": "стріла"}, {"phrase_source": ";", "phrase_translated": ";"}, {"phrase_source": "fruit flies", "phrase_translated": "мушки-дрозофіли"}, {"phrase_source": "like", "phrase_translated": "люблять"}, {"phrase_source": "a", "phrase_translated": ""}, {"phrase_source": "banana", "phrase_translated": "банан"}, {"phrase_source": ".", "phrase_translated": "."}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Ти", "phrase_translated": "You"}, {"phrase_source": "шо", "phrase_translated": "what"}, {"phrase_source": "тут", "phrase_translated": "here"}, {"phrase_source": "робиш", "phrase_translated": "doing"}, {"phrase_source": "???", "phrase_translated": "???"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Break a leg", "phrase_translated": "Ні пуху ні пера"}, {"phrase_source": "!", "phrase_translated": "!"}]}
NEXT EXAMPLE
{"translation": [{"phrase_source": "Він.іде" , "phrase_translated": "He goes"}, {"phrase_source": "до", "phrase_translated": "to"}, {"phrase_source": "школи,", "phrase_translated": "school,"}, {"phrase_source": "а", "phrase_translated": "and"}, {"phrase_source": "вона—додому", "phrase_translated": "she—home"}, {"phrase_source": ".", "phrase_translated": "."}]}
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
    predictions = []
    tasks = [
        translate(i, source_lang="ukrainian", target_lang="english") for i in questions
    ]
    completed = await asyncio.gather(*tasks)

    for answer_obj in completed:
        answer = " ".join([p.phrase_translated for p in answer_obj.translation])

        if raw_results:
            predictions.append(answer_obj)
        else:
            predictions.append(answer)

    return predictions


async def bert_test_llm(
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


def geval_test_llm(questions: list[str] = text_questions) -> None:
    """
    Evaluate LLM translation using DeepEval GEval metrics.
    """
    correctness = GEval(
        name="Translation correctness",
        model="gpt-4.1-mini",
        evaluation_steps=[
            "Ignore JSON structure, focus on translation quality",
            "Check translation correctness and accuracy",
            "Check grammar correctness",
            "Check vocabulary appropriateness",
            "Check if idioms and phrasal verbs are translated correctly",
            "Check punctuation correctness",
            "Check typo in input and is it corrected in output -> Success; else -> Failure",
        ],
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
        ],
    )

    structure_compliance = GEval(
        name="JSON Structure Compliance",
        model="gpt-4.1-mini",
        criteria="Check if LLM correctly decomposed the sentence into phrases. Idioms and phrasal verbs should be kept as single units. Punctuation should be correct. There"
        "are no entities like ... {phrase_source: '.', phrase_translated: '.'} ... but may be empty translation objects",
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
        ],
    )

    # Get LLM outputs (async) before running deepeval (sync)
    outputs = asyncio.run(ask_llm(questions, raw_results=True))

    dataset = EvaluationDataset()
    for i, output in enumerate(outputs):
        test_case = LLMTestCase(
            input=questions[i],
            actual_output=str(output),
        )
        dataset.add_test_case(test_case)

    evaluate(
        dataset.test_cases,
        metrics=[correctness, structure_compliance],
    )


if __name__ == "__main__":
    geval_test_llm(questions=text_questions)
