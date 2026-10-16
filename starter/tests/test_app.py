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
    assert b'<meta name="viewport" content="width=device-width, initial-scale=1">' in response.data
    assert b'class="leaderboard-scroll" role="region" aria-label="Top 10 scores table" tabindex="0"' in response.data
    assert b'id="theme-toggle" type="checkbox" role="switch" aria-label="Dark mode">' in response.data
    assert b'id="theme-label">Light Mode</span>' in response.data
    assert b'id="theme-message" role="status" aria-live="polite" hidden' in response.data
    assert b'id="timer" role="timer"' in response.data
    assert b'data-elapsed-seconds="0">00:00</span>' in response.data
    assert b'id="sudoku-board"' in response.data
    assert b'Current difficulty:' in response.data
    assert b'id="current-difficulty" aria-live="polite">No game started</strong>' in response.data
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


@pytest.mark.parametrize("error_type", [RuntimeError, OSError])
@pytest.mark.parametrize("active_game", [False, True])
def test_new_game_handles_generation_failure(
    client, monkeypatch, caplog, error_type, active_game
):
    if active_game:
        sudoku_app.CURRENT["puzzle"] = [[0] * 9 for _ in range(9)]
        sudoku_app.CURRENT["solution"] = [[1] * 9 for _ in range(9)]
    before = copy.deepcopy(sudoku_app.CURRENT)

    def fail_generation(clues):
        raise error_type("Internal generation details")

    monkeypatch.setattr(sudoku_app.sudoku_logic, "generate_puzzle", fail_generation)

    response = client.get("/new?difficulty=hard")

    assert response.status_code == 500
    assert response.json == {
        "error": "Unable to generate a puzzle. Please try starting a new game."
    }
    assert sudoku_app.CURRENT == before
    assert any(record.exc_info for record in caplog.records)
    assert b"Internal generation details" not in response.data


@pytest.mark.parametrize("clues", [16, 82])
def test_new_game_returns_json_for_out_of_range_clues(client, clues):
    response = client.get(f"/new?clues={clues}")

    assert response.status_code == 400
    assert response.json == {"error": "clues must be between 17 and 81"}
    assert sudoku_app.CURRENT == {"puzzle": None, "solution": None}


def test_new_game_rejects_non_integer_clues_before_generation(client, monkeypatch):
    def unexpected_generation(clues):
        pytest.fail("Invalid clue input must not reach generation")

    monkeypatch.setattr(
        sudoku_app.sudoku_logic, "generate_puzzle", unexpected_generation
    )

    response = client.get("/new?clues=invalid&difficulty=hard")

    assert response.status_code == 400
    assert response.json == {"error": "Clues must be an integer"}


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
    assert response.json == {"error": "No empty or incorrect cells available for a hint"}


def test_hint_corrects_one_wrong_entry_after_empty_cells_are_filled(client, monkeypatch):
    solution = [
        [(row * 3 + row // 3 + col) % 9 + 1 for col in range(9)]
        for row in range(9)
    ]
    puzzle = copy.deepcopy(solution)
    puzzle[0][0] = 0
    puzzle[0][1] = 0
    puzzle[0][2] = 0
    board = copy.deepcopy(solution)
    board[0][0] = 9
    board[0][1] = 8
    sudoku_app.CURRENT["puzzle"] = puzzle
    sudoku_app.CURRENT["solution"] = solution
    before = copy.deepcopy(sudoku_app.CURRENT)
    monkeypatch.setattr(sudoku_app.random, "choice", lambda cells: cells[0])

    for expected_col in (0, 1):
        response = client.post("/hint", json={"board": board})

        assert response.status_code == 200
        assert response.json == {
            "row": 0, "col": expected_col, "value": solution[0][expected_col]
        }
        board[response.json["row"]][response.json["col"]] = response.json["value"]

    assert board == solution
    assert sudoku_app.CURRENT == before
    assert sudoku_app.sudoku_logic.count_solutions(puzzle) == 1
    response = client.post("/hint", json={"board": board})
    assert response.status_code == 400


def test_hint_prefers_empty_cells_over_wrong_entries(client, monkeypatch):
    sudoku_app.CURRENT["puzzle"] = [[0] * 9 for _ in range(9)]
    sudoku_app.CURRENT["solution"] = [[1] * 9 for _ in range(9)]
    board = [[1] * 9 for _ in range(9)]
    board[0][0] = 9
    board[0][1] = 0
    monkeypatch.setattr(sudoku_app.random, "choice", lambda cells: cells[0])

    response = client.post("/hint", json={"board": board})

    assert response.status_code == 200
    assert response.json == {"row": 0, "col": 1, "value": 1}


@pytest.mark.parametrize("route", ["/hint", "/check"])
@pytest.mark.parametrize(
    "request_options",
    [
        pytest.param({}, id="empty-body"),
        pytest.param(
            {"data": '{"board":', "content_type": "application/json"},
            id="malformed-json",
        ),
        pytest.param(
            {"data": "null", "content_type": "application/json"},
            id="null-json",
        ),
        pytest.param(
            {"data": '{"board": []}', "content_type": "text/plain"},
            id="non-json-content-type",
        ),
        pytest.param({"json": []}, id="array-payload"),
        pytest.param({"json": "board"}, id="string-payload"),
        pytest.param({"json": 42}, id="number-payload"),
        pytest.param({"json": {}}, id="missing-board"),
        pytest.param({"json": {"board": None}}, id="null-board"),
        pytest.param({"json": {"board": {}}}, id="object-board"),
        pytest.param({"json": {"board": "0" * 9}}, id="string-board"),
        pytest.param({"json": {"board": [[0] * 9] * 8}}, id="too-few-rows"),
        pytest.param({"json": {"board": [[0] * 9] * 10}}, id="too-many-rows"),
        pytest.param({"json": {"board": [[0] * 8] * 9}}, id="too-few-columns"),
        pytest.param({"json": {"board": [[0] * 10] * 9}}, id="too-many-columns"),
        pytest.param(
            {"json": {"board": [[0] * 9] * 8 + [None]}}, id="null-row"
        ),
        pytest.param(
            {"json": {"board": [[0] * 9] * 8 + ["0" * 9]}}, id="string-row"
        ),
        *[
            pytest.param(
                {"json": {"board": [[0] * 9] * 8 + [[0] * 8 + [value]]}},
                id=f"invalid-cell-{name}",
            )
            for name, value in [
                ("negative", -1),
                ("above-nine", 10),
                ("true", True),
                ("false", False),
                ("float", 1.0),
                ("string", "1"),
                ("null", None),
                ("list", []),
                ("object", {}),
            ]
        ],
    ],
)
def test_board_routes_reject_invalid_payload(client, route, request_options):
    sudoku_app.CURRENT["puzzle"] = [[0] * 9 for _ in range(9)]
    sudoku_app.CURRENT["solution"] = [[1] * 9 for _ in range(9)]
    before = copy.deepcopy(sudoku_app.CURRENT)

    response = client.post(route, **request_options)

    assert response.status_code == 400
    assert response.json == {"error": "A valid 9x9 board is required"}
    assert sudoku_app.CURRENT == before
