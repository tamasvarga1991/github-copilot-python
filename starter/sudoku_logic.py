import copy
import random

SIZE = 9
EMPTY = 0
MIN_CLUES = 17
MAX_GENERATION_ATTEMPTS = 20

def deep_copy(board):
    return copy.deepcopy(board)

def create_empty_board():
    return [[EMPTY for _ in range(SIZE)] for _ in range(SIZE)]

def is_safe(board, row, col, num):
    # Check row and column
    for x in range(SIZE):
        if board[row][x] == num or board[x][col] == num:
            return False
    # Check 3x3 box
    start_row = row - row % 3
    start_col = col - col % 3
    for i in range(3):
        for j in range(3):
            if board[start_row + i][start_col + j] == num:
                return False
    return True

def fill_board(board):
    for row in range(SIZE):
        for col in range(SIZE):
            if board[row][col] == EMPTY:
                possible = list(range(1, SIZE + 1))
                random.shuffle(possible)
                for candidate in possible:
                    if is_safe(board, row, col, candidate):
                        board[row][col] = candidate
                        if fill_board(board):
                            return True
                        board[row][col] = EMPTY
                return False
    return True

def count_solutions(board):
    """Return the number of solutions, capped at two."""
    working_board = deep_copy(board)

    for row in range(SIZE):
        for col in range(SIZE):
            value = working_board[row][col]
            if value == EMPTY:
                continue
            if value < 1 or value > SIZE:
                return 0
            working_board[row][col] = EMPTY
            safe = is_safe(working_board, row, col, value)
            working_board[row][col] = value
            if not safe:
                return 0

    def search():
        best_cell = None
        best_candidates = None

        for row in range(SIZE):
            for col in range(SIZE):
                if working_board[row][col] != EMPTY:
                    continue
                candidates = [
                    num for num in range(1, SIZE + 1)
                    if is_safe(working_board, row, col, num)
                ]
                if not candidates:
                    return 0
                if best_candidates is None or len(candidates) < len(best_candidates):
                    best_cell = (row, col)
                    best_candidates = candidates
                    if len(candidates) == 1:
                        break
            if best_candidates is not None and len(best_candidates) == 1:
                break

        if best_cell is None:
            return 1

        row, col = best_cell
        solution_count = 0
        for candidate in best_candidates:
            working_board[row][col] = candidate
            solution_count += search()
            working_board[row][col] = EMPTY
            if solution_count >= 2:
                return 2
        return solution_count

    return search()

def remove_cells(board, clues):
    target_removals = SIZE * SIZE - clues
    if target_removals == 0:
        return True

    cells = [(row, col) for row in range(SIZE) for col in range(SIZE)]
    random.shuffle(cells)
    removed = 0

    for row, col in cells:
        value = board[row][col]
        if value != EMPTY:
            board[row][col] = EMPTY
            if count_solutions(board) == 1:
                removed += 1
                if removed == target_removals:
                    return True
            else:
                board[row][col] = value

    return removed == target_removals

def generate_puzzle(clues=35):
    if not MIN_CLUES <= clues <= SIZE * SIZE:
        raise ValueError(
            f"clues must be between {MIN_CLUES} and {SIZE * SIZE}"
        )

    for _ in range(MAX_GENERATION_ATTEMPTS):
        solution = create_empty_board()
        if not fill_board(solution):
            continue
        puzzle = deep_copy(solution)
        if remove_cells(puzzle, clues):
            return puzzle, solution

    raise RuntimeError(
        f"Unable to generate a unique puzzle with exactly {clues} clues "
        f"after {MAX_GENERATION_ATTEMPTS} attempts"
    )
