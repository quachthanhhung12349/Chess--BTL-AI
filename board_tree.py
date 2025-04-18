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

def order_moves(board):
    return sorted(board.legal_moves,
                  key=lambda move: (board.gives_check(move), board.is_capture(move)),
                  reverse=True)


def find_best_move(node, max_depth, alpha=-1000000, beta=1000000):
    # Base case: leaf node evaluation
    if node.depth == max_depth or node.board.is_game_over():
        if node.board.is_checkmate():
            # Assign worst possible value for checkmate
            node.minimax_value = -1000000 if node.board.turn == chess.WHITE else 1000000
        else:
            node.minimax_value = count_material(node.board)
        return node.minimax_value

    move_order = order_moves(node.board)  # Your move ordering function

    if node.board.turn == chess.WHITE:  # Maximizing player
        max_value = -1000000
        best_move = None
        for move in move_order:
            # Create child node
            temp_board = node.board.copy()
            temp_board.push(move)
            child_node = BoardTreeNode(temp_board, not node.color, node.depth + 1, move)
            node.children.append(child_node)

            # Recursive call with current alpha/beta
            current_value = find_best_move(child_node, max_depth, alpha, beta)

            # Update max value and best move
            if current_value > max_value:
                max_value = current_value
                best_move = move
                node.minimax_move = best_move
                node.minimax_value = max_value

            # Update alpha and check pruning
            alpha = max(alpha, max_value)
            if alpha >= beta:
                break  # Beta cutoff

        return max_value

    else:  # Minimizing player
        min_value = 1000000
        best_move = None
        for move in move_order:
            # Create child node
            temp_board = node.board.copy()
            temp_board.push(move)
            child_node = BoardTreeNode(temp_board, not node.color, node.depth + 1, move)
            node.children.append(child_node)

            # Recursive call with current alpha/beta
            current_value = find_best_move(child_node, max_depth, alpha, beta)

            # Update min value and best move
            if current_value < min_value:
                min_value = current_value
                best_move = move
                node.minimax_move = best_move
                node.minimax_value = min_value

            # Update beta and check pruning
            beta = min(beta, min_value)
            if alpha >= beta:
                break  # Alpha cutoff

        return min_value



if __name__ == "__main__":
    board1 = chess.Board()
    board1.push_san("e2e4")
    board1.push_san("e7e5")
    board1.push_san("g1f3")
    board1.push_san("b8c6")
    board1.push_san("f1c4")
    board1.push_san("c6d4")
    board1.push_san("f3e5")
    board1.push_san("d8g5")
    board1.push_san("e5f7")

    node1 = BoardTreeNode(board1, True, 0, None)


    tic = time.perf_counter()
    print(find_best_move(node1, 4))
    print(node1.minimax_move)

    toc = time.perf_counter()
    print(toc-tic)



