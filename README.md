# Wordplay Hangman

A polished, responsive browser-based Hangman game with a Python standard-library
web server, HTML, Tailwind utilities, and JavaScript. The game itself works
without installing Python packages. The stylesheet includes local presentation
rules, so the interface remains usable when the optional Tailwind CDN is
unavailable; loading Tailwind's utility layer requires internet access.

## Setup

The supplied guessing-word list is included at:

```text
data/google-10000-english-no-swears.txt
```

The web server reads this file relative to `web_app.py`, so it can be launched
from any working directory. Each line contains one word. Words shorter than
four characters and entries containing non-English or non-alphabetic characters
are ignored; valid English A-Z words are converted to lowercase.

If the word-list file is missing, unreadable, empty, or contains no usable
words, the server prints a clear warning and uses a small built-in fallback
list. The attached list is stored locally and is never fetched from the
internet.

## Run the browser game

From PowerShell in the project directory:

```powershell
py -3 .\web_app.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser. The game
allows six incorrect guesses, supports both the on-screen and physical
keyboards, and lets you start another round without restarting the server. If
you get stuck, the **Hint** button reveals one letter of the word for you, up to
three times per round; hints never cost an attempt. Active secret words remain
on the server and are only revealed when a round ends.

Press `Ctrl+C` in PowerShell to stop the server.

The original console version remains available:

```powershell
py -3 .\hangman.py
```

## Run the tests

From PowerShell in the project directory:

```powershell
py -3 -m unittest discover -s .\tests -v
```

## Project files

- `hangman.py` — application entry point and replay loop
- `word_manager.py` — word-list loading, filtering, fallback, and random choice
- `display.py` — gallows stages and round status formatting
- `game_logic.py` — deterministic guessing rules and outcome tracking
- `web_app.py` — Python HTTP server and session-based game API
- `templates/index.html` — accessible browser game structure
- `static/app.js` — keyboard input and game interaction
- `static/styles.css` — responsive game interface and Tailwind fallback styling
- `data/` — the supplied local guessing-word list
- `tests/` — unit tests for game logic, word management, and web state
