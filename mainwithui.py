import pygame
from LogicChess import ChessGame
from UI import *
from constant import *

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Chess Game")
        self.clock = pygame.time.Clock()

        self.game = ChessGame()
        self.board = self.game.get_board()
        self.game_menu = GameMenu()
        self.game_state = MAIN_MENU

        self.running = True
        self.selected_square = None
        self.legal_targets = []

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)
            self.handle_events()
            self.update(dt)
            self.draw(self.screen)
        pygame.quit()

    def draw(self, surface):
        draw_background(surface)
        if self.game_state == MAIN_MENU:
            self.game_menu.show_blinking_text(surface)
        elif self.game_state == MAIN_MENU_WITH_BUTTONS:
            self.game_menu.display_choice_overlay(surface)
        elif self.game_state == PVP_MODE:
            draw_board(surface, self.board)
            if self.selected_square:
                draw_selected_square(surface, self.selected_square)
            if self.legal_targets:
                draw_legal_moves(surface, self.legal_targets)
        pygame.display.update()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if self.game_state == MAIN_MENU:
                if self.game_menu.is_blinking_text_clicked(event):
                    self.game_state = MAIN_MENU_WITH_BUTTONS
            elif self.game_state == MAIN_MENU_WITH_BUTTONS:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.game_state = PVP_MODE
            elif self.game_state == PVP_MODE:
                if event.type == pygame.MOUSEBUTTONDOWN:
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

                        # Check if pawn promotion to Queen
                        from_sq = chess.parse_square(initial_square)
                        to_sq = chess.parse_square(final_square)
                        piece = self.board.piece_at(from_sq)

                        if piece and piece.piece_type == chess.PAWN:
                            if chess.square_rank(to_sq) in [0, 7]:  # Hàng cuối
                                move_uci += "q" 

                        # Check if the move is legal
                        if move_uci in self.game.get_legal_moves():
                            self.game.push_move(move_uci)
                            self.board = self.game.get_board()
                        self.selected_square = None
                        self.legal_targets = []

    def update(self, dt):
        if self.game_state == MAIN_MENU:
            self.game_menu.blink_the_text(dt)
        if self.game.is_game_over():
            print("🏁 Trò chơi kết thúc! Kết quả:", self.game.get_game_result())
            pygame.time.delay(3000)
            self.running = False

if __name__ == "__main__":
    game = Game()
    game.run()
