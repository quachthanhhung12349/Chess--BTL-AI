import chess
import time

from evaluation_basic import evaluate

MAX_DEPTH = 4

class BoardTreeNode:
    __slots__ = ['children', 'board', 'color', 'evaluation', 'depth', 'minimax_value', 'minimax_move',
                 'move', 'alpha', 'beta']
    def __init__(self, board, color, depth, move):
        self.children = []
        self.board = board
        self.color = color
        self.evaluation = evaluate(board)  # Assume count_material is defined
        self.depth = depth
        self.minimax_move = None
        self.move = move
        self.alpha = -1000000
        self.beta = 1000000
        if color:
            self.minimax_value = -1000000
        else:
            self.minimax_value = 1000000





def minimax(current_node):
    if not len(current_node.children):
        current_node.minimax_value = current_node.evaluation
        return

    if current_node.color:
        max_value = -1000000
        max_move = None
        for node in current_node.children:
            if max_value < node.evaluation:
                max_value = node.evaluation
                max_move = node.move
        current_node.minimax_value = max_value
        current_node.minimax_move = max_move
        return

    min_value = 1000000
    min_move = None
    for node in current_node.children:
        if min_value > node.evaluation:
            min_value = node.evaluation
            max_move = node.move
    current_node.minimax_value = min_value
    current_node.minimax_move = min_move
    return


def minimax_alpha_beta(current_node):
    if not len(current_node.children):
        current_node.minimax_value = current_node.evaluation
        return

    if current_node.color:
        max_value = -1000000
        max_move = None
        for node in current_node.children:
            if max_value < node.evaluation:
                max_value = node.evaluation
                max_move = node.move
                if max_value >= current_node.beta:
                    break
        current_node.minimax_value = max_value
        current_node.minimax_move = max_move
        current_node.alpha = max(current_node.alpha, max_value)
        return

    min_value = 1000000
    min_move = None
    for node in current_node.children:
        if min_value > node.evaluation:
            min_value = node.evaluation
            min_move = node.move
            if min_value <= current_node.alpha:
                break
    current_node.minimax_value = min_value
    current_node.minimax_move = min_move
    current_node.beta = min(current_node.beta, min_value)
    return


def find_best_move(root_node, max_depth):
    stack = [(root_node, False)]

    while stack:
        node, is_processed = stack.pop()

        if node.depth >= max_depth:
            continue

        if not is_processed:
            for move in node.board.legal_moves:
                node.board.push(move)
                temp_board = node.board.copy()
                node.board.pop()

                child_node = BoardTreeNode(temp_board, not node.color, node.depth + 1, move)

                node.children.append(child_node)
                stack.append((child_node, False))
            minimax(node)
            stack.append((node, True))
    return root_node.minimax_move

def find_best_move_alpha_beta(root_node, max_depth):
    stack = [(root_node, False)]

    while stack:
        node, is_processed = stack.pop()

        if node.depth >= max_depth:
            continue

        if not is_processed:
            for move in node.board.legal_moves:
                node.board.push(move)
                temp_board = node.board.copy()
                node.board.pop()

                child_node = BoardTreeNode(temp_board, not node.color, node.depth + 1, move)



                node.children.append(child_node)
                stack.append((child_node, False))
            minimax_alpha_beta(node)
            stack.append((node, True))
    return root_node.minimax_move



board1 = chess.Board()

node1 = BoardTreeNode(board1, True, 0, None)

tic = time.perf_counter()
print(find_best_move(node1, 3))

toc = time.perf_counter()
print(toc-tic)

tic = time.perf_counter()
print(find_best_move_alpha_beta(node1, 3))

toc = time.perf_counter()
print(toc-tic)



