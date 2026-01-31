#!/usr/bin/env python3
"""Interactive TUI client for dekomposit translation service."""

import asyncio
import logging
import sys
from dataclasses import dataclass
from typing import Optional

# Suppress logging before importing modules that configure it
logging.disable(logging.CRITICAL)

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt
from rich.style import Style

from dekomposit.llm.base_client import Client
from dekomposit.llm.prompts import TranslationPrompt
from dekomposit.llm.types import Language, Translation


console = Console()


@dataclass
class TokenUsage:
    """Token usage from LLM response."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class TranslationResult:
    """Translation with token usage."""
    translation: Translation
    usage: TokenUsage


class ChatMessage:
    """Represents a message in the chat history."""

    def __init__(self, role: str, content: str, result: Optional[TranslationResult] = None):
        self.role = role
        self.content = content
        self.result = result


class TranslationTUI:
    """Interactive TUI for translation."""

    def __init__(self):
        self.source_lang: Language = Language.EN
        self.target_lang: Language = Language.UK
        self.history: list[ChatMessage] = []
        self.running = True

    def display_header(self):
        """Display the application header."""
        console.clear()
        header = Text()
        header.append("dekomposit", style="bold magenta")
        header.append(" - Translation CLI", style="dim")
        console.print(Panel(header, border_style="magenta"))
        console.print(
            f"[dim]Source:[/dim] [cyan]{self.source_lang.value}[/cyan]  "
            f"[dim]Target:[/dim] [cyan]{self.target_lang.value}[/cyan]  "
            f"[dim]Commands:[/dim] [yellow]/lang[/yellow] [yellow]/clear[/yellow] [yellow]/exit[/yellow]\n"
        )

    def display_history(self):
        """Display chat history."""
        for msg in self.history:
            if msg.role == "user":
                console.print(f"[bold blue]>[/bold blue] {msg.content}")
            elif msg.role == "assistant" and msg.result:
                self._display_translation(msg.result.translation)
                self._display_usage(msg.result.usage)
            elif msg.role == "system":
                console.print(f"[dim italic]{msg.content}[/dim italic]")
            console.print()

    def _display_translation(self, translation: Translation):
        """Display a translation result."""
        table = Table(
            show_header=True,
            header_style="bold green",
            border_style="dim",
            expand=False,
            padding=(0, 1),
        )
        table.add_column("Source", style="white")
        table.add_column("Translation", style="cyan")

        for phrase in translation.translation:
            table.add_row(phrase.phrase_source, phrase.phrase_translated)

        console.print(table)

    def _display_usage(self, usage: TokenUsage):
        """Display token usage."""
        console.print(
            f"[dim]tokens: {usage.prompt_tokens} in / {usage.completion_tokens} out / {usage.total_tokens} total[/dim]"
        )

    def select_language(self, prompt_text: str, current: Language) -> Language:
        """Interactive language selection."""
        languages = list(Language)

        console.print(f"\n[bold]{prompt_text}[/bold]")
        console.print("[dim]Available languages:[/dim]")

        # Display languages in columns
        cols = 4
        for i in range(0, len(languages), cols):
            row = languages[i:i + cols]
            line = "  ".join(
                f"[yellow]{lang.name}[/yellow]=[dim]{lang.value}[/dim]"
                for lang in row
            )
            console.print(f"  {line}")

        console.print(f"\n[dim]Current: {current.name} ({current.value})[/dim]")

        while True:
            choice = Prompt.ask(
                "Enter language code (e.g. EN, UK)",
                default=current.name
            ).strip().upper()

            try:
                return Language[choice]
            except KeyError:
                console.print(f"[red]Invalid language code: {choice}[/red]")

    def handle_command(self, cmd: str) -> bool:
        """Handle special commands. Returns True if command was handled."""
        cmd = cmd.strip().lower()

        if cmd == "/exit" or cmd == "/quit" or cmd == "/q":
            self.running = False
            console.print("[dim]Goodbye![/dim]")
            return True

        if cmd == "/clear":
            self.history.clear()
            self.display_header()
            console.print("[dim]Chat cleared.[/dim]\n")
            return True

        if cmd == "/lang":
            self.source_lang = self.select_language(
                "Select source language:", self.source_lang
            )
            self.target_lang = self.select_language(
                "Select target language:", self.target_lang
            )
            self.history.append(ChatMessage(
                "system",
                f"Languages changed: {self.source_lang.value} -> {self.target_lang.value}"
            ))
            self.display_header()
            self.display_history()
            return True

        if cmd == "/help" or cmd == "/?":
            console.print(Panel(
                "[yellow]/lang[/yellow]  - Change source/target languages\n"
                "[yellow]/clear[/yellow] - Clear chat history\n"
                "[yellow]/exit[/yellow]  - Exit the application\n"
                "[yellow]/help[/yellow]  - Show this help",
                title="Commands",
                border_style="dim"
            ))
            return True

        return False

    async def translate_text(self, text: str) -> Optional[TranslationResult]:
        """Translate text with loading indicator."""
        try:
            with console.status("[cyan]Translating...", spinner="dots"):
                prompt = TranslationPrompt(self.source_lang, self.target_lang)
                prompt_text = prompt.get_prompt(text)

                client = Client()
                response = await client.request(
                    messages=[
                        {"role": "system", "content": prompt.system_prompt},
                        {"role": "user", "content": prompt_text},
                    ],
                    return_format=Translation,
                )

                usage = TokenUsage(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                )
                translation = response.choices[0].message.parsed

            return TranslationResult(translation=translation, usage=usage)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return None

    async def run(self):
        """Main TUI loop."""
        self.display_header()

        # Initial language selection
        console.print("[dim]Press Enter to use defaults or type /lang to change[/dim]\n")

        while self.running:
            try:
                user_input = Prompt.ask("[bold blue]>[/bold blue]").strip()

                if not user_input:
                    continue

                # Check for commands
                if user_input.startswith("/"):
                    if self.handle_command(user_input):
                        continue
                    else:
                        console.print(f"[red]Unknown command: {user_input}[/red]")
                        console.print("[dim]Type /help for available commands[/dim]\n")
                        continue

                # Add user message to history
                self.history.append(ChatMessage("user", user_input))

                # Translate (only current input, not history)
                result = await self.translate_text(user_input)

                if result:
                    self.history.append(ChatMessage("assistant", "", result))
                    self._display_translation(result.translation)
                    self._display_usage(result.usage)

                console.print()

            except KeyboardInterrupt:
                console.print("\n[dim]Use /exit to quit[/dim]")
            except EOFError:
                self.running = False


def main():
    """Entry point for the CLI."""
    try:
        asyncio.run(TranslationTUI().run())
    except KeyboardInterrupt:
        console.print("\n[dim]Bye![/dim]")
        sys.exit(0)


if __name__ == "__main__":
    main()
