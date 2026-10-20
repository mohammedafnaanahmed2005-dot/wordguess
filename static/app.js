const alphabet = "abcdefghijklmnopqrstuvwxyz";
const keyboardRows = ["qwertyuiop", "asdfghjkl", "zxcvbnm"];
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

const elements = {
  attemptCount: document.querySelector("#attempt-count"),
  announcement: document.querySelector("#announcement"),
  drawingCaption: document.querySelector("#drawing-caption"),
  feedback: document.querySelector("#feedback"),
  hintButton: document.querySelector("#hint-button"),
  hintCount: document.querySelector("#hint-count"),
  keyboard: document.querySelector("#keyboard"),
  letterHistory: document.querySelector("#letter-history"),
  lettersTotal: document.querySelector("#letters-total"),
  livesRow: document.querySelector("#lives-row"),
  livesText: document.querySelector("#lives-text"),
  newGameButton: document.querySelector("#new-game-button"),
  wordHint: document.querySelector("#word-hint"),
  wordLength: document.querySelector("#word-length"),
  wordSlots: document.querySelector("#word-slots"),
};

let gameState = null;
let requestInProgress = false;

function buildKeyboard() {
  elements.keyboard.replaceChildren();
  keyboardRows.forEach((row) => {
    const rowElement = document.createElement("div");
    rowElement.className = "keyboard-row";
    for (const letter of row) {
      const button = document.createElement("button");
      button.className = "key-button";
      button.type = "button";
      button.textContent = letter;
      button.dataset.letter = letter;
      button.setAttribute("aria-label", `Guess ${letter.toUpperCase()}`);
      button.addEventListener("click", () => submitGuess(letter));
      rowElement.append(button);
    }
    elements.keyboard.append(rowElement);
  });
}

function buildLives() {
  elements.livesRow.replaceChildren();
  for (let index = 0; index < 6; index += 1) {
    const life = document.createElement("span");
    life.className = "life-dot";
    life.dataset.life = String(index);
    elements.livesRow.append(life);
  }
}

function renderGame(state) {
  gameState = state;
  const incorrectCount = state.incorrect_letters.length;
  const usedLetters = new Set(state.guessed_letters);
  const isFinished = state.status !== "playing";

  elements.attemptCount.innerHTML = `<strong>${state.attempts_remaining}</strong><span> / ${state.max_attempts}</span>`;
  elements.livesText.textContent = `${state.attempts_remaining} ${state.attempts_remaining === 1 ? "chance" : "chances"}`;
  elements.livesRow.setAttribute(
    "aria-label",
    `${state.attempts_remaining} ${state.attempts_remaining === 1 ? "attempt" : "attempts"} remaining`,
  );
  elements.lettersTotal.textContent = String(state.guessed_letters.length);
  elements.wordLength.textContent = `${state.masked_word.length} ${state.masked_word.length === 1 ? "LETTER" : "LETTERS"}`;
  elements.wordHint.textContent = isFinished
    ? state.status === "won"
      ? "Beautifully done — you found the word"
      : "The mystery word was"
    : "A word is waiting to be discovered";

  elements.wordSlots.replaceChildren();
  const wordLength = state.masked_word.length;
  const slotGap = Math.min(12, Math.max(3, 140 / Math.max(1, wordLength)));
  const availableSlotWidth =
    elements.wordSlots.clientWidth -
    8 -
    slotGap * Math.max(0, wordLength - 1);
  const slotWidth = Math.min(
    33,
    Math.max(8, availableSlotWidth / Math.max(1, wordLength)),
  );
  elements.wordSlots.style.setProperty("--slot-width", `${slotWidth}px`);
  elements.wordSlots.style.setProperty(
    "--slot-font-size",
    `${Math.min(21, slotWidth * 0.68)}px`,
  );
  elements.wordSlots.style.setProperty("--slot-gap", `${slotGap}px`);
  state.masked_word.forEach((letter, index) => {
    const slot = document.createElement("span");
    slot.className = `word-slot${letter ? " is-revealed" : ""}`;
    slot.textContent = letter ? letter.toUpperCase() : "";
    slot.setAttribute("aria-hidden", "true");
    slot.dataset.position = String(index + 1);
    elements.wordSlots.append(slot);
  });
  elements.wordSlots.setAttribute(
    "aria-label",
    state.status === "playing"
      ? `${state.masked_word.map((letter) => letter ?? "blank").join(" ")}`
      : `The word is ${state.word}`,
  );
  if (isFinished) {
    const answer = document.createElement("span");
    answer.className = "answer-reveal";
    answer.textContent = state.word.toUpperCase();
    elements.wordSlots.replaceChildren(answer);
  }

  document.querySelectorAll(".key-button").forEach((button) => {
    const letter = button.dataset.letter;
    button.disabled = usedLetters.has(letter) || isFinished || requestInProgress;
    button.classList.toggle("is-correct", usedLetters.has(letter) && !state.incorrect_letters.includes(letter));
    button.classList.toggle("is-incorrect", state.incorrect_letters.includes(letter));
  });

  const hintsRemaining = state.hints_remaining ?? 0;
  if (elements.hintCount) {
    elements.hintCount.textContent = String(hintsRemaining);
  }
  if (elements.hintButton) {
    elements.hintButton.disabled =
      isFinished || requestInProgress || hintsRemaining <= 0;
  }

  document.querySelectorAll(".person-part").forEach((part) => {
    part.classList.toggle("is-visible", Number(part.dataset.stage) <= incorrectCount);
  });
  document.querySelectorAll(".life-dot").forEach((life) => {
    const index = Number(life.dataset.life);
    const isLost = index >= state.attempts_remaining;
    life.classList.toggle("is-lost", isLost);
    life.classList.toggle("is-last", index === state.attempts_remaining - 1 && state.attempts_remaining <= 2);
  });

  renderHistory(state.guessed_letters, state.incorrect_letters);
  renderFeedback(state);
}

function renderHistory(guessedLetters, incorrectLetters) {
  elements.letterHistory.replaceChildren();
  if (guessedLetters.length === 0) {
    const empty = document.createElement("span");
    empty.className = "history-empty";
    empty.textContent = "Your guesses will appear here";
    elements.letterHistory.append(empty);
    return;
  }
  guessedLetters.forEach((letter) => {
    const chip = document.createElement("span");
    chip.className = `history-chip${incorrectLetters.includes(letter) ? " is-incorrect" : " is-correct"}`;
    chip.textContent = letter.toUpperCase();
    chip.setAttribute(
      "aria-label",
      `${letter.toUpperCase()}, ${incorrectLetters.includes(letter) ? "not in word" : "in word"}`,
    );
    elements.letterHistory.append(chip);
  });
}

function renderFeedback(state) {
  const resultMessages = {
    correct: ["Lovely, that’s in the word.", "A perfect fit — keep going.", "Nice one, you found a letter."],
    incorrect: ["Not quite. Take another look.", "That one missed — keep going.", "No match this time."],
    duplicate: ["You already tried that letter."],
    invalid: ["Choose one letter from A to Z."],
    round_over: ["This round is over. Start a new game to play again."],
  };

  if (state.status === "won") {
    setFeedback("won", "A lovely solve. You found it!");
    elements.drawingCaption.textContent = "A word well found.";
    elements.announcement.textContent = `You win! The word was ${state.word}.`;
    return;
  }
  if (state.status === "lost") {
    setFeedback("lost", `Out of chances. The word was ${state.word.toUpperCase()}.`);
    elements.drawingCaption.textContent = "The word got away this time.";
    elements.announcement.textContent = `Round over. The word was ${state.word}.`;
    return;
  }

  elements.drawingCaption.textContent = [
    "A fresh start. You’ve got this.",
    "Good thinking. Keep going.",
    "Stay curious, you’re doing well.",
    "Every letter brings you closer.",
    "A little focus goes a long way.",
    "You’re nearly there. Trust your instincts.",
  ][Math.min(state.incorrect_letters.length, 5)];

  const messagePool = resultMessages[state.result];
  if (messagePool) {
    const message = messagePool[Math.floor(Math.random() * messagePool.length)];
    setFeedback(state.result, message);
    if (state.result === "correct" || state.result === "incorrect") {
      elements.announcement.textContent = message;
    }
  } else if (state.incorrect_letters.length === 0 && state.guessed_letters.length === 0) {
    setFeedback("neutral", "Pick a letter to begin");
  }
}

function setFeedback(kind, message) {
  const icon = document.createElement("span");
  icon.className = "feedback-dot";
  icon.setAttribute("aria-hidden", "true");
  const text = document.createElement("span");
  text.textContent = message;
  elements.feedback.className = `feedback is-${kind}`;
  elements.feedback.replaceChildren(icon, text);
}

async function apiRequest(path, body) {
  const response = await fetch(path, {
    method: body === undefined ? "GET" : "POST",
    headers: body === undefined ? {} : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
    credentials: "same-origin",
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "The game could not complete that request.");
  }
  return payload;
}

async function submitGuess(letter) {
  if (!gameState || gameState.status !== "playing" || requestInProgress) return;
  const normalizedLetter = letter.toLowerCase();
  if (gameState.guessed_letters.includes(normalizedLetter)) return;

  requestInProgress = true;
  document.querySelectorAll(".key-button").forEach((button) => {
    button.disabled = true;
  });
  try {
    const state = await apiRequest("/api/guess", { letter: normalizedLetter });
    renderGame(state);
  } catch (error) {
    showError(error);
  } finally {
    requestInProgress = false;
    if (gameState) renderGame(gameState);
  }
}

async function startNewGame() {
  if (requestInProgress) return;
  requestInProgress = true;
  elements.newGameButton.disabled = true;
  try {
    const state = await apiRequest("/api/new", {});
    elements.announcement.textContent = "A new word is ready.";
    renderGame(state);
    if (!reducedMotion.matches) {
      elements.wordSlots.classList.remove("celebrate");
      void elements.wordSlots.offsetWidth;
      elements.wordSlots.classList.add("celebrate");
    }
  } catch (error) {
    showError(error);
  } finally {
    requestInProgress = false;
    elements.newGameButton.disabled = false;
    if (gameState) renderGame(gameState);
  }
}

function showError(error) {
  const message = error instanceof Error ? error.message : "Something went wrong.";
  setFeedback("lost", message);
  elements.announcement.textContent = message;
}

async function useHint() {
  if (
    !gameState ||
    gameState.status !== "playing" ||
    requestInProgress ||
    (gameState.hints_remaining ?? 0) <= 0
  ) {
    return;
  }
  requestInProgress = true;
  if (elements.hintButton) elements.hintButton.disabled = true;
  document.querySelectorAll(".key-button").forEach((button) => {
    button.disabled = true;
  });
  try {
    const state = await apiRequest("/api/hint", {});
    renderGame(state);
    if (state.hint) {
      const message = `Hint: the word contains “${state.hint.toUpperCase()}”.`;
      setFeedback("correct", message);
      elements.announcement.textContent = message;
    }
  } catch (error) {
    showError(error);
  } finally {
    requestInProgress = false;
    if (gameState) renderGame(gameState);
  }
}

function openHelp() {
  document.querySelector("#help-dialog").showModal();
}

buildKeyboard();
buildLives();
elements.newGameButton.addEventListener("click", startNewGame);
if (elements.hintButton) {
  elements.hintButton.addEventListener("click", useHint);
}
document.querySelector("#help-button").addEventListener("click", openHelp);
document.querySelector("#close-help").addEventListener("click", () => {
  document.querySelector("#help-dialog").close();
});
document.querySelector("#got-it").addEventListener("click", () => {
  document.querySelector("#help-dialog").close();
});
document.addEventListener("keydown", (event) => {
  if (event.altKey || event.ctrlKey || event.metaKey) return;
  if (event.key === "Escape") return;
  const letter = event.key.toLowerCase();
  if (alphabet.includes(letter) && !document.querySelector("#help-dialog").open) {
    event.preventDefault();
    submitGuess(letter);
  }
});

apiRequest("/api/state")
  .then(renderGame)
  .catch(showError);
