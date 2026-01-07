from openai import OpenAI
import time
import sys


BASE_URL = None
MODEL = "gpt-5-mini"

if sys.argv[1:]:
    MODEL = sys.argv[1]
    if sys.argv[2:]:
        BASE_URL = sys.argv[2]


client = OpenAI(
    base_url=BASE_URL,
)

prompts = [
    "Translate the following sentences. Languages: (English, Russian, Slovak)"
    "The old man saw the saw saw the wood.",
    "Руки не доходять подивитися цей фільм.",
    "Mám toho po krk.",
    "He bought a lemon from the dealership.",
    "Косил косой косой косой.",
    "Time flies like an arrow; fruit flies like a banana.",
    "Nech nejem, keď to neviem.",
    "Він на цьому собаку з’їв.",
    "Да нет, наверное.",
    "Get off my back.",
    "It's raining cats and dogs.",
    "Hodilo by sa mi to.",
    "Buffalo Buffalo Buffalo Buffalo Buffalo Buffalo Buffalo buffalo.",
    "На злодієві шапка горить.",
    "Break a leg!",
]

messages = [{"role": "user", "content": msg} for msg in prompts]

start_time = time.time()
response = client.chat.completions.create(
    model=MODEL,
    messages=messages,
)
end_time = time.time() - start_time

print(f"{MODEL} finished in {end_time}")
for r in response.choices:
    print(r.message.content)
