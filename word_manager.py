"""Load and select words for Hangman."""

from pathlib import Path
import random
from collections.abc import Sequence


DEFAULT_WORD_LIST = (
    "hangman",
    "python",
    "computer",
    "developer",
    "programming",
)


class WordListError(Exception):
    """Raised when a word list cannot provide any usable words."""


def load_words(file_path: str | Path) -> list[str]:
    """Load, normalize, and filter alphabetic words from a text file."""
    path = Path(file_path)
    try:
        contents = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise WordListError(f"Cannot read word list '{path}': {error}") from error

    words = []
    for line in contents.splitlines():
        word = line.strip()
        if len(word) >= 4 and word.isascii() and word.isalpha():
            words.append(word.lower())
    if not words:
        raise WordListError(f"Word list '{path}' is empty or has no usable words.")
    return words


def choose_random_word(words: Sequence[str]) -> str:
    """Choose a secret word uniformly from a non-empty sequence."""
    if not words:
        raise WordListError("Cannot choose a secret word from an empty word list.")
    return random.choice(words)
