import pygame
from LogicChess import ChessGame
from UI import *
from constant import *

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Chess Game")
        self.font = pygame.font.SysFont("comicsans", 30)

        self.game = ChessGame()
        self.board = self.game.get_board()

        self.running = True
        self.selected_square = None
        self.legal_targets = []

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw(self.screen)
        pygame.quit()

    def draw(self, surface):
        draw_board(surface, self.board, self.font)
        if self.selected_square:
            draw_selected_square(surface, self.selected_square)
        if self.legal_targets:
            draw_legal_moves(surface, self.legal_targets)
        pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_position_x, mouse_position_y = pygame.mouse.get_pos()
                row = mouse_position_y // SQUARE_SIZE
                col = mouse_position_x // SQUARE_SIZE
                square = position_to_chess_square(row, col)
                square_uci = chess.square_name(square)

                if self.selected_square is None:
                    selected_piece = self.board.piece_at(square)
                    if selected_piece and selected_piece.color == self.board.turn:
                        self.selected_square = (row, col)
                        legal_moves =  self.game.get_legal_moves()
                        self.legal_targets = [
                            chess_square_to_position(chess.Move.from_uci(m).to_square)
                            for m in legal_moves
                            if m.startswith(square_uci)
                        ]
                
                else:

                    initial_square = chess.square_name(position_to_chess_square(*self.selected_square))
                    final_square = square_uci
                    move_uci = initial_square + final_square
                    if move_uci in self.game.get_legal_moves():
                        self.game.push_move(move_uci)
                        self.board = self.game.get_board()
                    self.selected_square = None
                    self.legal_targets = []

    def update(self):
        if self.game.is_game_over():
            print("🏁 Trò chơi kết thúc! Kết quả:", self.game.get_game_result())
            pygame.time.delay(3000)
            self.running = False

if __name__ == "__main__":
    game = Game()
    game.run()
