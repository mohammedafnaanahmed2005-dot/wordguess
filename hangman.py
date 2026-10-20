"""Console entry point and replay loop for Hangman."""

from pathlib import Path

from display import render_status
from game_logic import GuessResult, HangmanGame
from word_manager import (
    DEFAULT_WORD_LIST,
    WordListError,
    choose_random_word,
    load_words,
)


WORD_LIST_PATH = (
    Path(__file__).resolve().parent
    / "data"
    / "google-10000-english-no-swears.txt"
)


def play_round(secret_word: str) -> None:
    """Run one round until the player wins or uses all attempts."""
    game = HangmanGame(secret_word)
    print("\nNew round! Guess the secret word, one letter at a time.")
    print(
        render_status(
            game.secret_word,
            game.guessed_letters,
            game.incorrect_letters,
            game.attempts_remaining,
        )
    )

    while not game.is_over:
        result = game.guess(input("Your guess: "))
        if result is GuessResult.INVALID:
            print("Enter exactly one English letter (A-Z).")
            continue
        if result is GuessResult.DUPLICATE:
            print("You already guessed that letter. Try another.")
            continue

        if result is GuessResult.CORRECT:
            print("Good guess!")
        elif result is GuessResult.INCORRECT:
            print("That letter is not in the word.")

        print(
            render_status(
                game.secret_word,
                game.guessed_letters,
                game.incorrect_letters,
                game.attempts_remaining,
            )
        )

    if game.is_won:
        print("You win!")
    else:
        print(f"You ran out of attempts. The word was: {game.secret_word}")


def ask_to_play_again() -> bool:
    """Prompt until the player enters yes or no."""
    while True:
        response = input("Play again? (y/n): ").strip().lower()
        if response in {"y", "yes"}:
            return True
        if response in {"n", "no"}:
            return False
        print("Please enter y or n.")


def main() -> None:
    """Load the word list and run rounds until the player quits."""
    try:
        words = load_words(WORD_LIST_PATH)
    except WordListError as error:
        print(f"Word-list error: {error}")
        print("Using the built-in fallback word list for this session.")
        words = list(DEFAULT_WORD_LIST)

    while True:
        try:
            play_round(choose_random_word(words))
            if not ask_to_play_again():
                print("Thanks for playing!")
                return
        except EOFError:
            print("\nInput closed. Thanks for playing!")
            return
        except KeyboardInterrupt:
            print("\nGame interrupted. Thanks for playing!")
            return


if __name__ == "__main__":
    main()
