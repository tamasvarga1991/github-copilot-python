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
