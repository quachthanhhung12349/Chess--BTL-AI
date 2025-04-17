import chess
piece_values = [0, 1, 3, 3, 5, 9, 1000]

def count_material(board):
    material = [0, 0]
    for i in range(0, 64):
        if board.piece_at(i) is not None:
            material[board.color_at(i)] += board.piece_type_at(i)

    return material[1] - material[0]