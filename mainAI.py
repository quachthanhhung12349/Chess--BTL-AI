import chess
import random
import time

from board_tree import find_best_move, BoardTreeNode, find_best_move


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
        node2 = BoardTreeNode(board,  0, None)
        find_best_move_iterative(node2, 4)
        best_move = node2.minimax_move

        print(best_move)
        board.push_san(str(best_move))
        print(board)
        print("")
        if game_end(board):
            break

        node3 = BoardTreeNode(board, 0, None)
        find_best_move(node3, 4)
        best_move = node3.minimax_move

        print(best_move)
        board.push_san(str(best_move))
        print(board)
        print("")

        if game_end(board):
            break


    print(board.outcome())

    print(count_material(board))






