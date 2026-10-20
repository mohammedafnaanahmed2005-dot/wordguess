"""Small standard-library HTTP server for the Hangman browser game."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.cookies import CookieError, SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
from typing import Any
from uuid import uuid4

from game_logic import MAX_HINTS, MAX_INCORRECT_GUESSES, GuessResult, HangmanGame
from word_manager import DEFAULT_WORD_LIST, WordListError, choose_random_word, load_words


PROJECT_DIR = Path(__file__).resolve().parent
WORD_LIST_PATH = PROJECT_DIR / "data" / "google-10000-english-no-swears.txt"
COOKIE_NAME = "hangman_session"
MAX_REQUEST_SIZE = 1024
MAX_SESSIONS = 1024
SESSION_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
STATIC_FILES = {
    "/static/app.js": (PROJECT_DIR / "static" / "app.js", "text/javascript"),
    "/static/styles.css": (PROJECT_DIR / "static" / "styles.css", "text/css"),
}


class HangmanWebApp:
    """Own word choices and independent game state for browser sessions."""

    def __init__(self, words: list[str]) -> None:
        if not words:
            raise ValueError("The web app requires at least one usable word.")
        self.words = words
        self.sessions: dict[str, HangmanGame] = {}

    def create_session(self) -> tuple[str, HangmanGame]:
        """Create a fresh session with a randomly selected secret word."""
        session_id = uuid4().hex
        game = HangmanGame(choose_random_word(self.words))
        self.sessions[session_id] = game
        self._evict_oldest_sessions(protected_id=session_id)
        return session_id, game

    def _evict_oldest_sessions(self, protected_id: str) -> None:
        """Drop the oldest sessions once the store exceeds its size cap."""
        for stale_id in list(self.sessions):
            if len(self.sessions) <= MAX_SESSIONS:
                break
            if stale_id != protected_id:
                self.sessions.pop(stale_id, None)

    def get_or_create_session(self, session_id: str | None) -> tuple[str, HangmanGame]:
        """Return the current game, replacing unknown session identifiers."""
        if session_id and SESSION_ID_PATTERN.fullmatch(session_id):
            game = self.sessions.get(session_id)
            if game is not None:
                return session_id, game
        return self.create_session()

    def start_new_game(self, session_id: str) -> HangmanGame:
        """Replace the current game in a valid session."""
        game = HangmanGame(choose_random_word(self.words))
        self.sessions[session_id] = game
        return game


def game_payload(
    game: HangmanGame,
    result: GuessResult | None = None,
    hint_letter: str | None = None,
) -> dict[str, Any]:
    """Serialize public game state without exposing an active secret word."""
    status = "won" if game.is_won else "lost" if game.is_lost else "playing"
    payload: dict[str, Any] = {
        "status": status,
        "masked_word": [
            letter if letter in game.guessed_letters else None
            for letter in game.secret_word
        ],
        "guessed_letters": sorted(game.guessed_letters),
        "incorrect_letters": sorted(game.incorrect_letters),
        "attempts_remaining": game.attempts_remaining,
        "max_attempts": MAX_INCORRECT_GUESSES,
        "hints_remaining": game.hints_remaining,
        "max_hints": MAX_HINTS,
        "result": result.value if result is not None else None,
    }
    if hint_letter is not None:
        payload["hint"] = hint_letter
    if game.is_over:
        payload["word"] = game.secret_word
    return payload


def make_request_handler(app: HangmanWebApp) -> type[BaseHTTPRequestHandler]:
    """Create a request handler bound to the in-memory game service."""

    class HangmanRequestHandler(BaseHTTPRequestHandler):
        server_version = "WordplayHangman/1.0"

        def do_GET(self) -> None:
            if self.path == "/":
                session_id, _ = app.get_or_create_session(self._session_cookie())
                self._send_file(
                    PROJECT_DIR / "templates" / "index.html",
                    "text/html",
                    session_id,
                )
                return

            if self.path == "/api/state":
                session_id, game = app.get_or_create_session(self._session_cookie())
                self._send_json(game_payload(game), session_id)
                return

            static_file = STATIC_FILES.get(self.path)
            if static_file:
                self._send_file(static_file[0], static_file[1])
                return

            self._send_json(
                {"error": "The requested route was not found."},
                status=HTTPStatus.NOT_FOUND,
            )

        def do_POST(self) -> None:
            session_id, game = app.get_or_create_session(self._session_cookie())
            if self.path == "/api/new":
                game = app.start_new_game(session_id)
                self._send_json(game_payload(game), session_id)
                return

            if self.path == "/api/hint":
                hint = game.hint()
                if hint is None:
                    self._send_json({**game_payload(game), "hint": None}, session_id)
                    return
                letter, result = hint
                self._send_json(
                    game_payload(game, result, hint_letter=letter), session_id
                )
                return

            if self.path != "/api/guess":
                self._send_json(
                    {"error": "The requested route was not found."},
                    status=HTTPStatus.NOT_FOUND,
                )
                return

            try:
                body = self._read_json_body()
            except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as error:
                self._send_json(
                    {"error": f"Invalid request: {error}"},
                    status=HTTPStatus.BAD_REQUEST,
                    session_id=session_id,
                )
                return

            guess = body.get("letter")
            if not isinstance(guess, str):
                self._send_json(
                    {"error": "The request must include a letter string."},
                    status=HTTPStatus.BAD_REQUEST,
                    session_id=session_id,
                )
                return

            result = game.guess(guess)
            self._send_json(game_payload(game, result), session_id)

        def log_message(self, format_string: str, *args: object) -> None:
            """Keep routine request logging concise and useful in the terminal."""
            super().log_message(format_string, *args)

        def _session_cookie(self) -> str | None:
            cookie_header = self.headers.get("Cookie")
            if not cookie_header:
                return None
            cookie = SimpleCookie()
            try:
                cookie.load(cookie_header)
            except CookieError:
                return None
            morsel = cookie.get(COOKIE_NAME)
            return morsel.value if morsel else None

        def _read_json_body(self) -> dict[str, Any]:
            content_length = self.headers.get("Content-Length")
            if content_length is None:
                raise ValueError("Content-Length is required.")
            try:
                length = int(content_length)
            except ValueError as error:
                raise ValueError("Content-Length must be a number.") from error
            if length < 0 or length > MAX_REQUEST_SIZE:
                raise ValueError("Request body is too large.")
            raw_body = self.rfile.read(length)
            parsed = json.loads(raw_body.decode("utf-8"))
            if not isinstance(parsed, dict):
                raise ValueError("A JSON object is required.")
            return parsed

        def _send_file(
            self, path: Path, content_type: str, session_id: str | None = None
        ) -> None:
            try:
                content = path.read_bytes()
            except OSError:
                self._send_json(
                    {"error": "A required game asset could not be loaded."},
                    status=HTTPStatus.INTERNAL_SERVER_ERROR,
                )
                return
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self._security_headers()
            if session_id:
                self.send_header(
                    "Set-Cookie",
                    f"{COOKIE_NAME}={session_id}; Path=/; HttpOnly; SameSite=Lax",
                )
            self.end_headers()
            self.wfile.write(content)

        def _send_json(
            self,
            payload: dict[str, Any],
            session_id: str | None = None,
            status: HTTPStatus = HTTPStatus.OK,
        ) -> None:
            content = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self._security_headers()
            if session_id:
                self.send_header(
                    "Set-Cookie",
                    f"{COOKIE_NAME}={session_id}; Path=/; HttpOnly; SameSite=Lax",
                )
            self.end_headers()
            self.wfile.write(content)

        def _security_headers(self) -> None:
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Cache-Control", "no-store")

    return HangmanRequestHandler


def load_game_words() -> list[str]:
    """Load the supplied list or use the built-in fallback with a warning."""
    try:
        words = load_words(WORD_LIST_PATH)
        print(f"Loaded {len(words):,} valid words from {WORD_LIST_PATH}.")
        return words
    except WordListError as error:
        print(f"Word-list warning: {error}")
        print("Using the built-in fallback word list.")
        return list(DEFAULT_WORD_LIST)


def main() -> None:
    """Start the local browser game."""
    app = HangmanWebApp(load_game_words())
    server = ThreadingHTTPServer(("127.0.0.1", 8000), make_request_handler(app))
    print("Wordplay Hangman is ready at http://127.0.0.1:8000")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down Wordplay Hangman.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
