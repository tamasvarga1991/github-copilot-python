from flask import Flask, render_template, jsonify, request
import random
import sudoku_logic

app = Flask(__name__)

# Keep a simple in-memory store for current puzzle and solution
CURRENT = {
    'puzzle': None,
    'solution': None
}

def is_valid_board(board):
    return (
        isinstance(board, list)
        and len(board) == sudoku_logic.SIZE
        and all(
            isinstance(row, list) and len(row) == sudoku_logic.SIZE
            for row in board
        )
        and all(
            isinstance(value, int) and not isinstance(value, bool)
            and sudoku_logic.EMPTY <= value <= sudoku_logic.SIZE
            for row in board
            for value in row
        )
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/new')
def new_game():
    if 'clues' in request.args:
        try:
            clues = int(request.args['clues'])
        except ValueError:
            return jsonify({'error': 'Clues must be an integer'}), 400
    else:
        difficulty = request.args.get('difficulty', 'medium').lower()
        clues = sudoku_logic.DIFFICULTY_CLUES.get(difficulty)
        if clues is None:
            return jsonify({'error': 'Difficulty must be easy, medium, or hard'}), 400

    try:
        puzzle, solution = sudoku_logic.generate_puzzle(clues)
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    except Exception:
        app.logger.exception('Puzzle generation failed for %s clues', clues)
        return jsonify({
            'error': 'Unable to generate a puzzle. Please try starting a new game.'
        }), 500

    CURRENT['puzzle'] = puzzle
    CURRENT['solution'] = solution
    return jsonify({'puzzle': puzzle})

@app.route('/check', methods=['POST'])
def check_solution():
    solution = CURRENT.get('solution')
    if solution is None:
        return jsonify({'error': 'No game in progress'}), 400

    data = request.get_json(silent=True)
    board = data.get('board') if isinstance(data, dict) else None
    if not is_valid_board(board):
        return jsonify({'error': 'A valid 9x9 board is required'}), 400

    incorrect = []
    for i in range(sudoku_logic.SIZE):
        for j in range(sudoku_logic.SIZE):
            if board[i][j] != solution[i][j]:
                incorrect.append([i, j])
    return jsonify({'incorrect': incorrect})

@app.route('/hint', methods=['POST'])
def get_hint():
    puzzle = CURRENT.get('puzzle')
    solution = CURRENT.get('solution')
    if puzzle is None or solution is None:
        return jsonify({'error': 'No game in progress'}), 400

    data = request.get_json(silent=True)
    board = data.get('board') if isinstance(data, dict) else None
    if not is_valid_board(board):
        return jsonify({'error': 'A valid 9x9 board is required'}), 400

    empty_cells = [
        (row, col)
        for row in range(sudoku_logic.SIZE)
        for col in range(sudoku_logic.SIZE)
        if puzzle[row][col] == sudoku_logic.EMPTY
        and board[row][col] == sudoku_logic.EMPTY
    ]
    candidates = empty_cells or [
        (row, col)
        for row in range(sudoku_logic.SIZE)
        for col in range(sudoku_logic.SIZE)
        if puzzle[row][col] == sudoku_logic.EMPTY
        and board[row][col] != solution[row][col]
    ]
    if not candidates:
        return jsonify({'error': 'No empty or incorrect cells available for a hint'}), 400

    row, col = random.choice(candidates)
    return jsonify({'row': row, 'col': col, 'value': solution[row][col]})

if __name__ == '__main__':
    app.run(debug=True)