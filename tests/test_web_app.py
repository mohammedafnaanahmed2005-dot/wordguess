"""Tests for private game state and browser-session handling."""

import unittest
from unittest.mock import patch

from game_logic import GuessResult
from web_app import HangmanWebApp, game_payload


class WebAppTests(unittest.TestCase):
    def test_active_game_payload_does_not_reveal_the_secret(self) -> None:
        game = HangmanWebApp(["secret"]).create_session()[1]

        payload = game_payload(game)

        self.assertEqual(payload["status"], "playing")
        self.assertNotIn("word", payload)
        self.assertEqual(payload["masked_word"], [None] * 6)

    def test_finished_game_payload_reveals_the_answer(self) -> None:
        game = HangmanWebApp(["cat"]).create_session()[1]
        for letter in "cat":
            game.guess(letter)

        payload = game_payload(game, GuessResult.CORRECT)

        self.assertEqual(payload["status"], "won")
        self.assertEqual(payload["word"], "cat")
        self.assertEqual(payload["masked_word"], list("cat"))

    def test_session_is_replaced_by_new_game(self) -> None:
        app = HangmanWebApp(["first", "second"])
        with patch("web_app.choose_random_word", side_effect=["first", "second"]):
            session_id, original_game = app.create_session()
            new_game = app.start_new_game(session_id)

        self.assertIsNot(original_game, new_game)
        self.assertEqual(app.get_or_create_session(session_id)[1], new_game)
        self.assertEqual(new_game.secret_word, "second")

    def test_unknown_session_id_creates_a_fresh_session(self) -> None:
        app = HangmanWebApp(["secret"])

        session_id, game = app.get_or_create_session("not-a-valid-session")

        self.assertEqual(len(session_id), 32)
        self.assertEqual(game.secret_word, "secret")


if __name__ == "__main__":
    unittest.main()
