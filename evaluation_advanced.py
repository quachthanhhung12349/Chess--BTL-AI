import chess
import time

piece_values = [0, 100, 300, 330, 500, 900, 10000]

PAWN_TABLE = [
    [ 0,   0,   0,   0,   0,   0,   0,   0],  # a8-h8 (promotion ranks)
    [50,  50,  50,  50,  50,  50,  50,  50],  # a7-h7 (about to promote)
    [10,  10,  20,  30,  30,  20,  10,  10],  # a6-h6
    [ 5,   5,  10,  27,  27,  10,   5,   5],  # a5-h5
    [ 0,   0,   0,  25,  25,   0,   0,   0],  # a4-h4 (central control)
    [ 5,  -5, -10,   0,   0, -10,  -5,   5],  # a3-h3
    [ 5,  10,  10, -25, -25,  10,  10,   5],  # a2-h2 (penalize starting row)
    [ 0,   0,   0,   0,   0,   0,   0,   0],  # a1-h1 (never used)
]

KNIGHT_TABLE = [
    [-50, -40, -30, -30, -30, -30, -40, -50],  # a8-h8 (edges bad)
    [-40, -20,   0,   5,   5,   0, -20, -40],  # a7-h7
    [-30,   0,  10,  15,  15,  10,   0, -30],  # a6-h6
    [-30,   5,  15,  20,  20,  15,   5, -30],  # a5-h5 (central peak)
    [-30,   0,  15,  20,  20,  15,   0, -30],  # a4-h4
    [-30,   5,  10,  15,  15,  10,   5, -30],  # a3-h3
    [-40, -20,   0,   5,   5,   0, -20, -40],  # a2-h2
    [-50, -40, -30, -30, -30, -30, -40, -50],  # a1-h1
]

BISHOP_TABLE = [
    [-20, -10, -10, -10, -10, -10, -10, -20],  # a8-h8
    [-10,   0,   0,   0,   0,   0,   0, -10],  # a7-h7
    [-10,   0,   5,  10,  10,   5,   0, -10],  # a6-h6
    [-10,   5,   5,  10,  10,   5,   5, -10],  # a5-h5
    [-10,   0,  10,  10,  10,  10,   0, -10],  # a4-h4 (central diagonals)
    [-10,  10,  10,  10,  10,  10,  10, -10],  # a3-h3
    [-10,   5,   0,   0,   0,   0,   5, -10],  # a2-h2
    [-20, -10, -10, -10, -10, -10, -10, -20],  # a1-h1
]

ROOK_TABLE = [
    [  0,   0,   0,   5,   5,   0,   0,   0],  # a8-h8 (central files)
    [  5,  10,  10,  10,  10,  10,  10,   5],  # a7-h7 (encourage 7th rank)
    [ -5,   0,   0,   0,   0,   0,   0,  -5],  # a6-h6
    [ -5,   0,   0,   0,   0,   0,   0,  -5],  # a5-h5
    [ -5,   0,   0,   0,   0,   0,   0,  -5],  # a4-h4
    [ -5,   0,   0,   0,   0,   0,   0,  -5],  # a3-h3
    [ -5,   0,   0,   0,   0,   0,   0,  -5],  # a2-h2
    [  0,   0,   0,   0,   0,   0,   0,   0],  # a1-h1
]

QUEEN_TABLE = [
    [-20, -10, -10,  -5,  -5, -10, -10, -20],  # a8-h8
    [-10,   0,   0,   0,   0,   0,   0, -10],  # a7-h7
    [-10,   0,   5,   5,   5,   5,   0, -10],  # a6-h6
    [ -5,   0,   5,   5,   5,   5,   0,  -5],  # a5-h5 (central control)
    [  0,   0,   5,   5,   5,   5,   0,  -5],  # a4-h4
    [-10,   5,   5,   5,   5,   5,   0, -10],  # a3-h3
    [-10,   0,   5,   0,   0,   0,   0, -10],  # a2-h2
    [-20, -10, -10,  -5,  -5, -10, -10, -20],  # a1-h1
]

KING_MIDDLEGAME_TABLE = [
    [-30, -40, -40, -50, -50, -40, -40, -30],  # a8-h8
    [-30, -40, -40, -50, -50, -40, -40, -30],  # a7-h7
    [-30, -40, -40, -50, -50, -40, -40, -30],  # a6-h6
    [-30, -40, -40, -50, -50, -40, -40, -30],  # a5-h5
    [-20, -30, -30, -40, -40, -30, -30, -20],  # a4-h4
    [-10, -20, -20, -20, -20, -20, -20, -10],  # a3-h3
    [ 20,  20,   0,   0,   0,   0,  20,  20],  # a2-h2 (encourage castling)
    [ 20,  30,  10,   0,   0,  10,  30,  20],  # a1-h1 (king safety)
]

KING_ENDGAME_TABLE = [
    [-50, -40, -30, -20, -20, -30, -40, -50],  # a8-h8
    [-30, -20, -10,   0,   0, -10, -20, -30],  # a7-h7
    [-30, -10,  20,  30,  30,  20, -10, -30],  # a6-h6
    [-30, -10,  30,  40,  40,  30, -10, -30],  # a5-h5 (centralization)
    [-30, -10,  30,  40,  40,  30, -10, -30],  # a4-h4
    [-30, -10,  20,  30,  30,  20, -10, -30],  # a3-h3
    [-30, -30,   0,   0,   0,   0, -30, -30],  # a2-h2
    [-50, -30, -30, -30, -30, -30, -30, -50],  # a1-h1
]

def endgame(board):
    non_pawn_king_value = [0, 0]
    for i in range(0, 64):
       if board.piece_at(i) is chess.KNIGHT:
           non_pawn_king_value[board.color_at(i)] += piece_values[2]
       elif board.piece_at(i) is chess.BISHOP:
           non_pawn_king_value[board.color_at(i)] += piece_values[3]
       elif board.piece_at(i) is chess.ROOK:
           non_pawn_king_value[board.color_at(i)] += piece_values[4]
       elif board.piece_at(i) is chess.QUEEN:
           non_pawn_king_value[board.color_at(i)] += piece_values[5]
    return non_pawn_king_value[0] + non_pawn_king_value[1] <= 2460



def evaluation(board):
    material = [0, 0]
    is_endgame = endgame(board)
    for i in range(0, 64):
        rank = 7 - (i // 8)
        file = i % 8
        if board.piece_at(i) is not None:
            if not board.color_at(i):
                rank = 7 - rank
            if board.piece_at(i).piece_type == 1:
                material[board.color_at(i)] += (piece_values[1] + PAWN_TABLE[rank][file])
            elif board.piece_at(i).piece_type == 2:
                material[board.color_at(i)] += (piece_values[2] + KNIGHT_TABLE[rank][file])
            elif board.piece_at(i).piece_type == 3:
                material[board.color_at(i)] += (piece_values[3] + BISHOP_TABLE[rank][file])
            elif board.piece_at(i).piece_type == 4:
                material[board.color_at(i)] += (piece_values[4] + ROOK_TABLE[rank][file])
            elif board.piece_at(i).piece_type == 5:
                material[board.color_at(i)] += (piece_values[5] + QUEEN_TABLE[rank][file])
            elif board.piece_at(i).piece_type == 6:
                if is_endgame:
                    material[board.color_at(i)] += (piece_values[6] + KING_ENDGAME_TABLE[rank][file])
                else:
                    material[board.color_at(i)] += (piece_values[6] + KING_MIDDLEGAME_TABLE[rank][file])
    return material[1] - material[0]

if __name__ == "__main__":
    board1 = chess.Board()
    board1.push_san("e2e4")

    print(evaluation(board1))
