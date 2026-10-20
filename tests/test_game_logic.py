"""Unit tests for Hangman guessing rules and round outcomes."""

import unittest

from display import GALLOWS_STAGES, render_masked_word
from game_logic import (
    MAX_HINTS,
    MAX_INCORRECT_GUESSES,
    GuessResult,
    HangmanGame,
)


class HangmanGameTests(unittest.TestCase):
    def test_masked_word_reveals_every_occurrence_and_has_seven_stages(self) -> None:
        self.assertEqual(render_masked_word("banana", {"a"}), "_ a _ a _ a")
        self.assertEqual(len(GALLOWS_STAGES), MAX_INCORRECT_GUESSES + 1)

    def test_correct_guess_is_normalized_and_reveals_repeated_letters(self) -> None:
        game = HangmanGame("banana")

        result = game.guess("A")

        self.assertIs(result, GuessResult.CORRECT)
        self.assertEqual(game.guessed_letters, {"a"})
        self.assertEqual(game.attempts_remaining, MAX_INCORRECT_GUESSES)

    def test_invalid_guesses_do_not_change_state(self) -> None:
        game = HangmanGame("hangman")

        for guess in ("", "ab", "3", "!", "é"):
            with self.subTest(guess=guess):
                self.assertIs(game.guess(guess), GuessResult.INVALID)
                self.assertEqual(game.guessed_letters, set())
                self.assertEqual(game.incorrect_letters, set())
                self.assertEqual(game.attempts_remaining, MAX_INCORRECT_GUESSES)

    def test_duplicate_guess_does_not_deduct_attempt(self) -> None:
        game = HangmanGame("hangman")
        self.assertIs(game.guess("z"), GuessResult.INCORRECT)

        result = game.guess("Z")

        self.assertIs(result, GuessResult.DUPLICATE)
        self.assertEqual(game.incorrect_letters, {"z"})
        self.assertEqual(game.attempts_remaining, MAX_INCORRECT_GUESSES - 1)

    def test_each_new_incorrect_guess_deducts_one_attempt(self) -> None:
        game = HangmanGame("hangman")

        for index, letter in enumerate("qzxjkv", start=1):
            with self.subTest(letter=letter):
                self.assertIs(game.guess(letter), GuessResult.INCORRECT)
                self.assertEqual(
                    game.attempts_remaining, MAX_INCORRECT_GUESSES - index
                )

    def test_win_ends_round_and_further_guesses_have_no_effect(self) -> None:
        game = HangmanGame("abca")

        game.guess("a")
        game.guess("b")
        game.guess("c")

        self.assertTrue(game.is_won)
        self.assertTrue(game.is_over)
        self.assertIs(game.guess("z"), GuessResult.ROUND_OVER)
        self.assertEqual(game.attempts_remaining, MAX_INCORRECT_GUESSES)

    def test_six_incorrect_guesses_lose_round(self) -> None:
        game = HangmanGame("hangman")

        for letter in "qzxjkv":
            game.guess(letter)

        self.assertTrue(game.is_lost)
        self.assertTrue(game.is_over)
        self.assertEqual(game.attempts_remaining, 0)
        self.assertIs(game.guess("a"), GuessResult.ROUND_OVER)

    def test_secret_word_must_be_alphabetic(self) -> None:
        for word in ("bad-word", "caf\u00e9"):
            with self.subTest(word=word), self.assertRaises(ValueError):
                HangmanGame(word)
    
    def test_hint_reveals_a_correct_letter_without_costing_an_attempt(self) -> None:
        game = HangmanGame("banana")
    
        letter, result = game.hint()
    
        self.assertIn(letter, set("banana"))
        self.assertIs(result, GuessResult.CORRECT)
        self.assertIn(letter, game.guessed_letters)
        self.assertEqual(game.attempts_remaining, MAX_INCORRECT_GUESSES)
        self.assertEqual(game.hints_remaining, MAX_HINTS - 1)
    
    def test_hints_are_limited_and_reset_only_on_a_new_word(self) -> None:
        game = HangmanGame("cat")
    
        for _ in range(MAX_HINTS):
            self.assertIsNotNone(game.hint())
    
        self.assertEqual(game.hints_remaining, 0)
        self.assertIsNone(game.hint())
    
    def test_hint_returns_none_when_round_is_over(self) -> None:
        game = HangmanGame("hi")
        for letter in "hi":
            game.guess(letter)
    
        self.assertTrue(game.is_over)
        self.assertIsNone(game.hint())


if __name__ == "__main__":
    unittest.main()
