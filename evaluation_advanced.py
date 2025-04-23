
import chess
import chess.polyglot
import time
from constant import CENTER_SQUARES, EXTENDED_CENTER, FORK_BONUS, FORK_CHECK_BONUS, PIN_ABSOLUTE_BONUS
from dynamic_PstAndPieceValue import get_piece_value, get_pst

# Precomputed king attack bitboards
BB_KING_ATTACKS = {s: chess.BB_KING_ATTACKS[s] for s in chess.SQUARES}

# Cache dictionaries
attack_cache = {}
attackers_cache = {}
pin_cache = {}
open_files_cache = {}
semi_open_files_cache = {}
piece_map_cache = {}

def get_attacks(board, square):
    """Get attack squares for a piece, cached."""
    cache_key = (chess.polyglot.zobrist_hash(board), square)
    if cache_key not in attack_cache:
        attack_cache[cache_key] = board.attacks(square)
    return attack_cache[cache_key]

def get_attackers(board, square, color):
    """Get attackers of a square for a color, cached."""
    cache_key = (chess.polyglot.zobrist_hash(board), square, color)
    if cache_key not in attackers_cache:
        attackers_cache[cache_key] = board.attackers(color, square)
    return attackers_cache[cache_key]

def is_pinned(board, color, square):
    """Check if a piece is pinned, cached."""
    cache_key = (chess.polyglot.zobrist_hash(board), color, square)
    if cache_key not in pin_cache:
        pin_cache[cache_key] = board.is_pinned(color, square)
    return pin_cache[cache_key]

def get_open_files(board, white_pawns, black_pawns):
    """Get open files (no pawns), cached."""
    cache_key = chess.polyglot.zobrist_hash(board)
    if cache_key not in open_files_cache:
        pawn_bitboard = (white_pawns | black_pawns).mask
        open_files_cache[cache_key] = [
            f for f in range(8) if not (chess.BB_FILES[f] & pawn_bitboard)
        ]
    return open_files_cache[cache_key]

def get_semi_open_files(board, white_pawns, black_pawns):
    """Get semi-open files (pawns of one side only), cached."""
    cache_key = chess.polyglot.zobrist_hash(board)
    if cache_key not in semi_open_files_cache:
        white_pawn_files = set(chess.square_file(p) for p in white_pawns)
        black_pawn_files = set(chess.square_file(p) for p in black_pawns)
        semi_open_files_cache[cache_key] = {
            'white': [f for f in range(8) if f not in black_pawn_files and f in white_pawn_files],
            'black': [f for f in range(8) if f not in white_pawn_files and f in black_pawn_files]
        }
    return semi_open_files_cache[cache_key]

def get_piece_map(board):
    """Get piece map, cached."""
    cache_key = chess.polyglot.zobrist_hash(board)
    if cache_key not in piece_map_cache:
        piece_map_cache[cache_key] = board.piece_map()
    return piece_map_cache[cache_key]

def evaluate(board):
    """Evaluate the board position, returning a score (positive favors White)."""
    # Clear caches to prevent memory leaks
    attack_cache.clear()
    attackers_cache.clear()
    pin_cache.clear()
    open_files_cache.clear()
    semi_open_files_cache.clear()
    piece_map_cache.clear()

    # Check game end conditions
    if board.is_checkmate():
        return -9999 if board.turn == chess.WHITE else 9999
    if board.is_stalemate() or board.is_insufficient_material() or board.is_seventyfive_moves():
        return 0

    total_score = 0
    material = [0, 0]
    piece_map = get_piece_map(board)
    for square, piece in piece_map.items():
        material[piece.color] += get_piece_value(piece.piece_type, 1.0)
    total_material = sum(material) - get_piece_value(chess.KING, 1.0) * 2
    game_phase = min(1.0, total_material / (
        16 * get_piece_value(chess.PAWN, 1.0) +
        4 * get_piece_value(chess.KNIGHT, 1.0) +
        4 * get_piece_value(chess.BISHOP, 1.0) +
        4 * get_piece_value(chess.ROOK, 1.0) +
        2 * get_piece_value(chess.QUEEN, 1.0)
    ))

    # Material
    material = [0, 0]
    for square, piece in piece_map.items():
        material[piece.color] += get_piece_value(piece.piece_type, game_phase)
    total_score += material[chess.WHITE] - material[chess.BLACK]

    # Piece-Square Tables
    position_score = 0
    for square, piece in piece_map.items():
        score = get_pst(piece.piece_type, square, game_phase, piece.color == chess.WHITE)
        position_score += score if piece.color == chess.WHITE else -score
    total_score += position_score

    # Pawn Structure
    pawn_structure_score = 0
    white_pawns = board.pieces(chess.PAWN, chess.WHITE)
    black_pawns = board.pieces(chess.PAWN, chess.BLACK)
    for pawn in white_pawns:
        file, rank = chess.square_file(pawn), chess.square_rank(pawn)
        is_passed = not any(
            abs(chess.square_file(p) - file) <= 1 and chess.square_rank(p) > rank
            for p in black_pawns
        )
        if is_passed:
            bonus = 40 + 15 * rank
            if game_phase < 0.2 and rank >= 5:
                bonus += 100
            pawn_structure_score += bonus
    for pawn in black_pawns:
        file, rank = chess.square_file(pawn), chess.square_rank(pawn)
        is_passed = not any(
            abs(chess.square_file(p) - file) <= 1 and chess.square_rank(p) < rank
            for p in white_pawns
        )
        if is_passed:
            bonus = 40 + 15 * (7 - rank)
            if game_phase < 0.2 and rank <= 2:
                bonus += 100
            pawn_structure_score -= bonus
    for file in range(8):
        white_pawns_in_file = len([p for p in white_pawns if chess.square_file(p) == file])
        black_pawns_in_file = len([p for p in black_pawns if chess.square_file(p) == file])
        if white_pawns_in_file > 1:
            pawn_structure_score -= 15 * (white_pawns_in_file - 1)
        if black_pawns_in_file > 1:
            pawn_structure_score -= 15 * (black_pawns_in_file - 1)
    total_score += pawn_structure_score

    # Combined Mobility, Center Control, and Space
    mobility_score = 0
    center_control_score = 0
    space_score = 0
    white_mobility = 0
    black_mobility = 0
    white_attackers = chess.SquareSet()
    black_attackers = chess.SquareSet()
    for piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
        for piece_square in board.pieces(piece_type, chess.WHITE):
            attacks = get_attacks(board, piece_square)
            white_mobility += len(attacks)
            white_attackers |= attacks
        for piece_square in board.pieces(piece_type, chess.BLACK):
            attacks = get_attacks(board, piece_square)
            black_mobility += len(attacks)
            black_attackers |= attacks
    for square in CENTER_SQUARES:
        piece = board.piece_at(square)
        if piece and piece.piece_type == chess.PAWN:
            center_control_score += 30 if piece.color == chess.WHITE else -30
        if square in white_attackers:
            center_control_score += 10
        if square in black_attackers:
            center_control_score -= 10
    for square in chess.SQUARES:
        rank = chess.square_rank(square)
        if rank >= 3 and square in white_attackers and square not in black_attackers:
            space_score += 6
        if rank <= 4 and square in black_attackers and square not in white_attackers:
            space_score -= 6
    mobility_weight = 4 * game_phase + 2 * (1 - game_phase)
    mobility_score = (white_mobility - black_mobility) * mobility_weight
    total_score += mobility_score + center_control_score + space_score

    # Outposts
    outpost_score = 0
    for square in chess.SQUARES:
        rank = chess.square_rank(square)
        if not (3 <= rank <= 5 or 2 <= rank <= 4):
            continue
        piece = board.piece_at(square)
        if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
            file = chess.square_file(square)
            is_outpost = False
            if piece.color == chess.WHITE and rank >= 3:
                has_pawn_support = any(
                    chess.square_file(p) in [file - 1, file + 1] and chess.square_rank(p) == rank - 1
                    for p in white_pawns
                )
                no_enemy_pawn_block = not any(
                    abs(chess.square_file(p) - file) <= 1 and chess.square_rank(p) > rank
                    for p in black_pawns
                )
                if has_pawn_support and no_enemy_pawn_block:
                    is_outpost = True
            elif piece.color == chess.BLACK and rank <= 4:
                has_pawn_support = any(
                    chess.square_file(p) in [file - 1, file + 1] and chess.square_rank(p) == rank + 1
                    for p in black_pawns
                )
                no_enemy_pawn_block = not any(
                    abs(chess.square_file(p) - file) <= 1 and chess.square_rank(p) < rank
                    for p in white_pawns
                )
                if has_pawn_support and no_enemy_pawn_block:
                    is_outpost = True
            if is_outpost:
                outpost_score += 20 if piece.color == chess.WHITE else -20
    total_score += outpost_score

    # King Safety
    king_safety_score = 0
    white_king = board.king(chess.WHITE)
    black_king = board.king(chess.BLACK)
    white_king_zone = chess.SquareSet(BB_KING_ATTACKS[white_king] | chess.BB_SQUARES[white_king])
    black_king_zone = chess.SquareSet(BB_KING_ATTACKS[black_king] | chess.BB_SQUARES[black_king])
    white_pawn_shield = len([p for p in white_pawns if p in white_king_zone])
    black_pawn_shield = len([p for p in black_pawns if p in black_king_zone])
    king_safety_score += white_pawn_shield * 10 - black_pawn_shield * 10
    semi_open_files = get_semi_open_files(board, white_pawns, black_pawns)
    white_king_file = chess.square_file(white_king)
    black_king_file = chess.square_file(black_king)
    if white_king_file in semi_open_files['black']:
        king_safety_score -= 20
    if black_king_file in semi_open_files['white']:
        king_safety_score += 20
    total_score += king_safety_score

    # Piece Coordination
    coordination_score = 0
    white_bishops = len(board.pieces(chess.BISHOP, chess.WHITE))
    black_bishops = len(board.pieces(chess.BISHOP, chess.BLACK))
    if white_bishops == 2:
        coordination_score += 30
    if black_bishops == 2:
        coordination_score -= 30
    for file in get_open_files(board, white_pawns, black_pawns):
        file_squares = chess.SquareSet(chess.BB_FILES[file])
        white_rooks = len([r for r in board.pieces(chess.ROOK, chess.WHITE) if r in file_squares])
        white_queens = len([q for q in board.pieces(chess.QUEEN, chess.WHITE) if q in file_squares])
        black_rooks = len([r for r in board.pieces(chess.ROOK, chess.BLACK) if r in file_squares])
        black_queens = len([q for q in board.pieces(chess.QUEEN, chess.BLACK) if q in file_squares])
        if white_rooks >= 1 and white_queens >= 1:
            coordination_score += 20
        if black_rooks >= 1 and black_queens >= 1:
            coordination_score -= 20
    total_score += coordination_score

    # Rook on Seventh
    white_rooks_on_seventh = len([r for r in board.pieces(chess.ROOK, chess.WHITE) if chess.square_rank(r) == 6])
    black_rooks_on_seventh = len([r for r in board.pieces(chess.ROOK, chess.BLACK) if chess.square_rank(r) == 1])
    total_score += (white_rooks_on_seventh - black_rooks_on_seventh) * 30

    # Threats (Forks and Pins)
    threats_score = 0
    white_threats = 0
    black_threats = 0
    for square, piece in piece_map.items():
        if piece.color == chess.BLACK:
            attackers = get_attackers(board, square, chess.WHITE)
            defenders = get_attackers(board, square, chess.BLACK)
            if attackers and len(attackers) > len(defenders):
                if piece.piece_type == chess.PAWN:
                    white_threats += 6
                elif piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
                    white_threats += 12
                elif piece.piece_type == chess.ROOK:
                    white_threats += 20
                elif piece.piece_type == chess.QUEEN:
                    white_threats += 30
            if is_pinned(board, chess.BLACK, square):
                white_threats += PIN_ABSOLUTE_BONUS
        elif piece.color == chess.WHITE:
            attackers = get_attackers(board, square, chess.BLACK)
            defenders = get_attackers(board, square, chess.WHITE)
            if attackers and len(attackers) > len(defenders):
                if piece.piece_type == chess.PAWN:
                    black_threats += 6
                elif piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
                    black_threats += 12
                elif piece.piece_type == chess.ROOK:
                    black_threats += 20
                elif piece.piece_type == chess.QUEEN:
                    black_threats += 30
            if is_pinned(board, chess.WHITE, square):
                black_threats += PIN_ABSOLUTE_BONUS
    for piece_type in [chess.KNIGHT, chess.QUEEN]:
        for piece_square in board.pieces(piece_type, chess.WHITE):
            attacks = get_attacks(board, piece_square)
            attacked_pieces = [
                s for s in attacks
                if board.piece_at(s) and board.piece_at(s).color == chess.BLACK
                and board.piece_at(s).piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]
            ]
            if board.king(chess.BLACK) in attacks:
                attacked_pieces.append(board.king(chess.BLACK))
            if len(attacked_pieces) >= 2:
                white_threats += FORK_CHECK_BONUS if board.king(chess.BLACK) in attacked_pieces else FORK_BONUS
        for piece_square in board.pieces(piece_type, chess.BLACK):
            attacks = get_attacks(board, piece_square)
            attacked_pieces = [
                s for s in attacks
                if board.piece_at(s) and board.piece_at(s).color == chess.WHITE
                and board.piece_at(s).piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]
            ]
            if board.king(chess.WHITE) in attacks:
                attacked_pieces.append(board.king(chess.WHITE))
            if len(attacked_pieces) >= 2:
                black_threats += FORK_CHECK_BONUS if board.king(chess.WHITE) in attacked_pieces else FORK_BONUS
    threats_weight = 0.9 * game_phase + 0.5 * (1 - game_phase)
    total_score += (white_threats - black_threats) * threats_weight

    # Endgame Adjustments
    if game_phase < 0.2:
        white_king = board.king(chess.WHITE)
        black_king = board.king(chess.BLACK)
        white_king_activity = len(get_attacks(board, white_king))
        black_king_activity = len(get_attacks(board, black_king))
        total_score += (white_king_activity - black_king_activity) * 8
        for pawn in white_pawns:
            rank = chess.square_rank(pawn)
            if rank >= 6:
                total_score += 100
        for pawn in black_pawns:
            rank = chess.square_rank(pawn)
            if rank <= 1:
                total_score -= 100

    return total_score if board.turn == chess.WHITE else -total_score

if __name__ == "__main__":
    board1 = chess.Board()
    tic = time.perf_counter()
    #board1.push_san("e2e4")

    print(evaluate(board1))
    toc = time.perf_counter()
    print(toc - tic)
