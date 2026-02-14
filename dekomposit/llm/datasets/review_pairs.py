"""Interactive CLI for reviewing and approving translation pairs.

Uses Rich library for a modern, keyboard-driven interface.
Supports batch review, editing, and approval/rejection.

Usage:
    python -m dekomposit.llm.datasets.review_pairs
"""

import json
import logging
from pathlib import Path
from typing import cast

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.layout import Layout
from rich import box
from rich.text import Text

from dekomposit.llm.types import Translation


def check_translation_quality(pair: Translation) -> list[str]:
    """Check for common translation issues.
    
    Returns list of warning messages.
    """
    warnings = []
    source = (pair.source or "").strip()
    target = (pair.translated or "").strip()
    
    if not source or not target:
        return warnings
    
    # Check if source and target are identical (untranslated)
    if source.lower() == target.lower():
        warnings.append("⚠️  Identical source/target (untranslated?)")
    
    # Check length ratio (source vs target)
    len_ratio = len(target) / len(source) if len(source) > 0 else 0
    if len_ratio > 3 or len_ratio < 0.3:
        warnings.append(f"⚠️  Unusual length ratio: {len_ratio:.1f}x")
    
    # Check for Slavic languages: warn about potential declination issues
    slavic_langs = {"ru", "uk", "sk"}
    if pair.from_lang in slavic_langs or pair.to_lang in slavic_langs:
        # Look for common patterns that might indicate wrong declination
        # This is a simple heuristic - not perfect but helpful
        source_words = source.split()
        target_words = target.split()
        
        # Check if word count is very different (might indicate missing/extra words)
        if len(target_words) > len(source_words) * 2:
            warnings.append("⚠️  Target much longer (check declination/grammar)")
        elif len(target_words) < len(source_words) * 0.5:
            warnings.append("⚠️  Target much shorter (missing words?)")
    
    return warnings


logging.basicConfig(
    datefmt="%d/%m/%Y %H:%M",
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console = Console()

# All 12 language directions
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


class ReviewState:
    """Manages review state persistence."""

    def __init__(self, direction: tuple[str, str], data_dir: Path):
        self.direction = direction
        self.data_dir = data_dir
        self.state_file = data_dir / "review_state" / f"{direction[0]}-{direction[1]}.json"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        self.approved_indices: set[int] = set()
        self.rejected_indices: set[int] = set()
        self.current_batch_index: int = 0
        self.edited_pairs: dict[int, dict[str, str]] = {}

        self._load()

    def _load(self) -> None:
        """Load saved state if exists."""
        if self.state_file.exists():
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.approved_indices = set(data.get("approved", []))
                self.rejected_indices = set(data.get("rejected", []))
                self.current_batch_index = data.get("current_batch", 0)
                self.edited_pairs = {
                    int(k): v for k, v in data.get("edited", {}).items()
                }

    def save(self) -> None:
        """Save current state."""
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "approved": list(self.approved_indices),
                    "rejected": list(self.rejected_indices),
                    "current_batch": self.current_batch_index,
                    "edited": {str(k): v for k, v in self.edited_pairs.items()},
                },
                f,
                ensure_ascii=False,
                indent=2,
            )


class PairReviewer:
    """Interactive pair reviewer with Rich UI."""

    def __init__(self, batch_size: int = 4):
        self.batch_size = batch_size
        self.console = Console()
        self.data_dir = Path(__file__).parent

    def load_pairs(self, direction: tuple[str, str]) -> list[Translation]:
        """Load translation pairs from JSON."""
        json_file = self.data_dir / "synthetic_translations_all.json"

        if not json_file.exists():
            console.print(f"[red]File not found: {json_file}[/red]")
            return []

        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Filter by direction
        pairs = [
            Translation(**item)
            for item in data
            if item.get("from_lang") == direction[0]
            and item.get("to_lang") == direction[1]
        ]

        return pairs

    def select_direction(self) -> tuple[str, str] | None:
        """Show direction picker UI."""
        self.console.clear()
        self.console.print(
            Panel.fit(
                "[bold cyan]Translation Pair Review Tool[/bold cyan]",
                border_style="cyan",
            )
        )
        self.console.print()

        table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
        table.add_column("#", style="dim", width=3)
        table.add_column("Direction", justify="left")
        table.add_column("Description", style="dim")

        direction_map = {
            ("en", "ru"): "English → Russian",
            ("ru", "en"): "Russian → English",
            ("en", "uk"): "English → Ukrainian",
            ("uk", "en"): "Ukrainian → English",
            ("en", "sk"): "English → Slovak",
            ("sk", "en"): "Slovak → English",
            ("ru", "uk"): "Russian → Ukrainian",
            ("uk", "ru"): "Ukrainian → Russian",
            ("ru", "sk"): "Russian → Slovak",
            ("sk", "ru"): "Slovak → Russian",
            ("uk", "sk"): "Ukrainian → Slovak",
            ("sk", "uk"): "Slovak → Ukrainian",
        }

        for i, direction in enumerate(ALL_DIRECTIONS, 1):
            table.add_row(
                str(i), f"{direction[0]}-{direction[1]}", direction_map[direction]
            )

        self.console.print(table)
        self.console.print()

        choice = Prompt.ask(
            "[cyan]Select direction (1-12) or 'q' to quit[/cyan]",
            choices=[str(i) for i in range(1, 13)] + ["q"],
        )

        if choice == "q":
            return None

        return ALL_DIRECTIONS[int(choice) - 1]

    def display_batch(
        self,
        pairs: list[Translation],
        batch_index: int,
        state: ReviewState,
    ) -> None:
        """Display a batch of pairs."""
        start_idx = batch_index * self.batch_size
        end_idx = min(start_idx + self.batch_size, len(pairs))
        batch = pairs[start_idx:end_idx]

        self.console.clear()
        self.console.print(
            Panel.fit(
                f"[bold cyan]Batch {batch_index + 1} / {(len(pairs) + self.batch_size - 1) // self.batch_size}[/bold cyan]  "
                f"[dim]({start_idx + 1}-{end_idx} of {len(pairs)})[/dim]",
                border_style="cyan",
            )
        )
        self.console.print()

        for i, pair in enumerate(batch, 1):
            global_idx = start_idx + i - 1
            status = ""
            style = ""

            if global_idx in state.approved_indices:
                status = "✓"
                style = "green"
            elif global_idx in state.rejected_indices:
                status = "✗"
                style = "red"
            else:
                status = " "
                style = "white"

            # Check if edited
            if global_idx in state.edited_pairs:
                edited = state.edited_pairs[global_idx]
                source = edited["source"]
                target = edited["target"]
                edited_mark = "[yellow](edited)[/yellow]"
            else:
                source = pair.source
                target = pair.translated
                edited_mark = ""

            from_lang = (pair.from_lang or "source").upper()
            to_lang = (pair.to_lang or "target").upper()

            # Check for quality warnings
            warnings = check_translation_quality(pair)

            self.console.print(
                f"[{style}]{status} [{i}][/{style}] {edited_mark}",
                style=style,
            )
            self.console.print(f"  [cyan]{from_lang}:[/cyan] {source}")
            self.console.print(f"  [magenta]{to_lang}:[/magenta] {target}")
            
            # Show warnings if any
            if warnings:
                for warning in warnings:
                    self.console.print(f"  [yellow]{warning}[/yellow]")
            
            self.console.print()

    def show_help(self) -> None:
        """Show help panel."""
        help_text = Text()
        help_text.append("Quick Commands:\n\n", style="bold cyan")
        
        help_text.append("  SPACE or ENTER  ", style="green bold")
        help_text.append("→ Approve all & next batch\n")
        
        help_text.append("  x               ", style="red bold")
        help_text.append("→ Reject all & next batch\n\n")
        
        help_text.append("Individual pairs:\n", style="bold yellow")
        help_text.append("  1-4  ", style="yellow bold")
        help_text.append("→ Toggle approve/reject\n")
        help_text.append("  e    ", style="blue bold")
        help_text.append("→ Edit pair (s=source, t=target, b=both)\n\n")
        
        help_text.append("Navigation:\n", style="bold cyan")
        help_text.append("  n / →  ", style="cyan bold")
        help_text.append("→ Next batch\n")
        help_text.append("  p / ←  ", style="cyan bold")
        help_text.append("→ Previous batch\n\n")
        
        help_text.append("Other:\n", style="bold dim")
        help_text.append("  s  ", style="magenta bold")
        help_text.append("→ Statistics\n")
        help_text.append("  q  ", style="dim bold")
        help_text.append("→ Save & quit\n")

        self.console.print(Panel(help_text, title="[bold]Keyboard Shortcuts[/bold]", border_style="cyan"))

    def edit_pair(
        self, pairs: list[Translation], batch_index: int, state: ReviewState
    ) -> None:
        """Edit a specific pair with better UX."""
        pair_num = Prompt.ask("[cyan]Which pair to edit (1-4)?[/cyan]")

        try:
            pair_idx = int(pair_num) - 1
            global_idx = batch_index * self.batch_size + pair_idx

            if global_idx >= len(pairs):
                self.console.print("[red]Invalid pair number[/red]")
                return

            pair = pairs[global_idx]

            # Check if already edited
            if global_idx in state.edited_pairs:
                source = state.edited_pairs[global_idx]["source"]
                target = state.edited_pairs[global_idx]["target"]
            else:
                source = pair.source or ""
                target = pair.translated or ""

            from_lang = pair.from_lang or "source"
            to_lang = pair.to_lang or "target"
            
            # Simple choice: edit source, target, or both
            self.console.print(f"\n[cyan]{from_lang.upper()}:[/cyan] {source}")
            self.console.print(f"[magenta]{to_lang.upper()}:[/magenta] {target}")
            self.console.print()
            
            choice = Prompt.ask(
                "[yellow]Edit:[/yellow]",
                choices=["s", "t", "b", "c"],
                default="c"
            ).lower()
            
            if choice == "c":  # Cancel
                return
            
            final_source = source
            final_target = target
            
            if choice in ["s", "b"]:
                # Edit source - pre-filled with current text
                self.console.print(f"\n[dim]Editing {from_lang.upper()}: (Ctrl+C to cancel)[/dim]")
                try:
                    final_source = Prompt.ask(
                        f"[cyan]{from_lang.upper()}[/cyan]",
                        default=source,
                    ).strip() or source
                except KeyboardInterrupt:
                    self.console.print("\n[yellow]Cancelled[/yellow]")
                    return
            
            if choice in ["t", "b"]:
                # Edit target
                self.console.print(f"\n[dim]Editing {to_lang.upper()}: (Ctrl+C to cancel)[/dim]")
                try:
                    final_target = Prompt.ask(
                        f"[magenta]{to_lang.upper()}[/magenta]",
                        default=target,
                    ).strip() or target
                except KeyboardInterrupt:
                    self.console.print("\n[yellow]Cancelled[/yellow]")
                    return
            
            state.edited_pairs[global_idx] = {
                "source": final_source,
                "target": final_target,
            }

            # Auto-approve edited pairs
            state.approved_indices.add(global_idx)
            state.rejected_indices.discard(global_idx)

            self.console.print("[green]✓ Edited and approved[/green]")

        except ValueError:
            self.console.print("[red]Invalid input[/red]")
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Cancelled[/yellow]")

    def show_stats(self, total: int, state: ReviewState) -> None:
        """Show review statistics."""
        approved = len(state.approved_indices)
        rejected = len(state.rejected_indices)
        pending = total - approved - rejected

        table = Table(title="Review Statistics", box=box.ROUNDED)
        table.add_column("Status", style="bold")
        table.add_column("Count", justify="right")
        table.add_column("Percentage", justify="right")

        table.add_row(
            "[green]Approved[/green]",
            str(approved),
            f"{approved / total * 100:.1f}%",
        )
        table.add_row(
            "[red]Rejected[/red]", str(rejected), f"{rejected / total * 100:.1f}%"
        )
        table.add_row(
            "[yellow]Pending[/yellow]", str(pending), f"{pending / total * 100:.1f}%"
        )
        table.add_row("[cyan]Total[/cyan]", str(total), "100.0%", style="bold")

        self.console.print()
        self.console.print(table)
        self.console.print()

    def review_direction(self, direction: tuple[str, str]) -> None:
        """Review pairs for a specific direction."""
        pairs = self.load_pairs(direction)

        if not pairs:
            self.console.print(
                f"[yellow]No pairs found for {direction[0]}-{direction[1]}[/yellow]"
            )
            return

        state = ReviewState(direction, self.data_dir)
        batch_index = state.current_batch_index
        total_batches = (len(pairs) + self.batch_size - 1) // self.batch_size

        while True:
            self.display_batch(pairs, batch_index, state)
            self.show_help()

            start_idx = batch_index * self.batch_size
            end_idx = min(start_idx + self.batch_size, len(pairs))

            action = Prompt.ask("[cyan]›[/cyan]").lower()

            # SPACE or ENTER = approve all & next
            if action == "" or action == " ":
                for i in range(start_idx, end_idx):
                    state.approved_indices.add(i)
                    state.rejected_indices.discard(i)
                if batch_index < total_batches - 1:
                    batch_index += 1
                    state.current_batch_index = batch_index
                else:
                    self.console.print("[yellow]Last batch - press 'q' to finish[/yellow]")

            elif action == "x":
                # Reject all & next
                for i in range(start_idx, end_idx):
                    state.rejected_indices.add(i)
                    state.approved_indices.discard(i)
                if batch_index < total_batches - 1:
                    batch_index += 1
                    state.current_batch_index = batch_index

            elif action in ["1", "2", "3", "4"]:
                # Toggle individual pair
                pair_idx = int(action) - 1
                global_idx = start_idx + pair_idx

                if global_idx < len(pairs):
                    if global_idx in state.approved_indices:
                        state.approved_indices.remove(global_idx)
                        state.rejected_indices.add(global_idx)
                    elif global_idx in state.rejected_indices:
                        state.rejected_indices.remove(global_idx)
                    else:
                        state.approved_indices.add(global_idx)

            elif action == "e":
                self.edit_pair(pairs, batch_index, state)

            elif action in ["n", "→"]:
                if batch_index < total_batches - 1:
                    batch_index += 1
                    state.current_batch_index = batch_index
                else:
                    self.console.print("[yellow]Already at last batch[/yellow]")

            elif action in ["p", "←"]:
                if batch_index > 0:
                    batch_index -= 1
                    state.current_batch_index = batch_index
                else:
                    self.console.print("[yellow]Already at first batch[/yellow]")

            elif action == "s":
                self.show_stats(len(pairs), state)
                Prompt.ask("[dim]Press Enter to continue[/dim]")

            elif action == "h" or action == "?":
                continue

            elif action == "q":
                state.save()
                self.save_approved(pairs, direction, state)
                break

            # Auto-save progress
            state.save()

    def save_approved(
        self, pairs: list[Translation], direction: tuple[str, str], state: ReviewState
    ) -> None:
        """Save approved pairs to TSV."""
        approved_dir = self.data_dir / "automl" / "approved"
        rejected_dir = self.data_dir / "automl" / "rejected"
        approved_dir.mkdir(parents=True, exist_ok=True)
        rejected_dir.mkdir(parents=True, exist_ok=True)

        # Save approved
        approved_file = approved_dir / f"{direction[0]}-{direction[1]}.tsv"
        with open(approved_file, "w", encoding="utf-8") as f:
            for idx in sorted(state.approved_indices):
                pair = pairs[idx]
                if idx in state.edited_pairs:
                    source = state.edited_pairs[idx]["source"]
                    target = state.edited_pairs[idx]["target"]
                else:
                    source = pair.source
                    target = pair.translated
                f.write(f"{source}\t{target}\n")

        # Save rejected
        rejected_file = rejected_dir / f"{direction[0]}-{direction[1]}.tsv"
        with open(rejected_file, "w", encoding="utf-8") as f:
            for idx in sorted(state.rejected_indices):
                pair = pairs[idx]
                f.write(f"{pair.source}\t{pair.translated}\n")

        self.console.print(
            f"\n[green]✓ Saved {len(state.approved_indices)} approved pairs to {approved_file}[/green]"
        )
        self.console.print(
            f"[red]✗ Saved {len(state.rejected_indices)} rejected pairs to {rejected_file}[/red]"
        )

    def run(self) -> None:
        """Main entry point."""
        while True:
            direction = self.select_direction()
            if direction is None:
                self.console.print("[cyan]Goodbye![/cyan]")
                break

            self.review_direction(direction)

            if not Confirm.ask("\n[cyan]Review another direction?[/cyan]"):
                break


def main() -> None:
    """CLI entry point."""
    reviewer = PairReviewer(batch_size=10)
    reviewer.run()


if __name__ == "__main__":
    main()
