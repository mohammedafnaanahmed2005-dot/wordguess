"""Unit tests for Hangman word-list loading and selection."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from word_manager import WordListError, choose_random_word, load_words


class WordManagerTests(unittest.TestCase):
    def test_load_words_filters_and_normalizes_entries(self) -> None:
        contents = "Cat\nPython\nabc\nhas-hyphen\n12345\ncafé\n"
        with tempfile.TemporaryDirectory() as directory:
            word_file = Path(directory) / "words.txt"
            word_file.write_text(contents, encoding="utf-8")

            self.assertEqual(load_words(word_file), ["python"])

    def test_missing_file_raises_clear_word_list_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing_file = Path(directory) / "missing.txt"

            with self.assertRaisesRegex(WordListError, "Cannot read word list"):
                load_words(missing_file)

    def test_empty_or_unusable_file_raises_word_list_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            word_file = Path(directory) / "empty.txt"
            word_file.write_text("cat\nfour!\n1234\n", encoding="utf-8")

            with self.assertRaisesRegex(WordListError, "no usable words"):
                load_words(word_file)

    def test_unreadable_file_raises_word_list_error(self) -> None:
        with patch.object(Path, "read_text", side_effect=PermissionError("denied")):
            with self.assertRaisesRegex(WordListError, "denied"):
                load_words("restricted.txt")

    def test_random_word_selection_uses_random_choice(self) -> None:
        words = ["python", "hangman"]

        with patch("word_manager.random.choice", return_value="hangman") as choice:
            self.assertEqual(choose_random_word(words), "hangman")

        choice.assert_called_once_with(words)

    def test_empty_sequence_cannot_be_selected_from(self) -> None:
        with self.assertRaisesRegex(WordListError, "empty word list"):
            choose_random_word([])


if __name__ == "__main__":
    unittest.main()
