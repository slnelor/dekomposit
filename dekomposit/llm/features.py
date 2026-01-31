from .prompts import TranslationPrompt
from .types import Language, Translation
from .base_client import Client


async def translate(
    text: str, *, source_lang: Language | str, target_lang: Language | str
) -> Translation:
    prompt = TranslationPrompt(source_lang, target_lang)
    prompt_text = prompt.get_prompt(text)

    client = Client()
    response = await client.request(
        messages=[
            {"role": "system", "content": prompt.system_prompt},
            {"role": "user", "content": prompt_text},
        ],
        return_format=Translation,
    )

    return response.choices[0].message.parsed
