import chess

WIDTH = 1100
HEIGHT = 800

WIDTH_BOARD = 800
HEIGHT_BOARD = 800

FPS = 60

ROWS = 8
COLS = 8
SQUARE_SIZE = WIDTH_BOARD // COLS

PIECE_TEXTURE = {
    'p': 'black_pawn.png',
    'r': 'black_rook.png',
    'n': 'black_knight.png',
    'b': 'black_bishop.png',
    'q': 'black_queen.png',
    'k': 'black_king.png',
    'P': 'white_pawn.png',
    'R': 'white_rook.png',
    'N': 'white_knight.png',
    'B': 'white_bishop.png',
    'Q': 'white_queen.png',
    'K': 'white_king.png'
}

# Các ô trung tâm (d4, d5, e4, e5)
CENTER_SQUARES = {
    chess.D4, chess.D5,
    chess.E4, chess.E5
}

# Các ô mở rộng trung tâm (c3, c4, c5, c6, d3, d6, e3, e6, f3, f4, f5, f6)
EXTENDED_CENTER = {
    chess.C3, chess.C4, chess.C5, chess.C6,
    chess.D3, chess.D6,
    chess.E3, chess.E6,
    chess.F3, chess.F4, chess.F5, chess.F6
}
# Bonus for forks
FORK_BONUS = 40

# Bonus for forks that include a check
FORK_CHECK_BONUS = 80

# Bonus for absolute pins (pinned piece cannot move)
PIN_ABSOLUTE_BONUS = 80

MAIN_MENU = "manin_menu"
MAIN_MENU_WITH_BUTTONS = "main_menu_with_buttons"
GAME_MODE = "game_mode"
PVP_MODE = "pvp_mode"
PVE_MODE = "pve_mode"
AI_MATCHING_MODE = "ai_matching_mode"

BOARD_SIZE = 800
GAME_MODE_MENU = "game_mode_menu"

GAME_OVER_SCREEN = "game_over_screen"