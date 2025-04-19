<<<<<<< HEAD
#UI UX controller
=======
#UI UX controller
import pygame
import os
import chess
from constant import *


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
    screen.fill((0, 0, 0))
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

def load_piece_texture():
    piece_imgs = {}
    for symbol, texture_path in PIECE_TEXTURE.items():
        piece_img = pygame.image.load(f'assets/chess_image/{texture_path}').convert_alpha()
        piece_imgs[symbol] = piece_img
    return piece_imgs

class GameMenu():
    def __init__(self):
        self.blinking_text = BlinkingText("Click to start game", (WIDTH // 2, HEIGHT // 2 + 20), text_color='black', blinking_interval=500)
        
        self.buttons = []
        self.create_buttons()

        self.overlay_alpha = 0
        self.overlay_max_alpha = 180

    def create_buttons(self):
        labels = ["PvP", "PvE", "AI Matching"]
        for i, text in enumerate(labels):
            x = WIDTH // 2 - 150
            y = 250 + i * 120
            button = Button(x, y, 300, 70, text, "gray")
            self.buttons.append(button)
    
    def show_blinking_text(self, surface):
        self.blinking_text.show_blinking_text(surface)

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
        
    def handle_button_click(self, event):
        for i, button in enumerate(self.buttons):
            if button.is_clicked(event):
                if i == 0:
                    return PVP_MODE
                elif i == 1:
                    return PVE_MODE
                elif i == 2:
                    return AI_MATCHING_MODE

class Button():
    def __init__(self, button_pos_x, button_pos_y, button_width, button_height, button_text, button_color):
        self.font = pygame.font.SysFont('comicsans', 30)
        self.rect = pygame.Rect(button_pos_x, button_pos_y, button_width, button_height)
        self.button_text = button_text
        self.button_text_color = "black"
        self.button_color = button_color

    def show_button(self, screen):
        pygame.draw.rect(screen, self.button_color, self.rect, border_radius=10)
        button_text_surface = self.font.render(self.button_text, True, self.button_text_color)
        button_text_rect = button_text_surface.get_rect(center=self.rect.center)
        screen.blit(button_text_surface, button_text_rect)

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
>>>>>>> 34a1a9e0017b649147650e396d85f6411bfc5399
