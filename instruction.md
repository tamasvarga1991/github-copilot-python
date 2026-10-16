# Sudoku Project Maintenance Instructions

## Purpose and scope

Use this guide when reviewing or changing this Flask Sudoku project. Read the
[README rubric](README.md#project-instructions) alongside the relevant source and
tests. Preserve existing behavior unless the requested task explicitly changes it.

This root-level `instruction.md` is a reference document, not an automatically
discovered Copilot instruction file. Attach or reference it in Copilot requests.
If automatic project-wide instructions are requested later, use the supported
`.github/copilot-instructions.md` location; do not assume this filename activates
them or create duplicate instruction files without a request.

## Project overview

The application generates standard 9x9 Sudoku puzzles with exactly one solution.
Players select Easy, Medium, or Hard, enter digits, receive immediate conflict
feedback, request hints, and check their solution. Successful completion stops a
timer and offers an inline form for a browser-local Top 10 leaderboard.

The frontend uses plain JavaScript, HTML, and CSS. Flask serves the page and JSON
endpoints. There is no frontend build step, database, authentication, or server-side
leaderboard. Runtime dependencies and pytest are declared in
[starter/requirements.txt](starter/requirements.txt).

## Architecture and file responsibilities

| File | Responsibility |
| --- | --- |
| [starter/app.py](starter/app.py) | Flask application, request parsing, difficulty mapping, current game storage, and Check/Hint responses. |
| [starter/sudoku_logic.py](starter/sudoku_logic.py) | Board creation, Sudoku rules, randomized backtracking, solution counting, and uniqueness-preserving clue removal. Keep this independent of Flask and browser state. |
| [starter/templates/index.html](starter/templates/index.html) | Page structure, control IDs, accessible status regions, theme switch, timer, score form, and leaderboard table. |
| [starter/static/main.js](starter/static/main.js) | Board rendering, delegated input validation, API calls, game lifecycle, timer, hint counting, themes, and localStorage scores. |
| [starter/static/styles.css](starter/static/styles.css) | Light/dark theme variables, alternating 3x3 block colors, cell states, controls, and responsive layout. |
| [starter/tests/test_sudoku_logic.py](starter/tests/test_sudoku_logic.py) | Rule, solver, generation, uniqueness, and difficulty tests. |
| [starter/tests/test_app.py](starter/tests/test_app.py) | Flask test client, route contracts, hint behavior, and page markup assertions. |
| [starter/tests/test_input_feedback.html](starter/tests/test_input_feedback.html) | Browser regression harness loading the real game script with mocked fetch and storage. |
| [README.md](README.md) | Setup, usage, test instructions, and acceptance rubric. |

### State boundaries

- Flask's process-global `CURRENT` stores the original puzzle and full solution.
  It is shared across clients in a process, not isolated by user, tab, or session.
  It is also not shared consistently across separate worker processes.
- The browser owns entered values, disabled hinted cells, `hintsUsed`,
  `activeDifficulty`, `gameSolved`, and timer/completion state. Hints do not update
  the original server-side puzzle.
- Only scores and theme preferences persist in localStorage. The active game and
  timer are not restored after reload; startup requests a new game.
- Do not expose the full solution in new-game responses or move it into browser
  storage. Treat server state isolation as a separate architectural change.

## Coding standards and Copilot workflow

- Read the relevant producer, caller, UI markup, and tests before proposing edits.
  Trace behavior across Flask and JavaScript rather than changing one side alone.
- Make surgical changes within the requested scope. Do not combine a feature with
  framework migration, unrelated cleanup, or fixes for unrelated existing issues.
- Follow local formatting: Python uses four-space indentation and snake_case;
  JavaScript uses two spaces, semicolons, and camelCase; CSS uses four spaces and
  custom properties for theme colors. Preserve the surrounding quote style.
- Reuse `SIZE`, `EMPTY`, `DIFFICULTY_CLUES`, existing timer/storage helpers, and
  current CSS state classes. Avoid new dependencies or abstractions for behavior
  that fits the existing implementation.
- Keep route handlers focused on HTTP concerns and algorithms in Sudoku logic.
  Keep visual-only changes in CSS when the existing DOM supports them.
- Preserve DOM IDs consumed by JavaScript and markup tests. If an ID or response
  shape changes intentionally, update every caller and affected test together.
- Explain non-obvious constraints briefly; do not add comments restating code.
  Do not introduce `eval`, unsafe HTML interpolation, or secrets.
- Do not edit or commit `.venv`, cache directories, or generated artifacts.
  Preserve unrelated working-tree edits and do not commit unless asked.
- Before changing a public contract or storage schema, explain the compatibility
  impact. Ask for a decision when the requested behavior is genuinely ambiguous.
- Copilot-generated code is a proposal until verified. Add regression coverage,
  run appropriate checks, and report exact results and any unverified behavior.
- Update directly related README usage/test instructions when behavior changes,
  and keep this guide synchronized with intentional architectural changes.

## Flask API contracts and design principles

All coordinates below are zero-based. Boards are nested lists of nine rows with
nine integer values each; `0` is empty and `1` through `9` are digits.

| Method and path | Current input | Current successful response |
| --- | --- | --- |
| `GET /` | None | Rendered game page. |
| `GET /new` | Optional `difficulty=easy\|medium\|hard`, default `medium`; optional integer `clues` overrides difficulty. | `{"puzzle": [[...], ...]}`; stores puzzle and solution in `CURRENT`. |
| `POST /check` | JSON `{"board": [[...], ...]}` | `{"incorrect": [[row, col], ...]}`; empty list means solved. Empty cells differing from the solution are included. |
| `POST /hint` | JSON `{"board": [[...], ...]}` | `{"row": 0, "col": 0, "value": 5}` for exactly one eligible cell. |

- Preserve existing paths, methods, clue-query compatibility, and JSON field names
  unless an API change is explicitly requested. Although `/new` changes state via
  GET, do not silently migrate it to POST.
- Return JSON using `jsonify`; expected client errors use
  `{"error": "Actionable message"}` with a suitable non-success status. Existing
  explicit validation/no-game/no-hint errors use HTTP 400.
- Validate untrusted request data at the boundary. For board payloads require the
  shape and range above and reject booleans, which Python otherwise treats as ints.
  `/hint` implements this validation; `/check` currently does not fully do so.
- Do not require a submitted board to be conflict-free before Check or Hint:
  finding or correcting mistakes is their purpose.
- Complete generation before replacing `CURRENT`. Failed requests must not leave
  half-updated puzzle/solution state or report false success.
- Do not mutate submitted boards or the saved original puzzle during Check/Hint.
  Validate behavior with Flask's test client rather than requiring a live server.

## Sudoku generation and difficulty invariants

- `fill_board` mutates a board using randomized candidate order and recursive
  backtracking. A valid completed solution has digits 1-9 once in every row,
  column, and 3x3 box.
- `count_solutions` copies its input and returns `0`, `1`, or `2`, where `2` means
  two or more solutions. It checks givens for contradictions and searches using
  the empty cell with the fewest candidates. Preserve the early cutoff at two.
  It is not a general malformed-JSON validator.
- `remove_cells` tentatively removes a clue and retains the removal only when
  `count_solutions(board) == 1`; otherwise it restores the value. Never replace
  this with unconditional random removal.
- `generate_puzzle` returns `(puzzle, solution)` with independent nested rows,
  matching givens, exactly the requested clue count, and one solution.
  Clue bounds are 17-81. Generation retries at most
  `MAX_GENERATION_ATTEMPTS` (currently 20), then raises `RuntimeError`.
- Do not relax uniqueness, return fewer/more clues as a silent fallback, or make
  retry loops unbounded. The lower bound does not guarantee successful generation
  of every requested clue count within the retry limit.
- Current profiles are **Easy: 40**, **Medium: 35**, **Hard: 30** clues. Difficulty
  is a clue-count proxy, not a certified human-solving-technique rating.
- Keep backend mappings, selector options, active-difficulty display, persisted
  score validation, and tests aligned if profiles or level names change.
- Changing the selector only announces the pending selection. It must not reset
  the puzzle, timer, hints, or active difficulty. Apply the captured selection only
  after New Game succeeds; keep the current game unchanged on failure.

## Input feedback, Check, and hints

- Maintain the single delegated `input` handler on `#sudoku-board`, so validation
  still works after the cells are rebuilt. Accept only one digit from 1-9.
- Immediate validation detects duplicate digits in rows, columns, and boxes.
  Compare against all cells, including disabled clues/hints, but mark only
  editable conflicts. Recompute highlights when values change or are deleted.
- Keep `conflict` (rule violations) separate from `incorrect` (Check's comparison
  with the saved solution). A legal move can still be an incorrect answer.
  Keep `aria-invalid` synchronized with both states.
- Check must highlight errors without overwriting entries. Editing a checked
  cell clears its stale `incorrect` state and revalidates conflicts.
- Hint first chooses an originally empty cell that is still empty. Only when no
  such cells remain may it correct an originally empty cell with a wrong value.
  Never replace original clues or correct entries.
- A successful Hint fills/corrects exactly one cell from the saved solution,
  disables it, applies `hinted` styling, clears stale error state, revalidates
  conflicts, and increments `hintsUsed` exactly once. Failed hints do not count.
- No eligible hint is an explicit error, not an invented value or an arbitrary
  change. Preserve puzzle uniqueness and leave server puzzle/solution unchanged.

## Timer, completion, and leaderboard

- Start/reset the timer only after a new puzzle loads successfully. Derive elapsed
  seconds from timestamps, not interval tick counts; the 250ms interval refreshes
  the display. Store numeric whole seconds and format only for display.
- Current completion is confirmed by Check returning no incorrect cells, not
  automatically by the final input or Hint. Do not change this trigger incidentally.
- On completion, stop the timer, lock cells, set `gameSolved`, and capture
  `pendingCompletionSeconds`. Show elapsed time and hint count, including correct
  singular/plural wording, then reveal the inline name form.
- Avoid native `prompt()` for names. Require a nonblank trimmed name and cap saved
  names at 30 characters. Guard repeated completion and duplicate submissions.
- Store scores under `sudokuTop10` as a JSON array with this record shape:

  ```json
  {"name": "Player", "timeSeconds": 135, "difficulty": "medium", "hintsUsed": 2}
  ```

- Validate stored arrays and records before use. Time and hint counts must be
  nonnegative integers; difficulty must be `easy`, `medium`, or `hard`.
- Rank all difficulties together by ascending numeric `timeSeconds`, retaining
  only the best ten. Do not sort formatted strings, add hint penalties, or split
  leaderboards by difficulty unless requested.
- Save the completed game's active difficulty, frozen completion time, and hint
  count, not the pending selector value or a running timer.
- Render player names and score values with `textContent`, never as HTML.
  Preserve existing storage keys/schema or provide an explicit migration.
- localStorage is browser/origin-local and editable by the player. Do not describe
  this leaderboard as server-verified, shared across users, or tamper-resistant.

## Themes, accessibility, and responsive styling

- Keep theme state on the root `data-theme` attribute and preference under
  `sudokuTheme` with values `light` or `dark`. Default to light without a saved
  preference. Keep the switch checked state and visible mode label synchronized.
- Theme changes must not recreate the board or reset game state. When storage
  fails, retain the usable theme and explain that persistence failed.
- Use paired light/dark CSS variables. Preserve alternating neighboring 3x3 block
  backgrounds, separate clue shading, grid boundaries, and distinct hint, focus,
  and error states. Block shading must not override feedback colors.
- Preserve readable text and controls in both themes; target at least 4.5:1
  contrast for ordinary text, including disabled clue/hint digits.
- Keep the viewport meta tag, square mobile cells, wrapping controls, and
  independently scrolling leaderboard. Check narrow widths such as 320px as well
  as desktop; avoid page-wide horizontal overflow.
- Retain status/live regions, form labels, keyboard-operable theme switch,
  focus visibility, and the focusable leaderboard scrolling region.

## Error handling and known limitations

Apply these guidelines when touching error paths; they are not claims that all
existing paths already implement them:

- Handle expected validation and generation failures explicitly. Map invalid clue
  bounds to a client error and generation exhaustion to a suitable server error,
  with JSON messages rather than HTML tracebacks.
- Catch only expected exceptions at a useful boundary. Log unexpected server
  failures using Flask's logger without exposing tracebacks to the browser.
  Do not use broad catches to manufacture success or silently discard errors.
- Client API handling should cover network failures, non-JSON responses, and
  non-success statuses. Keep the current board and timer intact when New Game
  fails; do not show a completion or consume a hint on failed requests.
- Storage read, parse, validation, and write failures must be visible. Do not
  silently erase corrupt leaderboard data or claim a score was saved after a
  failed write. Use `message`, `theme-message`, and `difficulty-message` for their
  respective concerns.
- Existing gaps include incomplete `/check` validation, unhandled generation and
  fetch/JSON failures, shared `CURRENT`, and lack of stale-response/concurrent
  request guards. Startup New Game can also clear a leaderboard error message.
  Do not document these as fixed without implementation and regression tests.
- The `debug=True` entry point is for local development, not production
  deployment. Production hosting and multi-user state require separate design.

## Testing and verification requirements

Run commands from `starter`. PowerShell can use the existing local interpreter
without activating the virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pytest -q tests\test_sudoku_logic.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_app.py
```

Choose the smallest relevant test command first; run both modules together for
cross-cutting backend changes. If no environment exists, create one and install
the declared requirements, rather than relying on global packages:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

For manual application checks:

```powershell
.\.venv\Scripts\python.exe -m flask --app app run --no-reload
```

Open `http://127.0.0.1:5000`. A normal startup automatically creates a game.
Stop only the verification server you started after finishing.

### Required coverage for affected behavior

- **Logic:** zero/one/multiple solutions, the cutoff at two, input preservation,
  valid rows/columns/boxes, exact clue counts, matching givens, uniqueness at all
  difficulty levels, invalid bounds, and bounded generation failures.
- **API:** exact JSON shapes and statuses, difficulty mapping/defaults/clue
  precedence, malformed inputs for validation changes, no-game responses, hint
  empty-first priority and wrong-entry fallback, and unchanged saved state.
- **Isolation:** use the existing test-client fixture and `monkeypatch` to reset
  `CURRENT` and restore configuration. Stub generation/random choice in route
  tests when deterministic outputs matter; test real generation in logic tests.
  Some route fixtures are intentionally not valid Sudoku solutions and must not
  be treated as algorithm correctness evidence.
- **Browser:** open [the regression harness](starter/tests/test_input_feedback.html)
  directly and confirm its final "All tests passed." result. It currently covers
  conflict resolution, clues, filtering, Check, hints/delegation after rerender,
  and completion messages for zero, one, and multiple hints.
- Extend the browser harness for changed client behavior. It mocks fetch and
  storage and does not load the production CSS, so it is not proof of live API
  integration, real persistence, or visual correctness.
- For timer/score/theme/difficulty changes, also verify live behavior, persistence
  after reload, storage failures, unchanged current game on selector/theme
  changes, and prevention of duplicate score saves as applicable. Use isolated
  test storage; never clear a player's actual leaderboard.
- For styling changes, inspect both themes and mobile/desktop sizes, including
  clues, hints, errors, focused cells, and leaderboard readability.

No frontend build, JavaScript test runner, or linter is currently configured.
Do not invent successful checks or require new tooling for a small change.
Documentation-only updates need no runtime test run; verify links, commands, and
claims against the source. Report tests actually run, not historical test counts.