# Refactor a Sudoku Game written in Python Flask

Use this simple Sudoku game as a starting point to practice your skills with GitHub Copilot. The goal is to refactor the code to use modern technologies, while also adding new features and improving the overall user experience.

## Getting Started

Follow these instructions to get a copy of the project up and running on your local machine.

### Dependencies

```
- Modern web browser (Chrome, Firefox, Edge, etc.)
- Python 3
```

### Installation

1. Fork this repository to your GitHub account. (You can use the "Fork" button on the top right corner of the repository page.)

2. Clone your forked repository to your local machine.

3. Open a terminal window and navigate to the "github-copilot-python/starter" directory.

4. Create a Python virtual environment and activate it (optional but highly recommended).

```bash
python3 -m venv .venv
source .venv/bin/activate
```

5. Install required Python packages.

```bash
pip install -r requirements.txt
```

6. Run the Flask app.

```bash
python app.py
```

7. Open http://127.0.0.1:5000 in your browser.

Changing the difficulty selector shows a confirmation message but does not change the current puzzle or reset its timer. Click **New Game** to start a puzzle at the selected difficulty.
The **Current difficulty** display identifies the active puzzle's level and updates only after a new game loads successfully.

Use the theme switch to change between light and dark themes without changing the game. Light mode is the default when no preference is saved. The switch always displays the active mode: **Light Mode** or **Dark Mode**. Your preference is saved in browser localStorage under `sudokuTheme` and restored on the next visit. If browser storage is unavailable, switching themes still works and a message explains that the preference could not be saved.

Entered digits are checked immediately for duplicates in their row, column, or 3x3 box. Conflicting editable cells are highlighted, and the highlights disappear as conflicts are resolved. **Check Solution** still compares the board against the saved solution; a legal digit is not necessarily the correct solution digit.

### Running the tests

On small screens, the Sudoku board scales to the available width and controls wrap. The leaderboard scrolls horizontally within its own focusable region when its columns cannot fit, keeping text readable without widening the page.

**Hint** fills and locks one empty cell first. When no editable empty cells remain, it corrects and locks one incorrect entry instead. Correct entries and original clues are left unchanged.

From the `github-copilot-python/starter` directory, install the dependencies (including pytest) and run the test suite:

```bash
pip install -r requirements.txt
python -m pytest
```

The baseline tests cover the Flask page and API routes, along with Sudoku board creation, safety checks, solution generation, and puzzle clues. To run only one test module, use `python -m pytest tests/test_app.py` or `python -m pytest tests/test_sudoku_logic.py`.

Open `starter/tests/test_input_feedback.html` in a browser to run the client-side input-feedback regression tests. They use the actual game JavaScript with mocked API responses and isolated test storage.

## Project Instructions

Use GitHub Copilot to refactor the code for this game to add more advanced features. The goal is to create a more modern and maintainable codebase and add additional functionality to the final product. You can use any combination of code completion and chat features, like Ask, Edit, or Agent modes.

- Errors should be handled gracefully with appropriate messages to the user.
- Implement a Sudoku board generator that creates a valid Sudoku puzzle with a unique solution.
- Add a timer to track how long it takes to solve the puzzle.
- Implement a solution checker that verifies if the user's solution is correct using event delegation.
- Add a difficulty selector to allow users to choose between easy, medium, and hard puzzles.
- Add a hint feature that provides clues for the user that are noted with unique colors.
- Add a check puzzle button that checks the current state of the board against the solution.
- User should get immediate feedback on their input, such as highlighting invalid entries.
- Top 10 scores should be saved in local storage and displayed on the page with the user's name, time taken, hints used, and difficulty level.
- The game should be responsive and work well on both desktop and mobile devices.
- UI colors should be visually appealing and accessible.
- Completed and correct puzzles should display a congratulatory message with the time taken and hints used and ask for the user's name for Top 10 times.
