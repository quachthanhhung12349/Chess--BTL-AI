import chess
import random
import time

from board_tree import find_best_move, BoardTreeNode
from evaluation_basic import count_material


def game_end(chessboard):
    if chessboard.is_checkmate():
        return True
    if chessboard.is_insufficient_material():
        return True
    if chessboard.is_stalemate():
        return True
    if chessboard.can_claim_threefold_repetition():
        return True
    return False


board = chess.Board()

legal_moves = []
while not game_end(board):
    best_move = find_best_move(BoardTreeNode(board, True, 0, None), 3)

    print(best_move)
    board.push_san(str(best_move))
    print(board)
    print("")

    legal_moves = list(board.legal_moves)
    board.push_san(str(random.choice(legal_moves)))
    print(board)
    print("")


print(board.outcome())

print(count_material(board))






