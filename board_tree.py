import chess

from main import legal_moves


class GameTree:
    def __init__(self, current_board):
        parent_board = current_board
        children_board = []
        evaluation_value = 0

    def extend_game_tree(self):
        legal_moves_list = list(parent_board.legal_moves)

