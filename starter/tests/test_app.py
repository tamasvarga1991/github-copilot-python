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
    assert b'id="sudoku-board"' in response.data
    assert b'<option value="easy">Easy</option>' in response.data
    assert b'<option value="medium" selected>Medium</option>' in response.data
    assert b'<option value="hard">Hard</option>' in response.data


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
