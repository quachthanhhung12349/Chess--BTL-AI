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

def draw_board(screen, board, font):
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
