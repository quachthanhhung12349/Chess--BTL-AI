import pygame
import chess
from LogicChess import ChessGame
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

        self.gamemode_menu_active = False
        self.gamemode_buttons = []
        self.create_gamemode_buttons()

        self.player1_time = 0
        self.player2_time = 0
        self.current_player = chess.WHITE
        self.font = pygame.font.SysFont('comicsans', 30)
        self.game_start_time = 0

        self.resign_white_button = Button(WIDTH - 132, HEIGHT - 120, 120, 40, "Resign", "lightcoral")
        self.resign_black_button = Button(12, 80, 120, 40, "Resign", "lightcoral")

        self.game_over = False
        self.game_result_text = ""
        self.game_over_time = 0
        self.rematch_button = None
        self.menu_button = None

        self.base_time = 0  # thời gian ban đầu theo chế độ
        self.increment = 3  # số giây cộng thêm sau mỗi nước đi

        self.captured_pieces_white = []
        self.captured_pieces_black = []

    def handle_game_over(self):
        self.game_over = True
        self.game_result_text = self.game.get_game_result()
        self.game_over_time = pygame.time.get_ticks()
        button_width = 200
        button_height = 50
        start_x = WIDTH // 2 - button_width // 2
        start_y_rematch = HEIGHT // 2 + 50
        start_y_menu = HEIGHT // 2 + 120
        self.rematch_button = Button(start_x, start_y_rematch, button_width, button_height, "Rematch", "lightgreen")
        self.menu_button = Button(start_x, start_y_menu, button_width, button_height, "Main Menu", "lightcoral")
        self.game_state = GAME_OVER_SCREEN

    def create_gamemode_buttons(self):
        button_width = 200
        button_height = 50
        start_x = WIDTH // 2 - button_width // 2
        start_y = HEIGHT // 2 - (button_height * 3 // 2 + 20)
        button_texts = ["Blitz", "Rapid", "Standard", "No Timer"]
        self.gamemode_buttons = [
            Button(start_x, start_y + i * (button_height + 10), button_width, button_height, text, "lightgray")
            for i, text in enumerate(button_texts)
        ]

    def reset_timer(self):
        self.player1_time = self.base_time
        self.player2_time = self.base_time
        self.current_player = chess.WHITE
        self.game_start_time = pygame.time.get_ticks()

    def update_timer(self, dt):
        if self.game_mode in [PVP_MODE, PVE_MODE] and self.game_mode != "NO_TIMER" and not self.game.is_game_over():
            time_elapsed = dt / 1000.0  # Chuyển đổi milliseconds sang giây
            if self.current_player == chess.WHITE:
                self.player1_time -= time_elapsed
                if self.player1_time < 0:
                    self.game.declare_winner(chess.BLACK)  # đen thắng
            else:
                self.player2_time -= time_elapsed
                if self.player2_time < 0:
                    self.game.declare_winner(chess.WHITE)  # trắng thắng

    def format_time(self, seconds):
        if seconds < 0:
            return "00:00"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02}:{secs:02}"

    def draw_timer(self, surface):
        timer1_text = self.font.render(self.format_time(self.player2_time), True, (0, 0, 0))
        timer2_text = self.font.render(self.format_time(self.player1_time), True, (0, 0, 0))
        surface.blit(timer1_text, (30, 30))
        surface.blit(timer2_text, (WIDTH - timer2_text.get_width() - 30, HEIGHT - timer2_text.get_height() - 30))

    def draw_captured_pieces(self, surface):
        captured_piece_size = SQUARE_SIZE // 2
        padding = 5

        # vẽ quân cờ đen bị ăn (bên trái)
        start_x_black = (WIDTH - BOARD_SIZE) // 2 - captured_piece_size - padding
        current_y_black = (HEIGHT - BOARD_SIZE) // 2 + 150
        current_col_black = 0
        for i, piece in enumerate(self.captured_pieces_black):
            if i > 0 and current_y_black > HEIGHT - 400 :
                current_y_black = (HEIGHT - BOARD_SIZE) // 2 + 150
                current_col_black += 1
                start_x_black -= 20  # vẽ ở cột tiếp theo

            img = load_piece_texture().get(piece.symbol())
            scaled_img = pygame.transform.scale(img, (captured_piece_size, captured_piece_size))
            img_rect = scaled_img.get_rect(
                topleft=(start_x_black - current_col_black * (captured_piece_size + padding), current_y_black))
            surface.blit(scaled_img, img_rect)
            current_y_black += captured_piece_size + padding

        # vẽ quân cờ trắng bị ăn (bên phải)
        start_x_white = (WIDTH + BOARD_SIZE) // 2 + padding
        current_y_white = (HEIGHT - 200)
        current_col_white = 0
        for i, piece in enumerate(self.captured_pieces_white):
            if i > 0 and current_y_white < 100:
                current_y_white = (HEIGHT - 200)
                current_col_white += 1
                start_x_white += 20 # vẽ ở cột tiếp theo

            img = load_piece_texture().get(piece.symbol())
            scaled_img = pygame.transform.scale(img, (captured_piece_size, captured_piece_size))
            img_rect = scaled_img.get_rect(
                topleft=(start_x_white + current_col_white * (captured_piece_size + padding), current_y_white))
            surface.blit(scaled_img, img_rect)
            current_y_white -= captured_piece_size + padding

    def draw(self, surface):
        if self.game_state in [MAIN_MENU, MAIN_MENU_WITH_BUTTONS]:
            draw_background(surface)
            if self.game_state == MAIN_MENU:
                self.game_menu.show_blinking_text(surface)
            elif self.game_state == MAIN_MENU_WITH_BUTTONS:
                self.game_menu.display_choice_overlay(surface)
        elif self.game_state == GAME_MODE:
            surface.fill((139, 69, 19))  # nâu đậm
            # mid
            board_x = (WIDTH - BOARD_SIZE) // 2
            board_y = (HEIGHT - BOARD_SIZE) // 2
            board_surface = surface.subsurface((board_x, board_y, BOARD_SIZE, BOARD_SIZE))
            draw_board(board_surface, self.board)
            if self.selected_square:
                selected_row, selected_col = self.selected_square
                draw_selected_square(surface.subsurface((board_x, board_y, BOARD_SIZE, BOARD_SIZE)),
                                     (selected_row, selected_col))
            if self.legal_targets:
                legal_targets_on_board = [(r, c) for r, c in self.legal_targets]
                draw_legal_moves(surface.subsurface((board_x, board_y, BOARD_SIZE, BOARD_SIZE)), legal_targets_on_board)
            self.draw_timer(surface)
            self.resign_white_button.show_button(surface)
            self.resign_black_button.show_button(surface)
            self.draw_captured_pieces(surface)
        elif self.game_state == GAME_MODE_MENU:
            draw_background(surface)
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            surface.blit(overlay, (0, 0))
            for button in self.gamemode_buttons:
                button.show_button(surface)
        elif self.game_state == GAME_OVER_SCREEN:
            surface.fill((50, 50, 50))
            font_large = pygame.font.SysFont('comicsans', 60)
            font_small = pygame.font.SysFont('comicsans', 30)
            result_surface = font_large.render("Game Over!", True, (255, 255, 255))
            result_rect = result_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
            surface.blit(result_surface, result_rect)

            result_text_surface = font_small.render(f"Result: {self.game_result_text}", True, (255, 255, 255))
            result_text_rect = result_text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 10))
            surface.blit(result_text_surface, result_text_rect)

            if pygame.time.get_ticks() - self.game_over_time > 4000:
                if self.rematch_button:
                    self.rematch_button.show_button(surface)
                if self.menu_button:
                    self.menu_button.show_button(surface)
        pygame.display.update()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS)
            self.handle_events()
            self.update(dt)
            self.draw(self.screen)
        pygame.quit()

    def handle_player_click(self, event):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return

        mouse_x, mouse_y = pygame.mouse.get_pos()
        board_x = (WIDTH - BOARD_SIZE) // 2
        board_y = (HEIGHT - BOARD_SIZE) // 2
        relative_x = mouse_x - board_x
        relative_y = mouse_y - board_y

        if 0 <= relative_x < BOARD_SIZE and 0 <= relative_y < BOARD_SIZE:
            col = relative_x // SQUARE_SIZE
            row = relative_y // SQUARE_SIZE

            if not (0 <= row < 8 and 0 <= col < 8):
                return  # Click ra ngoài bàn cờ

            square = position_to_chess_square(row, col)
            square_uci = chess.square_name(square)

            if self.selected_square is None:
                selected_piece = self.board.piece_at(square)
                if selected_piece and selected_piece.color == self.board.turn and self.game_mode in [PVP_MODE, PVE_MODE,
                                                                                                     "NO_TIMER"]:
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

                if move_uci in self.game.get_legal_moves() and self.game_mode in [PVP_MODE, PVE_MODE, "NO_TIMER"]:
                    # Kiểm tra xem có quân cờ nào bị ăn không
                    captured_piece = self.board.piece_at(to_sq)
                    if captured_piece:
                        if captured_piece.color == chess.WHITE:
                            self.captured_pieces_white.append(captured_piece)
                        else:
                            self.captured_pieces_black.append(captured_piece)

                    self.game.push_move(move_uci)
                    self.board = self.game.get_board()
                    if self.current_player == chess.WHITE and self.game_mode != "NO_TIMER":
                        self.player1_time += self.increment
                    elif self.current_player == chess.BLACK and self.game_mode != "NO_TIMER":
                        self.player2_time += self.increment
                    self.current_player = not self.current_player
                    self.selected_square = None
                    self.legal_targets = []
                else:
                    # Nếu click vào một ô khác khi đang chọn quân, bỏ chọn hoặc chọn quân mới
                    selected_piece = self.board.piece_at(square)
                    if selected_piece and selected_piece.color == self.board.turn and self.game_mode in [PVP_MODE,
                                                                                                         PVE_MODE,
                                                                                                         "NO_TIMER"]:
                        self.selected_square = (row, col)
                        legal_moves = self.game.get_legal_moves()
                        self.legal_targets = [
                            chess_square_to_position(chess.Move.from_uci(m).to_square)
                            for m in legal_moves
                            if m.startswith(square_uci)
                        ]
                    else:
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
                if selected_mode:
                    self.game_mode = selected_mode
                    self.game_state = GAME_MODE_MENU
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.game_state = MAIN_MENU
            elif self.game_state == GAME_MODE_MENU:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.game_state = MAIN_MENU_WITH_BUTTONS
                for button in self.gamemode_buttons:
                    if button.is_clicked(event):
                        if button.button_text == "Blitz":
                            self.base_time = 180  # 3p
                        elif button.button_text == "Rapid":
                            self.base_time = 600  # 10p
                        elif button.button_text == "Standard":
                            self.base_time = 1800  # 30p
                        elif button.button_text == "No Timer":
                            self.game_mode = "NO_TIMER"
                            self.game_state = GAME_MODE
                            break
                        self.reset_timer()
                        self.game_state = GAME_MODE
                        break
            elif self.game_state == GAME_MODE:
                # if event.type == pygame.KEYDOWN:
                #   if event.key == pygame.K_ESCAPE:
                #      self.game_state = MAIN_MENU_WITH_BUTTONS
                #     self.game_mode = None
                #     self.selected_square = None
                #     self.legal_targets = []
                #    self.game.reset_game()

                if self.resign_white_button.is_clicked(event):
                    self.game.declare_winner(chess.BLACK)
                    self.handle_game_over()
                elif self.resign_black_button.is_clicked(event):
                    self.game.declare_winner(chess.WHITE)
                    self.handle_game_over()

                if self.game_mode in [PVP_MODE, PVE_MODE, "NO_TIMER"]:
                    self.handle_player_click(event)

                elif self.game_mode == PVE_MODE and self.board.turn == chess.BLACK:
                    """AI random"""
                    legal_moves = list(self.board.legal_moves)
                    if legal_moves:
                        import random
                        move = random.choice(legal_moves)
                        self.game.push_move(move)
                        self.board = self.game.get_board()
                        self.current_player = not self.current_player  # Chuyển lượt
            #         """AI minimax"""
            #         _, best_move = minimax(self.board, depth=3, alpha=float('-inf'), beta=float('inf'), is_maximizing=True)
            #         if best_move:
            #             self.board.push(best_move)
            #             self.current_player = not self.current_player # Chuyển lượt
            elif self.game_state == GAME_OVER_SCREEN:
                if pygame.time.get_ticks() - self.game_over_time > 4000:
                    if self.rematch_button and self.rematch_button.is_clicked(event):
                        print("Rematch button clicked!")
                        self.game_state = GAME_MODE
                        print(f"Game state after rematch: {self.game_state}")
                        self.game.reset_game()
                        print("Game reset!")
                        self.reset_timer()
                        print(f"Player 1 time: {self.player1_time}, Player 2 time: {self.player2_time}")
                        self.selected_square = None
                        self.legal_targets = []
                        self.game_over = False
                        self.game_result_text = ""
                    elif self.menu_button and self.menu_button.is_clicked(event):
                        self.game_state = MAIN_MENU
                        self.game.reset_game()
                        self.reset_timer()
                        self.selected_square = None
                        self.legal_targets = []
                        self.game_over = False
                        self.game_result_text = ""

    def update(self, dt):
        if self.game_state == MAIN_MENU:
            self.game_menu.blink_the_text(dt)
        elif self.game_state == GAME_MODE:
            if self.game_mode != "NO_TIMER":
                self.update_timer(dt)
                if self.game.is_game_over() and not self.game_over:
                    self.handle_game_over()


if __name__ == "__main__":
    game = Game()
    game.run()