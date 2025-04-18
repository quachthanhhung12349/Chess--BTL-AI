import chess
import random
import time

from board_tree import find_best_move, BoardTreeNode, find_best_move
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

if __name__ == "__main__":
    board = chess.Board()

    legal_moves = []
    while True:
        node2 = BoardTreeNode(board, True, 0, None)
        find_best_move(node2, 5)
        best_move = node2.minimax_move

        print(best_move)
        board.push_san(str(best_move))
        print(board)
        print("")
        if game_end(board):
            break

        legal_moves = list(board.legal_moves)
        board.push_san(str(random.choice(legal_moves)))
        print(board)
        print("")

        if game_end(board):
            break


    print(board.outcome())

    print(count_material(board))






