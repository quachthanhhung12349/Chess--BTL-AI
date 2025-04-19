import pygame
from LogicChess import *
from UI import *
from constant import *

class Game:
    def __init__(self):
        pygame.init()

        self.click_sound = pygame.mixer.Sound('assets/mouseClick.wav')
        pygame.mixer.music.load('assets/chess_music.mp3')
        pygame.mixer.music.play(-1)
        volume = 0.5
        pygame.mixer.music.set_volume(volume)
        self.mouse_clicked = False

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Chess Game")
        self.clock = pygame.time.Clock()

        self.game = ChessGame()
        self.board = self.game.get_board()
        self.game_menu = GameMenu()
        self.game_state = MAIN_MENU
        self.game_mode = None

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
        elif self.game_state == GAME_MODE:
            draw_board(surface, self.board)
            if self.selected_square:
                draw_selected_square(surface, self.selected_square)
            if self.legal_targets:
                draw_legal_moves(surface, self.legal_targets)
        pygame.display.update()

    def handle_player_click(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        mouse_x, mouse_y = pygame.mouse.get_pos()
        row = mouse_y // SQUARE_SIZE
        col = mouse_x // SQUARE_SIZE

        if not (0 <= row < 8 and 0 <= col < 8):
            return  # Click ra ngoài bàn cờ

        square = position_to_chess_square(row, col)
        square_uci = chess.square_name(square)

        if self.selected_square is None:
            selected_piece = self.board.piece_at(square)
            if selected_piece and selected_piece.color == self.board.turn:
                self.selected_square = (row, col)
                legal_moves = self.game.get_legal_moves()
                self.legal_targets = [
                    chess_square_to_position(chess.Move.from_uci(m).to_square)
                    for m in legal_moves
                    if m.startswith(square_uci)
                ]
        else:
            initial_square = chess.square_name(position_to_chess_square(*self.selected_square))
            final_square = square_uci
            move_uci = initial_square + final_square

            from_sq = chess.parse_square(initial_square)
            to_sq = chess.parse_square(final_square)
            piece = self.board.piece_at(from_sq)

            if piece and piece.piece_type == chess.PAWN and chess.square_rank(to_sq) in [0, 7]:
                move_uci += "q"  # Phong hậu

            if move_uci in self.game.get_legal_moves():
                self.game.push_move(move_uci)
                self.board = self.game.get_board()

            self.selected_square = None
            self.legal_targets = []

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.mouse_clicked = True
                self.click_sound.play()

            if event.type == pygame.QUIT:
                self.running = False
            if self.game_state == MAIN_MENU:

                self.game_menu.handle_settings_click(event)
                if self.game_menu.is_blinking_text_clicked(event):
                    self.game_state = MAIN_MENU_WITH_BUTTONS
            elif self.game_state == MAIN_MENU_WITH_BUTTONS:
                selected_mode = self.game_menu.handle_button_click(event)
                if selected_mode == PVP_MODE:
                    self.game_state = GAME_MODE
                    self.game_mode = PVP_MODE
                elif selected_mode == PVE_MODE:
                    self.game_state = GAME_MODE
                    self.game_mode = PVE_MODE
                elif selected_mode == AI_MATCHING_MODE:
                    self.game_state = GAME_MODE
                    self.game_mode = AI_MATCHING_MODE
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.game_state = MAIN_MENU
            elif self.game_state == GAME_MODE:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.game_state = MAIN_MENU_WITH_BUTTONS
                        self.game_mode = None
                        self.selected_square = None
                        self.legal_targets = []
                        self.game.reset_game()

                if self.game_mode == PVP_MODE:
                    self.handle_player_click(event)

                elif self.game_mode == PVE_MODE:
                    if self.board.turn == chess.WHITE:
                        self.handle_player_click(event)

    def update(self, dt):
        if self.game_state == MAIN_MENU:
            self.game_menu.blink_the_text(dt)
        if self.game_state == GAME_MODE and self.game_mode == PVE_MODE and self.board.turn == chess.BLACK:
            """AI random"""
            legal_moves = list(self.board.legal_moves)
            if legal_moves:
                import random
                move = random.choice(legal_moves)
                self.board.push(move)
        #     """AI minimax"""
        #     _, best_move = minimax(self.board, depth=3, alpha=float('-inf'), beta=float('inf'), is_maximizing=True)
        #     if best_move:
        #         self.board.push(best_move)
        if self.game.is_game_over():
            print("🏁 Trò chơi kết thúc! Kết quả:", self.game.get_game_result())
            pygame.time.delay(3000)
            self.running = False

if __name__ == "__main__":
    game = Game()
    game.run()