
#UI UX controller
import pygame
from constant import *
import tkinter as tk
from tkinter import filedialog


def chess_square_to_position(square):
    row = 7 - chess.square_rank(square) #Convert to row (flip back)
    col = chess.square_file(square) #column index
    return (row, col)

def position_to_chess_square(row, col):
    return chess.square(col, 7 - row) #Convert to square index (flip back

def draw_background(screen):
    background_img = pygame.image.load('assets/startIMG.png')
    background_img = pygame.transform.scale(background_img, (WIDTH, HEIGHT))
    screen.blit(background_img, (0, 0))

def draw_board(screen, board):
    for row in range(ROWS):
        for col in range(COLS):
            rect = pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            color = (234, 235, 200) if (row + col) % 2 == 0 else (119, 154, 88)
            pygame.draw.rect(screen, color, rect)

            square = position_to_chess_square(row, col)
            piece = board.piece_at(square)

            if piece:
                draw_pieces(screen, piece, row, col)

def draw_pieces(screen, piece, row, col):
    symbol = piece.symbol()
    piece_img = load_piece_texture().get(symbol)
    piece_img_center = col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2
    piece_img_rect = piece_img.get_rect(center=piece_img_center)
    screen.blit(piece_img, piece_img_rect)
    pass


def draw_selected_square(screen, selected_square):
    row, col = selected_square
    rect = pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
    pygame.draw.rect(screen, (0, 255, 0), rect, 4)

def draw_legal_moves(screen, legal_moves):
    for row, col in legal_moves:
        color = '#C86464' if (row + col) % 2 == 0 else '#C84646'
        rect = pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
        pygame.draw.rect(screen, color, rect)


# New function to highlight AI moves
def draw_ai_move(screen, from_square, to_square, duration_ms=500):
    from_pos = chess_square_to_position(from_square)
    to_pos = chess_square_to_position(to_square)

    # Highlight the "from" square
    from_rect = pygame.Rect(from_pos[1] * SQUARE_SIZE, from_pos[0] * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
    pygame.draw.rect(screen, (255, 215, 0), from_rect, 4)  # Gold border for "from" square

    # Highlight the "to" square
    to_rect = pygame.Rect(to_pos[1] * SQUARE_SIZE, to_pos[0] * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
    pygame.draw.rect(screen, (255, 165, 0), to_rect, 4)  # Orange border for "to" square

    pygame.display.update()
    pygame.time.delay(duration_ms)  # Show the highlight for 500ms

# def draw_move_history(screen, move_history):
#     font = pygame.font.SysFont('comicsans', 30)
#     pygame.draw.rect(screen, (245, 245, 245), (WIDTH_BOARD + 5, WIDTH // 2 - 200, WIDTH - WIDTH_BOARD, WIDTH // 2))
#     pygame.draw.rect(screen, (0, 0, 0), (WIDTH_BOARD + 5, WIDTH // 2 - 200, WIDTH - WIDTH_BOARD, WIDTH // 2), 2)
#     max_moves_display = WIDTH // 2 // 20
#     start_index = max(0, len(move_history) - max_moves_display)
#     temp_board = chess.Board()
#     move_display_count = 0
#     for i, move in enumerate(move_history[start_index:]): 
#         if move_display_count >= 10:
#             pygame.draw.rect(screen, (245, 245, 245), (WIDTH_BOARD + 5, WIDTH // 2 - 200, WIDTH - WIDTH_BOARD, WIDTH // 2))
#             pygame.draw.rect(screen, (0, 0, 0), (WIDTH_BOARD + 5, WIDTH // 2 - 200, WIDTH - WIDTH_BOARD, WIDTH // 2), 2)
#             move_display_count = 0
        
#         move = chess.Move.from_uci(move)
#         move_str = None
#         if move in temp_board.legal_moves:
#             # Xử lý ăn quân nếu có
#             target_piece = temp_board.piece_at(move.to_square)
#             if target_piece:  # Có quân bị ăn
#                 move_str = f"{temp_board.san(move)}"  # Giữ nguyên kiểu PGN
#             else:
#                 move_str = temp_board.san(move)  # Nếu không ăn quân, hiển thị bình thường
#         move_text = font.render(move_str, True, (0, 0, 0))
#         screen.blit(move_text, (WIDTH_BOARD + 10, WIDTH // 2 - 200 + move_display_count * 40))
#         # temp_board.push(move) if temp_board.is_legal(move) else print("exception") # Cập nhật bàn cờ tạm thời    
#         move_display_count += 1
                      
 
def load_piece_texture():
    piece_imgs = {}
    for symbol, texture_path in PIECE_TEXTURE.items():
        piece_img = pygame.image.load(f'assets/chess_image/{texture_path}').convert_alpha()
        piece_imgs[symbol] = piece_img
    return piece_imgs

class GameMenu():
    def __init__(self):
        self.blinking_text = BlinkingText("Click to start game", (WIDTH // 2, HEIGHT // 2 + 20), text_color='black', blinking_interval=500)

        self.current_volume = 0.5

        self.buttons = []
        self.create_buttons()
        self.settings_button = Button(WIDTH - 140, 20, 135, 40, "Settings", "gray")
        self.settings_popup_visible = False

        self.overlay_alpha = 0
        self.overlay_max_alpha = 180

    def create_buttons(self):
        labels = ["PvP", "PvE"]
        for i, text in enumerate(labels):
            x = WIDTH // 2 - 150
            y = 250 + i * 120
            button = Button(x, y, 300, 70, text, "gray")
            self.buttons.append(button)
    
    def show_blinking_text(self, surface):
        self.blinking_text.show_blinking_text(surface)
        self.settings_button.show_button(surface)
        if self.settings_popup_visible:
            self.display_settings_popup(surface)


    def blink_the_text(self, dt):
        self.blinking_text.update(dt)
    
    def is_blinking_text_clicked(self, event):
        return self.blinking_text.is_clicked(event)

    def display_choice_overlay(self, surface):
        if self.overlay_alpha < self.overlay_max_alpha:
            self.overlay_alpha += 10
            self.overlay_alpha = min(self.overlay_alpha, self.overlay_max_alpha)

        overlay = pygame.Surface((840, HEIGHT), pygame.SRCALPHA)
        overlay.fill((30,30,30, self.overlay_alpha))
        surface.blit(overlay, (WIDTH // 2 - 380, 0))

        for button in self.buttons:
            button.show_button(surface)

    def display_settings_popup(self, surface):
        popup_width = 300
        popup_height = 200
        self.popup_rect = pygame.Rect((WIDTH - popup_width) // 2, (HEIGHT - popup_height) // 2, popup_width,
                                      popup_height)
        pygame.draw.rect(surface, (200, 200, 200), self.popup_rect, border_radius=10)
        pygame.draw.rect(surface, (100, 100, 100), self.popup_rect, 4, border_radius=10)

        font = pygame.font.SysFont('comicsans', 28)
        text_surface = font.render("Settings", True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=(self.popup_rect.centerx, self.popup_rect.top + 40))
        surface.blit(text_surface, text_rect)

        # Nút X đỏ
        self.close_button_rect = pygame.Rect(self.popup_rect.right - 40, self.popup_rect.top + 10, 30, 30)
        pygame.draw.rect(surface, (255, 0, 0), self.close_button_rect, border_radius=5)

        x_font = pygame.font.SysFont('comicsans', 24, bold=True)
        x_surface = x_font.render("X", True, (255, 255, 255))
        x_rect = x_surface.get_rect(center=self.close_button_rect.center)
        surface.blit(x_surface, x_rect)

        #loa icon
        speaker_icon = pygame.image.load('assets/speaker_icon.png')
        speaker_icon = pygame.transform.scale(speaker_icon, (30, 30))
        surface.blit(speaker_icon, (self.popup_rect.left + 20, self.popup_rect.top + 80))

        # âm lượng
        self.slider_rect = pygame.Rect(self.popup_rect.left + 60, self.popup_rect.top + 90, 200, 10)
        pygame.draw.rect(surface, (150, 150, 150), self.slider_rect)
        # chấm tròn thể hiện mức âm lượng hiện tại
        volume_dot_x = self.slider_rect.left + int(self.current_volume * self.slider_rect.width)
        pygame.draw.circle(surface, (0, 0, 0), (volume_dot_x, self.slider_rect.centery), 8)

        # chọn file nhạc
        self.choose_music_button = pygame.Rect(self.popup_rect.centerx - 70, self.popup_rect.top + 130, 140, 30)
        pygame.draw.rect(surface, (100, 100, 255), self.choose_music_button, border_radius=5)
        choose_music_font = pygame.font.SysFont('comicsans', 20)
        music_text = choose_music_font.render("Choose Music", True, (255, 255, 255))
        music_rect = music_text.get_rect(center=self.choose_music_button.center)
        surface.blit(music_text, music_rect)

    def handle_settings_click(self, event):
        if self.settings_button.is_clicked(event):
            self.settings_popup_visible = not self.settings_popup_visible
        elif self.settings_popup_visible:
            mouse_pos = pygame.mouse.get_pos()

            # Đóng popup
            if hasattr(self, "close_button_rect") and self.close_button_rect.collidepoint(mouse_pos):
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.settings_popup_visible = False

            # Điều chỉnh âm lượng khi click vào thanh trượt
            if hasattr(self, "slider_rect") and self.slider_rect.collidepoint(mouse_pos):
                if event.type == pygame.MOUSEBUTTONDOWN:
                    relative_x = mouse_pos[0] - self.slider_rect.left
                    self.current_volume = max(0, min(1, relative_x / self.slider_rect.width))
                    pygame.mixer.music.set_volume(self.current_volume)

            # Chọn file nhạc từ máy
            if hasattr(self, "choose_music_button") and self.choose_music_button.collidepoint(mouse_pos):
                if event.type == pygame.MOUSEBUTTONDOWN:
                    root = tk.Tk()
                    root.withdraw()
                    file_path = filedialog.askopenfilename(filetypes=[("MP3 files", "*.mp3")])
                    if file_path:
                        try:
                            pygame.mixer.music.load(file_path)
                            pygame.mixer.music.play(-1)
                            pygame.mixer.music.set_volume(self.current_volume)
                        except Exception as e:
                            print("Lỗi tải nhạc:", e)

    def handle_button_click(self, event):
        for i, button in enumerate(self.buttons):
            if button.is_clicked(event):
                if i == 0:
                    return PVP_MODE
                elif i == 1:
                    return PVE_MODE

class Button():
    def __init__(self, button_pos_x, button_pos_y, button_width, button_height, button_text, button_color):
        self.font = pygame.font.SysFont('comicsans', 30)
        self.rect = pygame.Rect(button_pos_x, button_pos_y, button_width, button_height)
        self.button_text = button_text
        self.button_text_color = "black"
        self.default_color = button_color
        self.hover_color = self.get_hover_color(button_color)

    def get_hover_color(self, color_name):
        color_map = {
            "gray": (160, 160, 160),
            "red": (255, 100, 100),
            "green": (100, 255, 100),
            "blue": (100, 100, 255),
            # fallback nếu không match tên
            "default": (200, 200, 200)
        }
        return color_map.get(color_name, color_map["default"])

    def show_button(self, screen):
        current_color = self.hover_color if self.is_hovered() else self.default_color
        if isinstance(current_color, str):
            draw_color = pygame.Color(current_color)
        else:
            draw_color = current_color

        pygame.draw.rect(screen, draw_color, self.rect, border_radius=10)
        button_text_surface = self.font.render(self.button_text, True, self.button_text_color)
        button_text_rect = button_text_surface.get_rect(center=self.rect.center)
        screen.blit(button_text_surface, button_text_rect)

    def is_hovered(self):
        return self.rect.collidepoint(pygame.mouse.get_pos())

    def is_clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(pygame.mouse.get_pos())


class BlinkingText():
    def __init__(self, text, pos, text_color='black', blinking_interval=500):
        self.text = text
        self.font = pygame.font.SysFont('comicsans', 30)
        self.pos = pos
        self.text_color = text_color

        self.text_timer = 0
        self.blinking_interval = blinking_interval
        self.visible = True

    def get_text_surface(self, text, text_color):
        return self.font.render(text, True, text_color)
    
    def get_text_surface_rect(self, text_surface, pos):
        return text_surface.get_rect(center=pos)

    def update(self, dt):
        self.text_timer += dt
        if self.text_timer >= self.blinking_interval:
            self.visible = not self.visible
            self.text_timer = 0
    
    def show_blinking_text(self, surface):
        if self.visible:
            text_surface = self.get_text_surface(self.text, self.text_color)
            text_surface_rect = self.get_text_surface_rect(text_surface, self.pos)
            surface.blit(text_surface, text_surface_rect)

    def is_clicked(self, event):
        return event.type == pygame.MOUSEBUTTONDOWN and self.get_text_surface_rect(self.get_text_surface(self.text, self.text_color), self.pos).collidepoint(pygame.mouse.get_pos())
