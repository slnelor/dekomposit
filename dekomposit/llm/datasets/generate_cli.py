"""Interactive CLI for generating synthetic translation datasets.

Uses Rich for a guided, keyboard-driven flow to pick model, directions,
and size. Supports OpenAI, Gemini, and OpenRouter models.

Usage:
    python -m dekomposit.llm.datasets.generate_cli
"""

from __future__ import annotations

import asyncio
import importlib
import json
import logging
import os
import signal
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
from dotenv import load_dotenv
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

logging.basicConfig(
    datefmt="%d/%m/%Y %H:%M",
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console = Console()
load_dotenv()

if TYPE_CHECKING:
    from dekomposit.llm.types import Translation

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

DIRECTION_LABELS = {
    ("en", "ru"): "English -> Russian",
    ("ru", "en"): "Russian -> English",
    ("en", "uk"): "English -> Ukrainian",
    ("uk", "en"): "Ukrainian -> English",
    ("en", "sk"): "English -> Slovak",
    ("sk", "en"): "Slovak -> English",
    ("ru", "uk"): "Russian -> Ukrainian",
    ("uk", "ru"): "Ukrainian -> Russian",
    ("ru", "sk"): "Russian -> Slovak",
    ("sk", "ru"): "Slovak -> Russian",
    ("uk", "sk"): "Ukrainian -> Slovak",
    ("sk", "uk"): "Slovak -> Ukrainian",
}

OPENAI_MODELS = [
    "gpt-5-nano",
    "gpt-5-mini",
    "gpt-4o-mini",
    "gpt-4o",
]

GEMINI_MODELS = [
    "gemini-flash-lite-latest",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]

# Global flag for graceful shutdown
_shutdown_requested = False


@dataclass(frozen=True)
class ModelChoice:
    provider: str
    model: str
    api_key_env: str


def setup_signal_handlers(cli_instance: "DatasetGeneratorCLI") -> None:
    """Setup signal handlers for graceful shutdown.

    Uses a flag-based approach to avoid blocking I/O in signal handler context.
    The CLI checks this flag periodically and prompts the user at safe points.
    """

    def signal_handler(signum, frame):
        global _shutdown_requested
        sig_name = signal.Signals(signum).name
        # Use simple print to avoid rich console issues in signal context
        print(
            f"\n[SIGNAL] Received {sig_name} - will prompt for confirmation at next safe point..."
        )
        _shutdown_requested = True

    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # kill command
    # Note: Ctrl+Z (SIGTSTP) suspends the process - we can't intercept it easily
    # Users should use 'fg' to resume the suspended process


class DatasetGeneratorCLI:
    def __init__(self) -> None:
        self.console = Console()
        self.output_dir = Path(__file__).parent
        self._current_pairs: list = []

    def run(self) -> None:
        setup_signal_handlers(self)

        self.console.clear()
        self.console.print(
            Panel.fit(
                "[bold cyan]Translation Dataset Generator[/bold cyan]",
                border_style="cyan",
            )
        )
        self.console.print()
        self.console.print("[dim]Press Ctrl+C to pause/exit gracefully[/dim]")
        self.console.print()

        existing_counts = self.check_existing_data()

        if any(existing_counts.values()):
            self.console.print(
                f"[yellow]Found existing data:[/yellow] {sum(existing_counts.values())} total pairs"
            )
            table = Table(
                show_header=True, header_style="bold magenta", box=box.ROUNDED
            )
            table.add_column("Direction")
            table.add_column("Current", justify="right")

            for direction in ALL_DIRECTIONS:
                count = existing_counts.get(direction, 0)
                if count > 0:
                    table.add_row(
                        f"{direction[0]}->{direction[1]}",
                        str(count),
                    )

            self.console.print(table)
            self.console.print()

            if not Confirm.ask("Resume and append to existing data?", default=True):
                if Confirm.ask("Delete existing data and start fresh?", default=False):
                    self.delete_existing_data()
                    existing_counts = {}
                else:
                    self.console.print("[yellow]Cancelled.[/yellow]")
                    return

        model_choice = self.select_model()
        if model_choice is None:
            return

        directions = self.select_directions()
        if not directions:
            return

        target_per_direction = self.ask_int(
            "Target pairs per direction", default=5000, min_value=1
        )

        batch_size = 5
        max_concurrent = 3
        if Confirm.ask("Advanced settings?", default=False):
            batch_size = self.ask_int("Batch size", default=5, min_value=1)
            max_concurrent = self.ask_int(
                "Max concurrent requests", default=3, min_value=1
            )

        summary = Table(box=box.SIMPLE, show_header=False)
        summary.add_row("Model", model_choice.model)
        summary.add_row("Provider", model_choice.provider)
        summary.add_row("Directions", str(len(directions)))

        if any(existing_counts.values()):
            summary.add_row("Existing pairs", str(sum(existing_counts.values())))
            remaining = sum(
                max(0, target_per_direction - existing_counts.get(d, 0))
                for d in directions
            )
            summary.add_row("Remaining to generate", str(remaining))
        else:
            summary.add_row("Target per direction", str(target_per_direction))

        summary.add_row("Batch size", str(batch_size))
        summary.add_row("Max concurrent", str(max_concurrent))

        self.console.print(Panel(summary, title="Run Summary", border_style="green"))
        if not Confirm.ask("Start generation?", default=True):
            return

        self.run_generation(
            model_choice=model_choice,
            directions=directions,
            target_per_direction=target_per_direction,
            existing_counts=existing_counts,
            batch_size=batch_size,
            max_concurrent=max_concurrent,
        )

    def check_existing_data(self) -> dict[tuple[str, str], int]:
        """Check existing TSV files and count pairs per direction."""
        counts: dict[tuple[str, str], int] = {}
        automl_dir = self.output_dir / "automl"

        if not automl_dir.exists():
            return counts

        for direction in ALL_DIRECTIONS:
            tsv_file = automl_dir / f"{direction[0]}-{direction[1]}.tsv"
            if tsv_file.exists():
                with open(tsv_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    counts[direction] = len(lines) - 1

        return counts

    def delete_existing_data(self) -> None:
        """Delete existing JSON and TSV files."""
        json_file = self.output_dir / "synthetic_translations_all.json"
        if json_file.exists():
            json_file.unlink()

        automl_dir = self.output_dir / "automl"
        if automl_dir.exists():
            for f in automl_dir.glob("*.tsv"):
                f.unlink()

        self.console.print("[green]Existing data deleted.[/green]")

    def save_progress(self) -> None:
        """Save current progress to files."""
        if not self._current_pairs:
            return

        try:
            from dekomposit.llm.datasets.translation_data_gen import (
                TranslationDataGenerator,
            )

            generator = TranslationDataGenerator()
            generator.save(self._current_pairs, "synthetic_translations_all.json")
            generator.save_automl_tsv(self._current_pairs, split_by_direction=True)

            self.console.print(
                f"[green]Progress saved: {len(self._current_pairs)} pairs[/green]"
            )
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")
            self.console.print(f"[red]Warning: Could not save progress: {e}[/red]")

    def select_model(self) -> ModelChoice | None:
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.console.print("[bold]Select model[/bold]")

        options: list[tuple[str, str]] = []
        for model in OPENAI_MODELS:
            options.append(("openai", model))
        for model in GEMINI_MODELS:
            options.append(("gemini", model))

        table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
        table.add_column("#", style="dim", width=3)
        table.add_column("Provider")
        table.add_column("Model")

        for i, (provider, model) in enumerate(options, 1):
            table.add_row(str(i), provider, model)

        extra_start = len(options) + 1
        if openrouter_key:
            table.add_row(str(extra_start), "openrouter", "Search models")

        self.console.print(table)
        self.console.print()

        choices = [str(i) for i in range(1, len(options) + 1)]
        if openrouter_key:
            choices.append(str(extra_start))

        selection = Prompt.ask("Select a model", choices=choices, default="1")

        if openrouter_key and selection == str(extra_start):
            model = self.select_openrouter_model()
            if not model:
                return None
            return ModelChoice(
                provider="openrouter",
                model=model,
                api_key_env="OPENROUTER_API_KEY",
            )

        provider, model = options[int(selection) - 1]

        if openrouter_key and Confirm.ask("Route through OpenRouter?", default=False):
            return ModelChoice(
                provider="openrouter",
                model=model,
                api_key_env="OPENROUTER_API_KEY",
            )

        if provider == "openai":
            return ModelChoice(
                provider="openai",
                model=model,
                api_key_env="OPENAI_API_KEY",
            )

        return ModelChoice(
            provider="gemini",
            model=model,
            api_key_env="GEMINI_API_KEY",
        )

    def select_openrouter_model(self) -> str | None:
        if not os.getenv("OPENROUTER_API_KEY"):
            self.console.print("[red]OPENROUTER_API_KEY not set.[/red]")
            return None

        query = Prompt.ask("Search OpenRouter models", default="")
        models = self.fetch_openrouter_models(query)
        if not models:
            self.console.print("[red]No models found.[/red]")
            return None

        limit = min(30, len(models))
        table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
        table.add_column("#", style="dim", width=3)
        table.add_column("Model")

        for i, model in enumerate(models[:limit], 1):
            table.add_row(str(i), model)

        self.console.print(table)
        self.console.print()

        choice = Prompt.ask(
            "Select model", choices=[str(i) for i in range(1, limit + 1)]
        )
        return models[int(choice) - 1]

    def fetch_openrouter_models(self, query: str) -> list[str]:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return []

        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://localhost",
            "X-Title": "dekomposit-datasets",
        }

        try:
            with httpx.Client(timeout=20.0) as client:
                response = client.get(
                    "https://openrouter.ai/api/v1/models", headers=headers
                )
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            self.console.print(f"[red]OpenRouter request failed: {exc}[/red]")
            return []

        data = payload.get("data", [])
        models = [item.get("id", "") for item in data if item.get("id")]

        if query:
            query_lower = query.lower()
            models = [model for model in models if query_lower in model.lower()]

        return models

    def select_directions(self) -> list[tuple[str, str]]:
        if Confirm.ask("Use all directions?", default=True):
            return list(ALL_DIRECTIONS)

        table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
        table.add_column("#", style="dim", width=3)
        table.add_column("Direction")
        table.add_column("Description", style="dim")

        for i, direction in enumerate(ALL_DIRECTIONS, 1):
            table.add_row(
                str(i), f"{direction[0]}-{direction[1]}", DIRECTION_LABELS[direction]
            )

        self.console.print(table)
        self.console.print()

        raw = Prompt.ask("Enter comma-separated numbers (e.g. 1,3,7)")
        selected: list[tuple[str, str]] = []
        for item in raw.split(","):
            item = item.strip()
            if not item:
                continue
            if not item.isdigit():
                self.console.print(f"[red]Invalid choice: {item}[/red]")
                return []
            index = int(item)
            if index < 1 or index > len(ALL_DIRECTIONS):
                self.console.print(f"[red]Out of range: {item}[/red]")
                return []
            selected.append(ALL_DIRECTIONS[index - 1])

        return selected

    def run_generation(
        self,
        model_choice: ModelChoice,
        directions: list[tuple[str, str]],
        target_per_direction: int,
        existing_counts: dict[tuple[str, str], int],
        batch_size: int,
        max_concurrent: int,
    ) -> None:
        api_key = os.getenv(model_choice.api_key_env)
        if not api_key:
            self.console.print(
                f"[red]Missing {model_choice.api_key_env} in environment.[/red]"
            )
            return

        os.environ["CURRENT_LLM"] = model_choice.model
        os.environ["CURRENT_PROVIDER"] = model_choice.provider
        os.environ["CURRENT_API_KEY"] = model_choice.api_key_env

        import dekomposit.config as config
        import dekomposit.llm.base_client as base_client

        importlib.reload(config)
        importlib.reload(base_client)

        from dekomposit.llm.datasets.translation_data_gen import (
            TranslationDataGenerator,
        )

        async def runner() -> None:
            global _shutdown_requested

            generator = TranslationDataGenerator()

            existing_pairs = []
            if any(existing_counts.values()):
                existing_pairs = self.load_existing_pairs()

            all_new_pairs: list = []

            try:
                for direction in directions:
                    global _shutdown_requested
                    if _shutdown_requested:
                        break

                    current_count = existing_counts.get(direction, 0)
                    needed = max(0, target_per_direction - current_count)

                    if needed == 0:
                        self.console.print(
                            f"[green]{direction[0]}->{direction[1]}: already complete ({current_count})[/green]"
                        )
                        continue

                    self.console.print(
                        f"[cyan]Generating {needed} pairs for {direction[0]}->{direction[1]}...[/cyan]"
                    )

                    # Generate with retry logic for network errors
                    direction_pairs = await self.generate_with_retry(
                        generator=generator,
                        needed=needed,
                        batch_size=batch_size,
                        max_concurrent=max_concurrent,
                        direction=direction,
                    )

                    all_new_pairs.extend(direction_pairs)
                    self._current_pairs = existing_pairs + all_new_pairs

                    if _shutdown_requested:
                        break

            except Exception as e:
                logger.error(f"Generation error: {e}")
                self.console.print(f"[red]Error during generation: {e}[/red]")
            finally:
                # Always save progress
                self._current_pairs = existing_pairs + all_new_pairs
                if self._current_pairs:
                    self.console.print("[yellow]Saving progress...[/yellow]")
                    self.save_progress()

            # Final save
            all_pairs = existing_pairs + all_new_pairs

            if all_pairs:
                generator.save(all_pairs, "synthetic_translations_all.json")
                generator.save_automl_tsv(all_pairs, split_by_direction=True)

                self.print_summary(all_pairs)

        with self.console.status("Generating datasets...", spinner="dots"):
            try:
                asyncio.run(runner())
            except KeyboardInterrupt:
                # This shouldn't happen with signal handler, but just in case
                self.console.print("\n[yellow]Interrupted by user[/yellow]")
                if self._current_pairs:
                    self.save_progress()

    async def generate_with_retry(
        self,
        generator,
        needed: int,
        batch_size: int,
        max_concurrent: int,
        direction: tuple[str, str],
    ) -> list:
        """Generate pairs with retry logic for network errors.

        Retries indefinitely for network errors with exponential backoff up to 5 minutes.
        Handles internet outages lasting 20+ minutes gracefully.
        User can interrupt at any time with Ctrl+C.
        """
        global _shutdown_requested

        import time

        attempt = 0
        retry_delay = 5  # seconds
        max_delay = 300  # 5 minutes max between retries
        total_wait_time = 0
        start_time = time.time()

        while True:
            if _shutdown_requested:
                self.console.print(
                    f"[yellow]Shutdown requested for {direction[0]}->{direction[1]}, stopping...[/yellow]"
                )
                return []

            try:
                attempt += 1
                pairs = await generator.generate(
                    pairs_per_direction=needed,
                    batch_size=batch_size,
                    max_concurrent=max_concurrent,
                    directions=[direction],
                )

                # Success! Reset counters for next direction
                if attempt > 1:
                    elapsed = time.time() - start_time
                    self.console.print(
                        f"[green]✓ Success after {attempt} attempts ({elapsed:.0f}s) for {direction[0]}->{direction[1]}[/green]"
                    )
                return pairs

            except (
                httpx.ConnectError,
                httpx.TimeoutException,
                httpx.NetworkError,
                httpx.ReadTimeout,
                httpx.WriteTimeout,
                httpx.PoolTimeout,
            ) as e:
                elapsed = time.time() - start_time

                self.console.print(
                    f"[yellow]Network error for {direction[0]}->{direction[1]}: {type(e).__name__}[/yellow]"
                )
                self.console.print(
                    f"[yellow]Attempt {attempt} | Waiting {retry_delay}s before retry (total downtime: {elapsed:.0f}s)[/yellow]"
                )

                # Wait with periodic checks for shutdown signal
                waited = 0
                check_interval = 1  # Check every second
                while waited < retry_delay and not _shutdown_requested:
                    await asyncio.sleep(min(check_interval, retry_delay - waited))
                    waited += check_interval

                if _shutdown_requested:
                    return []

                # Exponential backoff: 5s, 10s, 20s, 40s, 60s, 120s, 180s, 240s, 300s, 300s...
                retry_delay = min(retry_delay * 2, max_delay)
                total_wait_time += retry_delay

                # After 20 minutes of waiting, auto-skip this direction
                # (User may not be present to respond to prompts)
                if elapsed > 1200:  # 20 minutes
                    self.console.print(
                        f"[yellow]Network down for {elapsed / 60:.0f}min, auto-skipping {direction[0]}->{direction[1]}[/yellow]"
                    )
                    return []

            except Exception as e:
                # Non-network errors - log and return
                self.console.print(
                    f"[red]Unexpected error for {direction[0]}->{direction[1]}: {e}[/red]"
                )
                logger.exception("Generation error")
                return []

    def load_existing_pairs(self) -> list:
        """Load existing pairs from JSON file."""
        json_file = self.output_dir / "synthetic_translations_all.json"
        if not json_file.exists():
            return []

        try:
            from dekomposit.llm.types import Translation

            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            return [Translation(**item) for item in data]
        except Exception as e:
            logger.warning(f"Failed to load existing pairs: {e}")
            return []

    def print_summary(self, pairs: list["Translation"]) -> None:
        by_direction: dict[tuple[str, str], int] = defaultdict(int)
        for pair in pairs:
            if pair.from_lang and pair.to_lang:
                by_direction[(pair.from_lang, pair.to_lang)] += 1

        table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
        table.add_column("Direction")
        table.add_column("Count", justify="right")

        for direction, count in sorted(by_direction.items()):
            table.add_row(f"{direction[0]}->{direction[1]}", str(count))

        self.console.print(
            Panel(table, title="Generation Summary", border_style="green")
        )
        self.console.print(f"Total pairs: [bold]{sum(by_direction.values())}[/bold]")

    @staticmethod
    def ask_int(label: str, default: int, min_value: int = 1) -> int:
        while True:
            raw = Prompt.ask(label, default=str(default))
            if not raw.isdigit():
                console.print("[red]Enter a valid integer.[/red]")
                continue
            value = int(raw)
            if value < min_value:
                console.print(f"[red]Value must be >= {min_value}.[/red]")
                continue
            return value


def main() -> None:
    DatasetGeneratorCLI().run()


if __name__ == "__main__":
    main()
