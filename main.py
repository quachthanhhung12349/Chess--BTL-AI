import chess
import random
import time

piece_values = [0, 1, 3, 3, 5, 9, 1000]

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
    legal_moves = list(board.legal_moves)
    board.push_san(str(random.choice(legal_moves)))
    print(board)
    print("")
print(board.outcome())





