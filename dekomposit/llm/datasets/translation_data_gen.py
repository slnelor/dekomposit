"""Multi-language synthetic translation data generator for AutoML.

Generates high-quality translation pairs for fine-tuning translation models.
Supports 4 languages in all 12 directions: EN, RU, UK, SK.

Example AutoML TSV output (per direction):
    source\ttarget
    Hello!\tПривет!

Example JSON output:
    [
        {
            "source": "Hello!",
            "translated": "Привет!",
            "from_lang": "en",
            "to_lang": "ru"
        }
    ]

Usage:
    # Generate dataset
    generator = TranslationDataGenerator()
    pairs = await generator.generate(pairs_per_direction=1000)

    # Save for AutoML
    generator.save_automl_tsv(pairs, split_by_direction=True)
    generator.save(pairs)  # JSON backup

Examples source:
    This script reads rules and examples from TRANSLATION.md.
    Direction sections are written like:

        Slovak → Russian
        SK: ...
        RU: ...

        English → Ukrainian
        EN: ...
        UK: ...
"""

import json
import logging
import asyncio
import re
from pathlib import Path
from typing import cast
from collections import defaultdict
from pydantic import BaseModel, Field

from dekomposit.llm.base_client import Client
from dekomposit.llm.types import Translation


logging.basicConfig(
    datefmt="%d/%m/%Y %H:%M",
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Language code mapping
LANGUAGE_CODES = {
    "english": "en",
    "en": "en",
    "russian": "ru",
    "ru": "ru",
    "ukrainian": "uk",
    "uk": "uk",
    "ua": "uk",
    "slovak": "sk",
    "sk": "sk",
}

LANGUAGE_PREFIXES = {
    "EN": "en",
    "RU": "ru",
    "UK": "uk",
    "UA": "uk",
    "SK": "sk",
}

# All 12 ordered directions for 4 languages
ALL_DIRECTIONS = [
    ("en", "ru"),
    ("ru", "en"),
    ("en", "uk"),
    ("uk", "en"),
    ("en", "sk"),
    ("sk", "en"),
    ("ru", "uk"),
    ("uk", "ru"),
    ("ru", "sk"),
    ("sk", "ru"),
    ("uk", "sk"),
    ("sk", "uk"),
]


class TranslationBatch(BaseModel):
    """Schema for batch of generated translation pairs."""

    pairs: list[Translation] = Field(description="List of translation pairs")


class TranslationDataGenerator:
    """Generates synthetic translation pairs for multiple languages.

    Supports loading examples from TRANSLATION.md and generating
    datasets for all language directions (EN↔RU↔UK↔SK).

    Attributes:
        client: LLM client for API calls
        output_dir: Directory for saving outputs
        examples: Dict of (from_lang, to_lang) -> list of example pairs
    """

    def __init__(
        self,
        client: Client | None = None,
        output_dir: Path | None = None,
        examples_file: Path | None = None,
        strict_directions: bool = True,
    ) -> None:
        """Initialize the generator.

        Args:
            client: LLM client (creates default if None)
            output_dir: Directory for output files
            examples_file: Path to TRANSLATION.md (defaults to script dir)
        """
        self.client = client or Client()
        self.output_dir = output_dir or Path(__file__).parent
        self.examples_file = examples_file or self.output_dir / "TRANSLATION.md"
        self.strict_directions = strict_directions

        # Load rules and examples from file
        self.rules_text = self._load_rules_text(self.examples_file)
        self.examples = self._load_examples_from_file(self.examples_file)
        self._validate_examples(self.examples)

        logger.info(
            f"Initialized TranslationDataGenerator with model: {self.client.model}"
        )
        logger.info(f"Loaded {sum(len(v) for v in self.examples.values())} example pairs")

    def _load_rules_text(self, filepath: Path) -> str:
        """Extract translation rules block from TRANSLATION.md.

        The rules are everything before "### Examples of good translation".
        """
        if not filepath.exists():
            logger.warning(f"Examples file not found: {filepath}")
            return ""

        content = filepath.read_text(encoding="utf-8")
        marker = "### Examples of good translation"
        if marker in content:
            return content.split(marker, 1)[0].strip()
        return content.strip()

    def _load_examples_from_file(
        self, filepath: Path
    ) -> dict[tuple[str, str], list[str]]:
        """Parse TRANSLATION.md to extract example pairs per direction.

        Expected format:
            Slovak → Russian
            SK: ...
            RU: ...

            English → Ukrainian
            EN: ...
            UK: ...

        Args:
            filepath: Path to TRANSLATION.md

        Returns:
            Dict mapping (from_lang, to_lang) -> list of "source → target" examples
        """
        examples: dict[tuple[str, str], list[str]] = defaultdict(list)

        if not filepath.exists():
            logger.warning(f"Examples file not found: {filepath}")
            return examples

        content = filepath.read_text(encoding="utf-8")
        lines = content.splitlines()

        direction_pattern = re.compile(
            r"^\s*(?:###\s*)?(English|Russian|Ukrainian|Slovak)\s*→\s*(English|Russian|Ukrainian|Slovak)\s*$",
            re.IGNORECASE,
        )
        prefix_pattern = re.compile(r"^\s*([A-Z]{2}):\s*(.+)\s*$")

        current_from: str | None = None
        current_to: str | None = None
        pending_source: str | None = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            direction_match = direction_pattern.match(line)
            if direction_match:
                from_raw, to_raw = direction_match.groups()
                current_from = LANGUAGE_CODES.get(from_raw.lower())
                current_to = LANGUAGE_CODES.get(to_raw.lower())
                pending_source = None
                continue

            if not current_from or not current_to:
                continue

            prefix_match = prefix_pattern.match(line)
            if prefix_match:
                prefix, text = prefix_match.groups()
                lang = LANGUAGE_PREFIXES.get(prefix.upper())
                if not lang:
                    continue

                if lang == current_from:
                    pending_source = text.strip()
                    continue

                if lang == current_to and pending_source:
                    source = pending_source
                    target = text.strip()
                    if len(source) >= 3 and len(target) >= 3:
                        examples[(current_from, current_to)].append(
                            f"{source} → {target}"
                        )
                    pending_source = None
                continue

            # Fallback: unprefixed lines inside a direction block
            if pending_source is None:
                pending_source = line
            else:
                source = pending_source
                target = line
                if len(source) >= 3 and len(target) >= 3:
                    examples[(current_from, current_to)].append(
                        f"{source} → {target}"
                    )
                pending_source = None

        return examples

    def _validate_examples(
        self, examples: dict[tuple[str, str], list[str]]
    ) -> None:
        """Validate examples coverage for required directions."""
        if not self.strict_directions:
            return

        missing = [direction for direction in ALL_DIRECTIONS if not examples.get(direction)]
        if missing:
            missing_list = ", ".join([f"{a}→{b}" for a, b in missing])
            raise ValueError(
                "Missing examples in TRANSLATION.md for directions: "
                f"{missing_list}. Add example pairs for each direction."
            )

    async def _generate_batch(
        self,
        direction: str,
        examples: list[str],
        batch_size: int = 5,
    ) -> list[Translation]:
        """Generate a batch of translation pairs.

        Args:
            direction: Human-readable direction (e.g., "English to Russian")
            examples: Example patterns to guide generation
            batch_size: Number of pairs to generate

        Returns:
            List of Translation objects
        """
        # Select diverse examples (up to 5)
        selected_examples = examples[: min(5, len(examples))]

        rules_block = self.rules_text
        system_content = (
            f"You are a data generator for {direction} translation training."
        )
        if rules_block:
            system_content += f"\n\nRules:\n{rules_block}"

        messages = [
            {
                "role": "system",
                "content": system_content,
            },
            {
                "role": "user",
                "content": f"""Generate {batch_size} NEW, ORIGINAL sentence pairs for {direction} translation.

Examples of the desired style and quality:
{chr(10).join(f"- {ex}" for ex in selected_examples)}

Requirements:
- Direction: {direction}
- Include variety: idioms, slang, casual speech, questions, emotional expressions
- Keep tone natural, informal, culturally authentic
- Preserve typos/errors if present in source (don't autocorrect)
- Include cultural references and regional expressions
- Vary length: short phrases (2-3 words) to longer sentences (15+ words)
- Generate authentic, diverse content - not variations of the examples

Return as structured Translation data.""",
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

    def _filter_pair(self, pair: Translation) -> bool:
        """Apply quality filters to a translation pair.

        Args:
            pair: Translation pair to check

        Returns:
            True if pair passes all filters
        """
        # Must have source and target
        if not pair.source or not pair.translated:
            return False

        source = pair.source.strip()
        target = pair.translated.strip()

        # Min/max length
        if len(source) < 3 or len(target) < 3:
            return False
        if len(source) > 500 or len(target) > 500:
            return False

        # Skip if source equals target (no translation)
        if source.lower() == target.lower():
            return False

        # Skip if only numbers/symbols
        if not any(c.isalpha() for c in source):
            return False

        return True

    async def generate(
        self,
        pairs_per_direction: int = 100,
        batch_size: int = 5,
        max_concurrent: int = 3,
        directions: list[tuple[str, str]] | None = None,
    ) -> list[Translation]:
        """Generate synthetic translation dataset for multiple directions.

        Uses asyncio.gather() for concurrent generation with semaphore control.

        Args:
            pairs_per_direction: Number of pairs to generate per language direction
            batch_size: Pairs per API call
            max_concurrent: Maximum concurrent API calls
            directions: List of (from_lang, to_lang) tuples (defaults to ALL_DIRECTIONS)

        Returns:
            List of Translation Pydantic models
        """
        directions = directions or ALL_DIRECTIONS
        num_batches = (pairs_per_direction + batch_size - 1) // batch_size

        logger.info(
            f"Starting async generation: {len(directions)} directions, "
            f"{pairs_per_direction} pairs each, {num_batches} batches per direction"
        )

        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(max_concurrent)

        async def generate_direction_with_limit(
            from_lang: str,
            to_lang: str,
        ) -> list[Translation]:
            """Generate all batches for one direction with concurrency control."""
            direction_key = (from_lang, to_lang)
            direction_examples = self.examples.get(direction_key, [])

            if not direction_examples:
                logger.warning(f"No examples found for {from_lang}→{to_lang}")
                return []

            direction_label = f"{from_lang.upper()} to {to_lang.upper()}"
            all_pairs: list[Translation] = []

            for batch_num in range(num_batches):
                async with semaphore:
                    pairs = await self._generate_batch(
                        direction_label, direction_examples, batch_size
                    )

                    # Apply quality filters
                    for pair in pairs:
                        pair.from_lang = from_lang
                        pair.to_lang = to_lang
                        if self._filter_pair(pair):
                            all_pairs.append(pair)

                    logger.debug(
                        f"{direction_label} batch {batch_num+1}/{num_batches}: "
                        f"generated {len(pairs)}, kept {len([p for p in pairs if self._filter_pair(p)])}"
                    )

            return all_pairs

        # Build tasks for all directions
        tasks: list[asyncio.Task[list[Translation]]] = []
        for from_lang, to_lang in directions:
            task = asyncio.create_task(
                generate_direction_with_limit(from_lang, to_lang)
            )
            tasks.append(task)

        # Execute all tasks concurrently
        logger.info(f"Executing {len(tasks)} direction tasks concurrently...")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect results
        all_pairs: list[Translation] = []
        for i, result in enumerate(results):
            from_lang, to_lang = directions[i]
            if isinstance(result, BaseException):
                logger.error(f"Direction {from_lang}→{to_lang} failed: {result}")
            else:
                all_pairs.extend(result)
                logger.info(
                    f"Direction {from_lang}→{to_lang}: generated {len(result)} pairs"
                )

        logger.info(f"Successfully generated {len(all_pairs)} total translation pairs")
        return all_pairs

    def save(
        self,
        pairs: list[Translation],
        filename: str = "synthetic_translations.json",
    ) -> Path:
        """Save translation pairs to JSON file.

        Args:
            pairs: List of Translation Pydantic models
            filename: Output filename

        Returns:
            Path to saved file
        """
        output_path = self.output_dir / filename
        data = [pair.model_dump() for pair in pairs]

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {len(pairs)} Translation models to: {output_path}")
        return output_path

    def save_automl_tsv(
        self,
        pairs: list[Translation],
        output_dir: Path | None = None,
        split_by_direction: bool = True,
    ) -> list[Path]:
        """Save translation pairs in AutoML TSV format.

        AutoML Translation expects TSV files with:
            source\ttarget

        Args:
            pairs: List of Translation models
            output_dir: Directory for TSV files (defaults to self.output_dir/automl)
            split_by_direction: If True, creates separate TSV per direction

        Returns:
            List of paths to created TSV files
        """
        output_dir = output_dir or self.output_dir / "automl"
        output_dir.mkdir(parents=True, exist_ok=True)

        saved_files: list[Path] = []

        if split_by_direction:
            # Group by direction
            by_direction: dict[tuple[str, str], list[Translation]] = defaultdict(list)
            for pair in pairs:
                if pair.from_lang and pair.to_lang:
                    by_direction[(pair.from_lang, pair.to_lang)].append(pair)

            # Save one file per direction
            for (from_lang, to_lang), direction_pairs in by_direction.items():
                filename = f"{from_lang}-{to_lang}.tsv"
                filepath = output_dir / filename

                with open(filepath, "w", encoding="utf-8") as f:
                    f.write("source\ttarget\n")
                    for pair in direction_pairs:
                        source = (pair.source or "").replace("\t", " ").replace("\n", " ")
                        target = (pair.translated or "").replace("\t", " ").replace("\n", " ")
                        if source and target:  # Only write if both exist
                            f.write(f"{source}\t{target}\n")

                saved_files.append(filepath)
                logger.info(
                    f"Saved {len(direction_pairs)} pairs to AutoML TSV: {filepath}"
                )
        else:
            # Save all in one file
            filepath = output_dir / "all_translations.tsv"
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("source\ttarget\n")
                for pair in pairs:
                    source = (pair.source or "").replace("\t", " ").replace("\n", " ")
                    target = (pair.translated or "").replace("\t", " ").replace("\n", " ")
                    if source and target:
                        f.write(f"{source}\t{target}\n")

            saved_files.append(filepath)
            logger.info(f"Saved {len(pairs)} pairs to AutoML TSV: {filepath}")

        return saved_files

    @staticmethod
    def load(filepath: Path | str) -> list[Translation]:
        """Load translation pairs from JSON file.

        Args:
            filepath: Path to JSON file

        Returns:
            List of Translation Pydantic models
        """
        path = Path(filepath)

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        translations = [Translation(**item) for item in data]
        logger.info(f"Loaded {len(translations)} Translation models from: {path}")
        return translations


async def main() -> None:
    """Main entry point for CLI execution."""
    generator = TranslationDataGenerator()

    # Generate translations for all directions
    pairs = await generator.generate(
        pairs_per_direction=10,  # Small number for testing
        batch_size=5,
        max_concurrent=3,
    )

    # Save results
    generator.save(pairs, "synthetic_translations_all.json")
    generator.save_automl_tsv(pairs, split_by_direction=True)

    # Display summary
    logger.info("\n" + "=" * 60)
    logger.info("Generation Summary:")
    logger.info("=" * 60)

    # Count by direction
    by_direction: dict[tuple[str, str], int] = defaultdict(int)
    for pair in pairs:
        if pair.from_lang and pair.to_lang:
            by_direction[(pair.from_lang, pair.to_lang)] += 1

    for (from_lang, to_lang), count in sorted(by_direction.items()):
        logger.info(f"  {from_lang}→{to_lang}: {count} pairs")

    logger.info(f"\nTotal: {len(pairs)} pairs")

    # Show samples
    logger.info("\nSample generated pairs:")
    for i, pair in enumerate(pairs[:5], 1):
        logger.info(f"\n{i}. [{pair.from_lang} → {pair.to_lang}] {pair.source}")
        logger.info(f"   → {pair.translated}")


if __name__ == "__main__":
    asyncio.run(main())
