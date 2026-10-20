"""Rendering helpers for the Hangman console interface."""

from collections.abc import Collection


GALLOWS_STAGES = (
    "  +---+\n"
    "  |   |\n"
    "      |\n"
    "      |\n"
    "      |\n"
    "      |\n"
    "=========",
    "  +---+\n"
    "  |   |\n"
    "  O   |\n"
    "      |\n"
    "      |\n"
    "      |\n"
    "=========",
    "  +---+\n"
    "  |   |\n"
    "  O   |\n"
    "  |   |\n"
    "      |\n"
    "      |\n"
    "=========",
    "  +---+\n"
    "  |   |\n"
    "  O   |\n"
    " /|   |\n"
    "      |\n"
    "      |\n"
    "=========",
    "  +---+\n"
    "  |   |\n"
    "  O   |\n"
    " /|\\  |\n"
    "      |\n"
    "      |\n"
    "=========",
    "  +---+\n"
    "  |   |\n"
    "  O   |\n"
    " /|\\  |\n"
    " /    |\n"
    "      |\n"
    "=========",
    "  +---+\n"
    "  |   |\n"
    "  O   |\n"
    " /|\\  |\n"
    " / \\  |\n"
    "      |\n"
    "=========",
)


def render_masked_word(secret_word: str, guessed_letters: Collection[str]) -> str:
    """Render guessed positions and hide all other letters with underscores."""
    return " ".join(
        letter if letter in guessed_letters else "_" for letter in secret_word
    )


def render_status(
    secret_word: str,
    guessed_letters: Collection[str],
    incorrect_letters: Collection[str],
    attempts_remaining: int,
) -> str:
    """Build the gallows and current round details for display."""
    stage = min(len(incorrect_letters), len(GALLOWS_STAGES) - 1)
    return (
        f"{GALLOWS_STAGES[stage]}\n\n"
        f"Word: {render_masked_word(secret_word, guessed_letters)}\n"
        f"Guessed letters: {format_letters(guessed_letters)}\n"
        f"Incorrect letters: {format_letters(incorrect_letters)}\n"
        f"Attempts remaining: {attempts_remaining}"
    )


def format_letters(letters: Collection[str]) -> str:
    """Format a set of letters consistently, showing a dash when it is empty."""
    return ", ".join(sorted(letters)) if letters else "-"
