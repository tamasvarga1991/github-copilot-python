// Client-side rendering and interaction for the Flask-backed Sudoku
const SIZE = 9;
const LEADERBOARD_KEY = 'sudokuTop10';
const THEME_KEY = 'sudokuTheme';
let puzzle = [];
let timerInterval = null;
let timerStartedAt = null;
let elapsedSeconds = 0;
let hintsUsed = 0;
let activeDifficulty = 'medium';
let gameSolved = false;
let pendingCompletionSeconds = null;

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  document.getElementById('theme-toggle').checked = theme === 'dark';
  document.getElementById('theme-label').textContent = theme === 'dark' ? 'Dark Mode' : 'Light Mode';
}

function showThemeError(message) {
  const status = document.getElementById('theme-message');
  status.textContent = message;
  status.hidden = false;
}

function initializeTheme() {
  let theme;
  try {
    theme = localStorage.getItem(THEME_KEY);
  } catch {
    applyTheme('light');
    showThemeError('Saved theme could not be read. You can still switch themes.');
    return;
  }
  if (theme !== null && theme !== 'light' && theme !== 'dark') {
    applyTheme('light');
    showThemeError('The saved theme is invalid. Select a theme to save a new preference.');
    return;
  }
  applyTheme(theme || 'light');
}

function toggleTheme() {
  const theme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  applyTheme(theme);
  try {
    localStorage.setItem(THEME_KEY, theme);
  } catch {
    showThemeError('Theme changed, but your preference could not be saved.');
    return;
  }
  document.getElementById('theme-message').hidden = true;
}

function readLeaderboard() {
  let scores;
  try {
    scores = JSON.parse(localStorage.getItem(LEADERBOARD_KEY) || '[]');
  } catch {
    throw new Error('Leaderboard data could not be read or parsed.');
  }
  if (
    !Array.isArray(scores)
    || scores.some(score => (
      score === null
      || typeof score !== 'object'
      || typeof score.name !== 'string'
      || !Number.isInteger(score.timeSeconds)
      || score.timeSeconds < 0
      || !['easy', 'medium', 'hard'].includes(score.difficulty)
      || !Number.isInteger(score.hintsUsed)
      || score.hintsUsed < 0
    ))
  ) {
    throw new Error('Leaderboard data in local storage is invalid.');
  }
  scores.sort((a, b) => a.timeSeconds - b.timeSeconds);
  const topScores = scores.slice(0, 10);
  if (scores.length > topScores.length) {
    try {
      localStorage.setItem(LEADERBOARD_KEY, JSON.stringify(topScores));
    } catch {
      throw new Error('Leaderboard could not be saved to local storage.');
    }
  }
  return topScores;
}

function renderLeaderboard() {
  const tbody = document.querySelector('#leaderboard tbody');
  const msg = document.getElementById('message');
  try {
    const scores = readLeaderboard();
    tbody.replaceChildren();
    scores.forEach((score, index) => {
      const row = document.createElement('tr');
      const values = [
        index + 1,
        score.name,
        formatTime(score.timeSeconds),
        score.difficulty,
        score.hintsUsed
      ];
      values.forEach(value => {
        const cell = document.createElement('td');
        cell.textContent = value;
        row.appendChild(cell);
      });
      tbody.appendChild(row);
    });
  } catch (error) {
    msg.className = 'error';
    msg.innerText = error.message;
  }
}

function saveScore(name, timeSeconds) {
  const scores = readLeaderboard();
  scores.push({
    name,
    timeSeconds,
    difficulty: activeDifficulty,
    hintsUsed
  });
  scores.sort((a, b) => a.timeSeconds - b.timeSeconds);
  const topScores = scores.slice(0, 10);
  try {
    localStorage.setItem(LEADERBOARD_KEY, JSON.stringify(topScores));
  } catch {
    throw new Error('Leaderboard could not be saved to local storage.');
  }
  renderLeaderboard();
}

function formatTime(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60).toString().padStart(2, '0');
  const seconds = (totalSeconds % 60).toString().padStart(2, '0');
  return `${minutes}:${seconds}`;
}

function updateTimer() {
  if (timerStartedAt !== null) {
    elapsedSeconds = Math.floor((Date.now() - timerStartedAt) / 1000);
  }
  const timer = document.getElementById('timer');
  const minutes = Math.floor(elapsedSeconds / 60).toString().padStart(2, '0');
  const seconds = (elapsedSeconds % 60).toString().padStart(2, '0');
  timer.innerText = `${minutes}:${seconds}`;
  timer.dataset.elapsedSeconds = elapsedSeconds;
}

function startTimer() {
  if (timerInterval !== null) {
    clearInterval(timerInterval);
  }
  elapsedSeconds = 0;
  timerStartedAt = Date.now();
  updateTimer();
  timerInterval = setInterval(updateTimer, 250);
}

function stopTimer() {
  if (timerStartedAt === null) {
    return elapsedSeconds;
  }
  elapsedSeconds = Math.floor((Date.now() - timerStartedAt) / 1000);
  timerStartedAt = null;
  clearInterval(timerInterval);
  timerInterval = null;
  updateTimer();
  return elapsedSeconds;
}

function createBoardElement() {
  const boardDiv = document.getElementById('sudoku-board');
  boardDiv.innerHTML = '';
  for (let i = 0; i < SIZE; i++) {
    const rowDiv = document.createElement('div');
    rowDiv.className = 'sudoku-row';
    for (let j = 0; j < SIZE; j++) {
      const input = document.createElement('input');
      input.type = 'text';
      input.maxLength = 1;
      input.className = 'sudoku-cell';
      input.dataset.row = i;
      input.dataset.col = j;
      rowDiv.appendChild(input);
    }
    boardDiv.appendChild(rowDiv);
  }
}

function validateBoardConflicts() {
  const inputs = Array.from(document.querySelectorAll('#sudoku-board input'));
  for (const input of inputs) {
    const row = Number(input.dataset.row);
    const col = Number(input.dataset.col);
    const conflict = !input.disabled && input.value !== '' && inputs.some(other => {
      if (other === input || other.value !== input.value) return false;
      const otherRow = Number(other.dataset.row);
      const otherCol = Number(other.dataset.col);
      return row === otherRow || col === otherCol
        || (Math.floor(row / 3) === Math.floor(otherRow / 3)
          && Math.floor(col / 3) === Math.floor(otherCol / 3));
    });
    input.classList.toggle('conflict', conflict);
    input.setAttribute('aria-invalid', String(conflict || input.classList.contains('incorrect')));
  }
}

function renderPuzzle(puz) {
  puzzle = puz;
  createBoardElement();
  const boardDiv = document.getElementById('sudoku-board');
  const inputs = boardDiv.getElementsByTagName('input');
  for (let i = 0; i < SIZE; i++) {
    for (let j = 0; j < SIZE; j++) {
      const idx = i * SIZE + j;
      const val = puzzle[i][j];
      const inp = inputs[idx];
      if (val !== 0) {
        inp.value = val;
        inp.disabled = true;
        inp.className += ' prefilled';
      } else {
        inp.value = '';
        inp.disabled = false;
      }
    }
  }
}

async function newGame() {
  const difficulty = document.getElementById('difficulty').value;
  const res = await fetch(`/new?difficulty=${encodeURIComponent(difficulty)}`);
  const data = await res.json();
  if (!res.ok) {
    document.getElementById('message').innerText = data.error || 'Unable to start a new game.';
    return;
  }
  activeDifficulty = difficulty;
  document.getElementById('current-difficulty').textContent =
    activeDifficulty.charAt(0).toUpperCase() + activeDifficulty.slice(1);
  hintsUsed = 0;
  gameSolved = false;
  pendingCompletionSeconds = null;
  renderPuzzle(data.puzzle);
  startTimer();
  const msg = document.getElementById('message');
  msg.className = '';
  msg.innerText = '';
  document.getElementById('score-entry').hidden = true;
  document.getElementById('player-name').value = '';
  document.getElementById('difficulty-message').innerText = 'Difficulty changes apply when you click New Game.';
}

async function checkSolution() {
  if (gameSolved) {
    return;
  }
  const boardDiv = document.getElementById('sudoku-board');
  const inputs = boardDiv.getElementsByTagName('input');
  const board = [];
  for (let i = 0; i < SIZE; i++) {
    board[i] = [];
    for (let j = 0; j < SIZE; j++) {
      const idx = i * SIZE + j;
      const val = inputs[idx].value;
      board[i][j] = val ? parseInt(val, 10) : 0;
    }
  }
  const res = await fetch('/check', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({board})
  });
  const data = await res.json();
  const msg = document.getElementById('message');
  if (!res.ok || data.error) {
    msg.className = 'error';
    msg.innerText = data.error || 'Unable to check the puzzle.';
    return;
  }
  const incorrect = new Set(data.incorrect.map(x => x[0]*SIZE + x[1]));
  for (let idx = 0; idx < inputs.length; idx++) {
    const inp = inputs[idx];
    if (inp.disabled) continue;
    const isIncorrect = incorrect.has(idx);
    inp.classList.toggle('incorrect', isIncorrect);
    inp.setAttribute('aria-invalid', String(isIncorrect || inp.classList.contains('conflict')));
  }
  if (incorrect.size === 0) {
    pendingCompletionSeconds = stopTimer();
    gameSolved = true;
    for (const input of inputs) {
      input.disabled = true;
    }
    msg.className = 'success';
    msg.innerText = `Congratulations! You solved it in ${formatTime(pendingCompletionSeconds)} with ${hintsUsed} hint${hintsUsed === 1 ? '' : 's'} used. Enter your name to save your score.`;
    document.getElementById('score-entry').hidden = false;
    document.getElementById('player-name').focus();
  } else {
    msg.className = 'error';
    msg.innerText = `${incorrect.size} cell${incorrect.size === 1 ? ' is' : 's are'} incorrect or incomplete.`;
  }
}

function submitScore() {
  const msg = document.getElementById('message');
  const nameInput = document.getElementById('player-name');
  const name = nameInput.value.trim();
  if (!name) {
    msg.className = 'error';
    msg.innerText = 'Enter your name to save your score.';
    nameInput.focus();
    return;
  }
  if (pendingCompletionSeconds === null) {
    msg.className = 'error';
    msg.innerText = 'Solve a puzzle before saving a score.';
    return;
  }
  try {
    saveScore(name.slice(0, 30), pendingCompletionSeconds);
    pendingCompletionSeconds = null;
    document.getElementById('score-entry').hidden = true;
    msg.className = 'success';
    msg.innerText = 'Your score has been saved to the Top 10 leaderboard.';
  } catch (error) {
    msg.className = 'error';
    msg.innerText = error.message;
  }
}

async function getHint() {
  if (gameSolved) {
    return;
  }
  const inputs = document.getElementById('sudoku-board').getElementsByTagName('input');
  const board = [];
  for (let row = 0; row < SIZE; row++) {
    board[row] = [];
    for (let col = 0; col < SIZE; col++) {
      const value = inputs[row * SIZE + col].value;
      board[row][col] = value ? parseInt(value, 10) : 0;
    }
  }

  const res = await fetch('/hint', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({board})
  });
  const data = await res.json();
  const msg = document.getElementById('message');
  if (!res.ok || data.error) {
    msg.className = 'error';
    msg.innerText = data.error || 'Unable to provide a hint.';
    return;
  }

  const input = inputs[data.row * SIZE + data.col];
  const correctingEntry = input.value !== '';
  input.value = data.value;
  input.disabled = true;
  input.classList.remove('incorrect');
  input.classList.add('hinted');
  input.setAttribute('aria-label', `Hint: ${data.value}`);
  input.setAttribute('aria-invalid', 'false');
  validateBoardConflicts();
  hintsUsed += 1;
  msg.className = 'success';
  msg.innerText = correctingEntry
    ? 'Hint used: one incorrect entry has been corrected and locked.'
    : 'Hint used: one correct cell has been filled and locked.';
}

// Wire buttons
window.addEventListener('load', () => {
  document.getElementById('sudoku-board').addEventListener('input', (event) => {
    const input = event.target;
    if (!(input instanceof HTMLInputElement) || input.disabled) return;
    input.value = input.value.replace(/[^1-9]/g, '').slice(0, 1);
    input.classList.remove('incorrect');
    validateBoardConflicts();
  });
  initializeTheme();
  document.getElementById('theme-toggle').addEventListener('change', toggleTheme);
  document.getElementById('difficulty').addEventListener('change', (event) => {
    const difficulty = event.target.selectedOptions[0].textContent;
    document.getElementById('difficulty-message').innerText =
      `${difficulty} selected. This difficulty will apply when you click New Game. Your current game is unchanged.`;
  });
  document.getElementById('new-game').addEventListener('click', newGame);
  document.getElementById('check-solution').addEventListener('click', checkSolution);
  document.getElementById('hint').addEventListener('click', getHint);
  document.getElementById('save-score').addEventListener('click', submitScore);
  renderLeaderboard();
  // initialize
  newGame();
});