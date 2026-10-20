"""State and rules for a single Hangman round."""

from enum import Enum
import random


MAX_INCORRECT_GUESSES = 6
MAX_HINTS = 3


class GuessResult(Enum):
    """Possible outcomes of submitting a guess."""

    INVALID = "invalid"
    DUPLICATE = "duplicate"
    CORRECT = "correct"
    INCORRECT = "incorrect"
    ROUND_OVER = "round_over"


class HangmanGame:
    """Manage guesses and outcomes for one secret word."""

    def __init__(self, secret_word: str) -> None:
        normalized_word = secret_word.lower()
        if (
            not normalized_word
            or not normalized_word.isascii()
            or not normalized_word.isalpha()
        ):
            raise ValueError("The secret word must contain English letters only.")

        self.secret_word = normalized_word
        self.guessed_letters: set[str] = set()
        self.incorrect_letters: set[str] = set()
        self.hints_used = 0

    @property
    def hints_remaining(self) -> int:
        """Return the number of hints still available this round."""
        return MAX_HINTS - self.hints_used

    @property
    def attempts_remaining(self) -> int:
        """Return the number of incorrect guesses remaining."""
        return MAX_INCORRECT_GUESSES - len(self.incorrect_letters)

    @property
    def is_won(self) -> bool:
        """Return whether every letter in the secret word has been guessed."""
        return all(letter in self.guessed_letters for letter in self.secret_word)

    @property
    def is_lost(self) -> bool:
        """Return whether no incorrect guesses remain."""
        return self.attempts_remaining == 0

    @property
    def is_over(self) -> bool:
        """Return whether the round has been won or lost."""
        return self.is_won or self.is_lost

    def guess(self, raw_guess: str) -> GuessResult:
        """Validate and apply one guess without changing state on invalid input."""
        if self.is_over:
            return GuessResult.ROUND_OVER

        guess = raw_guess.strip().lower()
        if len(guess) != 1 or not guess.isascii() or not guess.isalpha():
            return GuessResult.INVALID
        if guess in self.guessed_letters:
            return GuessResult.DUPLICATE

        self.guessed_letters.add(guess)
        if guess in self.secret_word:
            return GuessResult.CORRECT

        self.incorrect_letters.add(guess)
        return GuessResult.INCORRECT

    def hint(self) -> tuple[str, GuessResult] | None:
        """Reveal one still-hidden letter of the secret word as a hint.

        Consumes one of the round's hints and never costs an attempt. Returns
        ``None`` when the round is over, hints are exhausted, or no hidden
        letters remain.
        """
        if self.is_over or self.hints_remaining <= 0:
            return None
        hidden = {
            letter for letter in self.secret_word
            if letter not in self.guessed_letters
        }
        if not hidden:
            return None
        letter = random.choice(sorted(hidden))
        self.hints_used += 1
        return letter, self.guess(letter)
