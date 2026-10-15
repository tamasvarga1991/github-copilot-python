import copy

import pytest

import app as sudoku_app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setitem(sudoku_app.CURRENT, "puzzle", None)
    monkeypatch.setitem(sudoku_app.CURRENT, "solution", None)
    monkeypatch.setitem(sudoku_app.app.config, "TESTING", True)
    with sudoku_app.app.test_client() as test_client:
        yield test_client


def test_index_renders_sudoku_page(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Sudoku Game" in response.data
    assert b'id="theme-toggle" type="button" aria-pressed="false">Dark Mode</button>' in response.data
    assert b'id="theme-message" role="status" aria-live="polite" hidden' in response.data
    assert b'id="timer" role="timer"' in response.data
    assert b'data-elapsed-seconds="0">00:00</span>' in response.data
    assert b'id="sudoku-board"' in response.data
    assert b'<option value="easy">Easy</option>' in response.data
    assert b'<option value="medium" selected>Medium</option>' in response.data
    assert b'<option value="hard">Hard</option>' in response.data
    assert b'aria-describedby="difficulty-message"' in response.data
    assert b'id="difficulty-message" role="status" aria-live="polite"' in response.data
    assert b'Difficulty changes apply when you click New Game.' in response.data
    assert b'id="hint"' in response.data
    assert b'id="message" role="status" aria-live="polite"' in response.data
    assert b'id="leaderboard"' in response.data
    assert b'Top 10 Scores' in response.data
    assert b'id="player-name"' in response.data
    assert b'id="save-score"' in response.data
    assert b'<th scope="col">Player</th>' in response.data
    assert b'<th scope="col">Time</th>' in response.data
    assert b'<th scope="col">Difficulty</th>' in response.data
    assert b'<th scope="col">Hints</th>' in response.data


def test_new_game_returns_and_stores_generated_puzzle(client, monkeypatch):
    puzzle = [[0 for _ in range(9)] for _ in range(9)]
    solution = [[1 for _ in range(9)] for _ in range(9)]
    monkeypatch.setattr(
        sudoku_app.sudoku_logic,
        "generate_puzzle",
        lambda clues: (puzzle, solution),
    )

    response = client.get("/new?clues=40")

    assert response.status_code == 200
    assert response.json == {"puzzle": puzzle}
    assert sudoku_app.CURRENT == {"puzzle": puzzle, "solution": solution}


@pytest.mark.parametrize(
    ("difficulty", "expected_clues"),
    [("easy", 40), ("medium", 35), ("hard", 30)],
)
def test_new_game_maps_difficulty_to_clue_count(
    client, monkeypatch, difficulty, expected_clues
):
    puzzle = [[0 for _ in range(9)] for _ in range(9)]
    solution = [[1 for _ in range(9)] for _ in range(9)]
    generated_with = []

    def generate_puzzle(clues):
        generated_with.append(clues)
        return puzzle, solution

    monkeypatch.setattr(sudoku_app.sudoku_logic, "generate_puzzle", generate_puzzle)

    response = client.get(f"/new?difficulty={difficulty}")

    assert response.status_code == 200
    assert response.json == {"puzzle": puzzle}
    assert generated_with == [expected_clues]


def test_new_game_rejects_unknown_difficulty(client, monkeypatch):
    generated_with = []

    def generate_puzzle(clues):
        generated_with.append(clues)
        return [], []

    monkeypatch.setattr(sudoku_app.sudoku_logic, "generate_puzzle", generate_puzzle)

    response = client.get("/new?difficulty=expert")

    assert response.status_code == 400
    assert response.json == {"error": "Difficulty must be easy, medium, or hard"}
    assert generated_with == []


def test_new_game_keeps_supporting_numeric_clue_count(client, monkeypatch):
    generated_with = []
    puzzle = [[0 for _ in range(9)] for _ in range(9)]
    solution = [[1 for _ in range(9)] for _ in range(9)]
    monkeypatch.setattr(
        sudoku_app.sudoku_logic,
        "generate_puzzle",
        lambda clues: (generated_with.append(clues) or puzzle, solution),
    )

    response = client.get("/new?clues=42")

    assert response.status_code == 200
    assert generated_with == [42]


def test_check_without_active_game_returns_error(client):
    response = client.post("/check", json={"board": [[0] * 9 for _ in range(9)]})

    assert response.status_code == 400
    assert response.json == {"error": "No game in progress"}


def test_check_returns_coordinates_of_cells_that_differ(client):
    solution = [[0 for _ in range(9)] for _ in range(9)]
    solution[0][0] = 5
    solution[8][8] = 9
    sudoku_app.CURRENT["solution"] = solution
    board = copy.deepcopy(solution)
    board[0][0] = 0
    board[4][2] = 3

    response = client.post("/check", json={"board": board})

    assert response.status_code == 200
    assert response.json == {"incorrect": [[0, 0], [4, 2]]}


def test_check_returns_no_incorrect_cells_for_a_correct_board(client):
    solution = [[0 for _ in range(9)] for _ in range(9)]
    solution[0][0] = 5
    sudoku_app.CURRENT["solution"] = solution

    response = client.post("/check", json={"board": solution})

    assert response.status_code == 200
    assert response.json == {"incorrect": []}


def test_hint_returns_solution_for_one_currently_empty_puzzle_cell(client, monkeypatch):
    puzzle = [[0 for _ in range(9)] for _ in range(9)]
    solution = [[1 for _ in range(9)] for _ in range(9)]
    puzzle[0][1] = 4
    solution[0][0] = 7
    solution[0][1] = 4
    sudoku_app.CURRENT["puzzle"] = puzzle
    sudoku_app.CURRENT["solution"] = solution
    board = copy.deepcopy(puzzle)
    board[0][0] = 0
    board[0][2] = 9
    monkeypatch.setattr(sudoku_app.random, "choice", lambda cells: cells[0])

    response = client.post("/hint", json={"board": board})

    assert response.status_code == 200
    assert response.json == {"row": 0, "col": 0, "value": 7}
    assert sudoku_app.CURRENT["puzzle"] == puzzle


def test_hint_returns_error_when_no_game_is_active(client):
    response = client.post("/hint", json={"board": [[0] * 9 for _ in range(9)]})

    assert response.status_code == 400
    assert response.json == {"error": "No game in progress"}


def test_hint_returns_error_when_no_original_empty_cells_remain(client):
    sudoku_app.CURRENT["puzzle"] = [[1 for _ in range(9)] for _ in range(9)]
    sudoku_app.CURRENT["solution"] = [[1 for _ in range(9)] for _ in range(9)]

    response = client.post("/hint", json={"board": [[1] * 9 for _ in range(9)]})

    assert response.status_code == 400
    assert response.json == {"error": "No empty cells available for a hint"}


def test_hint_rejects_invalid_board_payload(client):
    sudoku_app.CURRENT["puzzle"] = [[0 for _ in range(9)] for _ in range(9)]
    sudoku_app.CURRENT["solution"] = [[1 for _ in range(9)] for _ in range(9)]

    response = client.post("/hint", json={"board": [[0] * 8 for _ in range(9)]})

    assert response.status_code == 400
    assert response.json == {"error": "A valid 9x9 board is required"}
