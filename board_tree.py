import chess
import time

import evaluation_advanced
from evaluation_basic import count_material

MAX_DEPTH = 4
BLUNDER_THRESHOLD = 2
class BoardTreeNode:
    __slots__ = ['children', 'board', 'evaluation', 'depth', 'minimax_value', 'minimax_move',
                 'move']
    def __init__(self, board, depth, move):
        self.children = []
        self.board = board
        self.evaluation = count_material(board)  # Assume count_material is defined
        self.depth = depth
        self.minimax_move = None
        self.move = move
        if board.turn == chess.WHITE:
            self.minimax_value = -1000000
        else:
            self.minimax_value = 1000000

def order_moves_basic(board):
    return sorted(board.legal_moves,
                  key=lambda move: (board.gives_check(move), board.is_capture(move)),
                  reverse=True)

def hang_checkmate(board):
    move_order = order_moves_basic(board)
    for move in move_order:
        board.push(move)
        if board.is_checkmate():
            return True
        if not board.is_check():
            break
        board.pop()
    return False

def is_blunder(board, move, prev_board, max_depth=2):
    node = BoardTreeNode(board, 0, move)
    if board.turn == chess.WHITE:
        if find_best_move(node, max_depth, True) - count_material(prev_board) > BLUNDER_THRESHOLD:
            return True
    else:
        if find_best_move(node, max_depth, True) - count_material(prev_board) < -BLUNDER_THRESHOLD:
            return False
    return False

def order_moves(board):
    move_scores = []
    for move in board.legal_moves:
        score = 0
        # MVV-LVA for captures
        if board.is_capture(move):
            captured_piece = board.piece_at(move.to_square)
            attacker_piece = board.piece_at(move.from_square)
            if captured_piece and attacker_piece:
                # Assign piece values (e.g., pawn=1, knight=3, ..., queen=9)
                piece_value = {chess.PAWN: 100, chess.KNIGHT: 300, chess.BISHOP: 330,
                               chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 10000}
                captured_val = piece_value.get(captured_piece.piece_type, 0)
                attacker_val = piece_value.get(attacker_piece.piece_type, 0)
                score += captured_val * 10 - attacker_val  # MVV-LVA
        # Check bonus
        if board.gives_check(move):
            score += 100
        move_scores.append((score, move))
    # Sort by descending score
    move_scores.sort(key=lambda x: -x[0])
    return [move for (score, move) in move_scores]

cnt = 0

def find_best_move(node, max_depth, alpha=-1000000, beta=1000000):
    global cnt
    if node.depth == max_depth or node.board.is_game_over():
        if node.board.is_checkmate():
            node.minimax_value = -1000000 if node.board.turn == chess.WHITE else 1000000
        else:
            node.minimax_value = evaluation_advanced.evaluation(node.board)
        return node.minimax_value

    move_order = order_moves(node.board)

    if node.board.turn == chess.WHITE:
        max_value = -1000000
        best_move = None
        for move in move_order:
            # Create child node
            node.board.push(move)
            child_node = BoardTreeNode(node.board, node.depth + 1, move)
            node.children.append(child_node)


            current_value = find_best_move(child_node, max_depth, alpha, beta)
            node.board.pop()
            # Update max value and best move
            if current_value > max_value:
                max_value = current_value
                node.minimax_move = move
                node.minimax_value = max_value

            cnt += 1
            alpha = max(alpha, max_value)
            if alpha >= beta:
                break

        return node.minimax_value

    else:  # Minimizing player
        min_value = 1000000
        best_move = None
        for move in move_order:
            # Create child node
            node.board.push(move)
            child_node = BoardTreeNode(node.board, node.depth + 1, move)
            node.children.append(child_node)
            current_value = find_best_move(child_node, max_depth, alpha, beta)
            node.board.pop()

            if current_value < min_value:
                min_value = current_value
                node.minimax_move = move
                node.minimax_value = min_value

            cnt += 1
            beta = min(beta, min_value)
            if alpha >= beta:
                break

        return node.minimax_value


if __name__ == "__main__":
    board1 = chess.Board()


    node1 = BoardTreeNode(board1,0, None)

    tic = time.perf_counter()
    print(find_best_move(node1, 5))
    print(node1.minimax_move)

    print(cnt)
    toc = time.perf_counter()
    print(toc - tic)



