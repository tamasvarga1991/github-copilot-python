import pytest

import sudoku_logic


def assert_valid_solution(board):
    expected = set(range(1, sudoku_logic.SIZE + 1))
    assert len(board) == sudoku_logic.SIZE
    assert all(len(row) == sudoku_logic.SIZE for row in board)
    assert all(set(row) == expected for row in board)
    assert all(
        {board[row][col] for row in range(sudoku_logic.SIZE)} == expected
        for col in range(sudoku_logic.SIZE)
    )
    for box_row in range(0, sudoku_logic.SIZE, 3):
        for box_col in range(0, sudoku_logic.SIZE, 3):
            box = {
                board[row][col]
                for row in range(box_row, box_row + 3)
                for col in range(box_col, box_col + 3)
            }
            assert box == expected


def test_create_empty_board_has_independent_nine_by_nine_rows():
    board = sudoku_logic.create_empty_board()

    assert len(board) == sudoku_logic.SIZE
    assert all(len(row) == sudoku_logic.SIZE for row in board)
    assert all(value == sudoku_logic.EMPTY for row in board for value in row)
    assert board[0] is not board[1]


def test_deep_copy_does_not_share_nested_rows():
    board = sudoku_logic.create_empty_board()

    copied_board = sudoku_logic.deep_copy(board)
    copied_board[0][0] = 7

    assert board[0][0] == sudoku_logic.EMPTY


@pytest.mark.parametrize(
    ("existing_cell", "candidate_cell"),
    [
        ((0, 0), (0, 1)),
        ((0, 0), (1, 0)),
        ((0, 0), (1, 1)),
    ],
    ids=["same-row", "same-column", "same-box"],
)
def test_is_safe_rejects_duplicate_in_row_column_or_box(
    existing_cell, candidate_cell
):
    board = sudoku_logic.create_empty_board()
    board[existing_cell[0]][existing_cell[1]] = 7

    assert not sudoku_logic.is_safe(
        board, candidate_cell[0], candidate_cell[1], 7
    )
    assert sudoku_logic.is_safe(
        board, candidate_cell[0], candidate_cell[1], 8
    )


def test_fill_board_creates_a_valid_completed_solution():
    board = sudoku_logic.create_empty_board()

    assert sudoku_logic.fill_board(board)

    assert_valid_solution(board)


def test_count_solutions_returns_zero_for_inconsistent_puzzle():
    puzzle = sudoku_logic.create_empty_board()
    puzzle[0][0] = 1
    puzzle[0][1] = 1

    assert sudoku_logic.count_solutions(puzzle) == 0


def test_count_solutions_returns_one_for_a_completed_valid_board():
    solution = [
        [5, 3, 4, 6, 7, 8, 9, 1, 2],
        [6, 7, 2, 1, 9, 5, 3, 4, 8],
        [1, 9, 8, 3, 4, 2, 5, 6, 7],
        [8, 5, 9, 7, 6, 1, 4, 2, 3],
        [4, 2, 6, 8, 5, 3, 7, 9, 1],
        [7, 1, 3, 9, 2, 4, 8, 5, 6],
        [9, 6, 1, 5, 3, 7, 2, 8, 4],
        [2, 8, 7, 4, 1, 9, 6, 3, 5],
        [3, 4, 5, 2, 8, 6, 1, 7, 9],
    ]

    assert sudoku_logic.count_solutions(solution) == 1


def test_count_solutions_caps_multiple_solutions_at_two():
    puzzle = sudoku_logic.create_empty_board()

    assert sudoku_logic.count_solutions(puzzle) == 2


def test_generate_puzzle_returns_matching_solution_and_requested_clue_count():
    clues = 35

    puzzle, solution = sudoku_logic.generate_puzzle(clues)

    assert_valid_solution(solution)
    assert sum(value != sudoku_logic.EMPTY for row in puzzle for value in row) == clues
    assert all(
        puzzle[row][col] in (sudoku_logic.EMPTY, solution[row][col])
        for row in range(sudoku_logic.SIZE)
        for col in range(sudoku_logic.SIZE)
    )
