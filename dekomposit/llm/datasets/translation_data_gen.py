"""Synthetic translation data generation using LLM.

This module generates synthetic Slovak-Russian translation pairs for training/evaluation.
Unlike DeepEval Synthesizer (designed for RAG), this generates actual translation pairs
as Pydantic Translation models that can be easily serialized and deserialized.

Example output format (JSON):
    [
        {
            "source": "Povedz mi, kam si schoval ten bordel!",
            "translated": "Скажи мне, куда ты засунул этот бардак!",
            "from_lang": "sk",
            "to_lang": "ru"
        }
    ]

Usage:
    # Generate and save
    generator = TranslationDataGenerator()
    pairs = await generator.generate(num_pairs=30)
    generator.save(pairs)
    
    # Load back
    loaded = TranslationDataGenerator.load("synthetic_translations.json")
    # Returns list[Translation] - fully typed Pydantic models
"""

import json
import logging
import asyncio
from pathlib import Path
from typing import cast
from pydantic import BaseModel, Field

from dekomposit.llm.base_client import Client
from dekomposit.llm.types import Translation


logging.basicConfig(
    datefmt="%d/%m/%Y %H:%M",
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class TranslationBatch(BaseModel):
    """Schema for batch of generated translation pairs."""

    pairs: list[Translation] = Field(description="List of translation pairs")


class TranslationDataGenerator:
    """Generates synthetic translation pairs using LLM.

    Uses your existing TRANSLATION.md examples as patterns to generate
    new, similar translation pairs with the same style (slang, idioms, etc.)

    Attributes:
        client: LLM client for making generation requests
        output_dir: Directory to save generated data
    """

    def __init__(
        self, client: Client | None = None, output_dir: Path | None = None
    ) -> None:
        """Initialize the generator.

        Args:
            client: LLM client (creates default if None)
            output_dir: Where to save output files (defaults to script dir)
        """
        self.client = client or Client()
        self.output_dir = output_dir or Path(__file__).parent

        # Example patterns for few-shot prompting
        self._sk_to_ru_examples = [
            "SK: Povedz mi, kam si schoval ten bordel, lebo nemám celý deň! → RU: Скажи мне, куда ты засунул этот бардак, потому что у меня нет целого дня!",
            "SK: Mám toho po krk, fakt už nevládzem. → RU: Мне это по горло, реально больше не могу.",
            "SK: Ten chlap je uplne debil nerozumie ničomu → RU: Этот чувак полный дебил, ничего не понимает.",
            "SK: Nebud' taký pičus, pomôž mi s tým. → RU: Не будь таким говнюком, помоги мне с этим.",
            "SK: Musíme to dotiahnuť do konca, inak sme v prdeli. → RU: Мы должны довести это до конца, иначе мы в жопе.",
        ]

        self._ru_to_sk_examples = [
            "RU: Блин забыл куда положил ключи → SK: Blin, zabudol som, kam som položil kľúče.",
            "RU: Он совсем охренел, требует невозможное. → SK: Úplne zbláznil, požaduje nemožné.",
            "RU: Мне по барабану, что они думают. → SK: Je mi to ukradnuté, čo si myslia.",
            "RU: Не ссы, все будет нормально! → SK: Neboj sa, všetko bude v poriadku!",
            "RU: Пошел на хуй со своими советами! → SK: Choď do piče so svojimi radami!",
        ]

        logger.info(
            f"Initialized TranslationDataGenerator with model: {self.client.model}"
        )

    async def _generate_batch(
        self, direction: str, examples: list[str], batch_size: int = 5
    ) -> list[Translation]:
        """Generate a batch of translation pairs.

        Args:
            direction: Translation direction (e.g., "Slovak to Russian")
            examples: Example patterns to guide generation
            batch_size: Number of pairs to generate

        Returns:
            List of Translation objects
        """
        messages = [
            {
                "role": "system",
                "content": "You are a data generator for Slovak-Russian translation training.",
            },
            {
                "role": "user",
                "content": f"""Based on these example patterns:
{chr(10).join(f"- {ex}" for ex in examples[:5])}

Generate {batch_size} NEW, ORIGINAL sentence pairs following the same style.

Requirements:
- Direction: {direction}
- Include: idioms, slang, casual speech, questions, emotional expressions
- Keep same tone (casual, informal, natural)
- Preserve typos/errors if present in source
- Include cultural references and regional expressions
- Vary length: short phrases to longer sentences

Return as structured data.""",
            },
        ]

        try:
            response = await self.client.request(
                messages=messages, return_format=TranslationBatch
            )

            result = cast(TranslationBatch | None, response.choices[0].message.parsed)
            if result is not None:
                logger.debug(f"Generated {len(result.pairs)} pairs for {direction}")
                return result.pairs
            return []

        except Exception as e:
            logger.error(f"Failed to generate batch for {direction}: {e}")
            return []

    async def generate(
        self,
        num_pairs: int = 30,
        batch_size: int = 5,
        rate_limit_delay: float = 1.0,
    ) -> list[Translation]:
        """Generate synthetic translation dataset.

        Args:
            num_pairs: Total number of pairs to generate
            batch_size: Pairs per batch
            rate_limit_delay: Seconds to wait between batches

        Returns:
            List of Translation Pydantic models with from_lang/to_lang set
        """
        logger.info(f"Starting generation of {num_pairs} translation pairs")

        all_pairs: list[Translation] = []
        num_batches = (num_pairs + batch_size - 1) // batch_size
        sk_ru_batches = num_batches // 2

        # Generate SK → RU pairs
        logger.info(f"Generating {sk_ru_batches} SK→RU batches...")
        for i in range(sk_ru_batches):
            pairs = await self._generate_batch(
                "Slovak to Russian", self._sk_to_ru_examples, batch_size
            )
            for pair in pairs:
                pair.from_lang = "sk"
                pair.to_lang = "ru"
                all_pairs.append(pair)
            await asyncio.sleep(rate_limit_delay)

        # Generate RU → SK pairs
        ru_sk_batches = num_batches - sk_ru_batches
        logger.info(f"Generating {ru_sk_batches} RU→SK batches...")
        for i in range(ru_sk_batches):
            pairs = await self._generate_batch(
                "Russian to Slovak", self._ru_to_sk_examples, batch_size
            )
            for pair in pairs:
                pair.from_lang = "ru"
                pair.to_lang = "sk"
                all_pairs.append(pair)
            await asyncio.sleep(rate_limit_delay)

        logger.info(f"Successfully generated {len(all_pairs)} translation pairs")
        return all_pairs

    def save(
        self,
        pairs: list[Translation],
        filename: str = "synthetic_translations.json",
    ) -> Path:
        """Save translation pairs to JSON file.

        Serializes Pydantic Translation models to JSON that can be
        parsed back using TranslationDataGenerator.load()

        Args:
            pairs: List of Translation Pydantic models
            filename: Output filename

        Returns:
            Path to saved file
        """
        output_path = self.output_dir / filename

        # Serialize Pydantic models to JSON
        data = [pair.model_dump() for pair in pairs]

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(pairs)} Translation models to: {output_path}")
        return output_path

    @staticmethod
    def load(filepath: Path | str) -> list[Translation]:
        """Load translation pairs from JSON file.

        Parses JSON back into Pydantic Translation models for type safety.

        Args:
            filepath: Path to JSON file

        Returns:
            List of Translation Pydantic models

        Example:
            pairs = TranslationDataGenerator.load("synthetic_translations.json")
            for pair in pairs:
                print(f"{pair.from_lang} → {pair.to_lang}: {pair.source}")
        """
        path = Path(filepath)

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Parse back into Pydantic models
        translations = [Translation(**item) for item in data]

        logger.info(f"Loaded {len(translations)} Translation models from: {path}")
        return translations


async def main() -> None:
    """Main entry point for CLI execution."""
    generator = TranslationDataGenerator()

    # Generate translations
    pairs = await generator.generate(num_pairs=30)

    # Save results
    output_file = generator.save(pairs)

    # Display samples
    logger.info("\nSample generated pairs:")
    for i, pair in enumerate(pairs[:5], 1):
        logger.info(f"\n{i}. [{pair.from_lang} → {pair.to_lang}] {pair.source}")
        logger.info(f"   → {pair.translated}")

    # Demonstrate loading back
    logger.info("\n\nDemonstrating load functionality:")
    loaded_pairs = TranslationDataGenerator.load(output_file)
    logger.info(f"Successfully loaded {len(loaded_pairs)} Translation models")
    logger.info(f"First pair type: {type(loaded_pairs[0]).__name__}")


if __name__ == "__main__":
    asyncio.run(main())
