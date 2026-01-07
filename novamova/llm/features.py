import asyncio

from .prompts import TranslationPrompt
from .types import Language, PhraseDetailed, Translation
from .base_client import client, LLM_MODEL


async def translate(
    source_lang: Language | str, target_lang: Language | str
) -> Translation:
    prompt = TranslationPrompt(source_lang, target_lang)
    prompt_text = prompt.get_prompt("I just wanna say you should fall your back")

    # 25/12/2025 Gemini openai compatible endpoint does not support responses API
    response = await client.chat.completions.parse(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": prompt.system_prompt},
            {"role": "user", "content": prompt_text},
        ],
        response_format=PhraseDetailed,
    )

    print(prompt.json_schema)
    print(response.choices[0].message.parsed)
    return response.choices[0].message.parsed


asyncio.run(translate("english", "russian"))
