import chess
piece_values = [0, 100, 300, 330, 500, 900, 10000]

def count_material(board):
    material = [0, 0]
    for i in range(0, 64):
        if board.piece_at(i) is not None:
            material[board.color_at(i)] += piece_values[board.piece_type_at(i)]

    return material[1] - material[0]