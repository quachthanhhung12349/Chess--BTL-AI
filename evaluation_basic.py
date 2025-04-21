import chess
from constant import CENTER_SQUARES, EXTENDED_CENTER
from dynamic_PstAndPieceValue import get_piece_value, get_pst

def evaluate(board):
    """
    Hàm đánh giá bàn cờ dựa trên vật chất, PST, pawn structure, mobility, outposts,
    king safety, center control, space, piece coordination, và initiative/threats.
    Trả về giá trị (centipawns): dương nếu Trắng có lợi, âm nếu Đen có lợi.
    """
    if board.is_checkmate():
        return -9999 if board.turn == chess.WHITE else 9999
    if board.is_stalemate() or board.is_insufficient_material() or board.is_seventyfive_moves():
        return 0

    # Tổng điểm đánh giá
    total_score = 0

    # Tính giai đoạn ván cờ
    material = [0, 0]  # [Đen, Trắng]
    for square, piece in board.piece_map().items():
        material[piece.color] += get_piece_value(piece.piece_type, 1.0)  # Dùng giá trị khai cuộc để tính game_phase
    total_material = sum(material) - get_piece_value(chess.KING, 1.0) * 2
    game_phase = total_material / (
        16 * get_piece_value(chess.PAWN, 1.0) +
        4 * get_piece_value(chess.KNIGHT, 1.0) +
        4 * get_piece_value(chess.BISHOP, 1.0) +
        4 * get_piece_value(chess.ROOK, 1.0) +
        2 * get_piece_value(chess.QUEEN, 1.0)
    )

    # 1. Giá trị vật chất
    material = [0, 0]  # [Đen, Trắng]
    for square, piece in board.piece_map().items():
        value = get_piece_value(piece.piece_type, game_phase)
        material[piece.color] += value
    total_score += material[chess.WHITE] - material[chess.BLACK]

    # 2. Bảng vị trí quân cờ (PST)
    position_score = 0
    for square, piece in board.piece_map().items():
        position_score += get_pst(piece.piece_type, square, game_phase, piece.color == chess.WHITE)
        # Điểm âm cho Đen
        if piece.color == chess.BLACK:
            position_score = -position_score
    total_score += position_score

    # 3. Cấu trúc tốt (Pawn Structure)
    pawn_structure_score = 0
    white_pawns = board.pieces(chess.PAWN, chess.WHITE)
    black_pawns = board.pieces(chess.PAWN, chess.BLACK)

    # Tốt thông (Passed Pawns)
    for pawn in white_pawns:
        file = chess.square_file(pawn)
        rank = chess.square_rank(pawn)
        is_passed = True
        for enemy_pawn in black_pawns:
            enemy_file = chess.square_file(enemy_pawn)
            enemy_rank = chess.square_rank(enemy_pawn)
            if abs(file - enemy_file) <= 1 and enemy_rank > rank:
                is_passed = False
                break
        if is_passed:
            pawn_structure_score += 50 + 20 * rank  # Thưởng nhiều hơn ở hàng cao
    for pawn in black_pawns:
        file = chess.square_file(pawn)
        rank = chess.square_rank(pawn)
        is_passed = True
        for enemy_pawn in white_pawns:
            enemy_file = chess.square_file(enemy_pawn)
            enemy_rank = chess.square_rank(enemy_pawn)
            if abs(file - enemy_file) <= 1 and enemy_rank < rank:
                is_passed = False
                break
        if is_passed:
            pawn_structure_score -= 50 + 20 * (7 - rank)

    # Tốt đôi (Doubled Pawns)
    for file in range(8):
        white_pawns_in_file = len([p for p in white_pawns if chess.square_file(p) == file])
        black_pawns_in_file = len([p for p in black_pawns if chess.square_file(p) == file])
        if white_pawns_in_file > 1:
            pawn_structure_score -= 20 * (white_pawns_in_file - 1)
        if black_pawns_in_file > 1:
            pawn_structure_score -= 20 * (black_pawns_in_file - 1)

    total_score += pawn_structure_score

    # 4. Tính linh hoạt (Mobility)
    mobility_score = 0
    white_mobility = 0
    black_mobility = 0
    for piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
        for piece_square in board.pieces(piece_type, chess.WHITE):
            white_mobility += len(board.attacks(piece_square))
        for piece_square in board.pieces(piece_type, chess.BLACK):
            black_mobility += len(board.attacks(piece_square))
    mobility_weight = 6 * game_phase + 3 * (1 - game_phase)  # Nội suy: 6 (khai cuộc) -> 3 (tàn cuộc)
    mobility_score = (white_mobility - black_mobility) * mobility_weight
    total_score += mobility_score

    # 5. Tiền đồn (Outposts)
    outpost_score = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
            file = chess.square_file(square)
            rank = chess.square_rank(square)
            is_outpost = False
            # Kiểm tra tiền đồn cho Trắng
            if piece.color == chess.WHITE and rank >= 4:  # Hàng 5-8
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
            # Kiểm tra tiền đồn cho Đen
            elif piece.color == chess.BLACK and rank <= 3:  # Hàng 1-4
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
                outpost_score += 30 if piece.color == chess.WHITE else -30
    total_score += outpost_score

    # 6. An toàn vua (King Safety)
    king_safety_score = 0
    white_king = board.king(chess.WHITE)
    black_king = board.king(chess.BLACK)

    # Đếm tốt che chắn quanh vua
    white_king_zone = board.attacks(white_king) | chess.BB_SQUARES[white_king]
    black_king_zone = board.attacks(black_king) | chess.BB_SQUARES[black_king]
    white_pawn_shield = len([p for p in white_pawns if p in white_king_zone])
    black_pawn_shield = len([p for p in black_pawns if p in black_king_zone])
    king_safety_score += white_pawn_shield * 20 - black_pawn_shield * 20

    # Phạt nếu có đường mở gần vua
    white_king_file = chess.square_file(white_king)
    black_king_file = chess.square_file(black_king)
    for file in range(max(0, white_king_file - 1), min(8, white_king_file + 2)):
        # Kết hợp hàng 1-3 thành một bitboard
        rank_mask = chess.BB_RANKS[0] | chess.BB_RANKS[1] | chess.BB_RANKS[2]
        file_rank_intersection = chess.BB_FILES[file] & rank_mask
        if not any(p in white_pawns for p in chess.SquareSet(file_rank_intersection)):
            king_safety_score -= 30  # Cột mở gần vua Trắng
    for file in range(max(0, black_king_file - 1), min(8, black_king_file + 2)):
        # Kết hợp hàng 6-8 thành một bitboard
        rank_mask = chess.BB_RANKS[5] | chess.BB_RANKS[6] | chess.BB_RANKS[7]
        file_rank_intersection = chess.BB_FILES[file] & rank_mask
        if not any(p in black_pawns for p in chess.SquareSet(file_rank_intersection)):
            king_safety_score += 30  # Cột mở gần vua Đen

    total_score += king_safety_score

    # 7. Kiểm soát trung tâm (Center Control)
    center_control_score = 0
    white_center_control = 0
    black_center_control = 0
    for square in CENTER_SQUARES:
        if board.piece_at(square) and board.piece_at(square).piece_type == chess.PAWN:
            if board.piece_at(square).color == chess.WHITE:
                white_center_control += 50
            else:
                black_center_control += 50
        attackers = board.attackers(chess.WHITE, square)
        white_center_control += len(attackers) * 20
        attackers = board.attackers(chess.BLACK, square)
        black_center_control += len(attackers) * 20
    center_control_score = white_center_control - black_center_control
    total_score += center_control_score

    # 8. Không gian bàn cờ (Space)
    space_score = 0
    white_space = 0
    black_space = 0
    white_controlled_squares = set()
    black_controlled_squares = set()
    for square in chess.SQUARES:
        rank = chess.square_rank(square)
        if rank >= 3:
            if board.is_attacked_by(chess.WHITE, square) and not board.is_attacked_by(chess.BLACK, square):
                white_controlled_squares.add(square)
        if rank <= 4:
            if board.is_attacked_by(chess.BLACK, square) and not board.is_attacked_by(chess.WHITE, square):
                black_controlled_squares.add(square)
    white_space = len(white_controlled_squares) * 10
    black_space = len(black_controlled_squares) * 10
    space_score = white_space - black_space
    total_score += space_score

    # 9. Sự phối hợp của các quân (Piece Coordination)
    coordination_score = 0
    white_bishops = len(board.pieces(chess.BISHOP, chess.WHITE))
    black_bishops = len(board.pieces(chess.BISHOP, chess.BLACK))
    if white_bishops == 2:
        coordination_score += 50
    if black_bishops == 2:
        coordination_score -= 50
    open_files = [
        f for f in range(8)
        if not (chess.BB_FILES[f] & (white_pawns | black_pawns).mask)
    ]
    for file in open_files:
        file_squares = chess.BB_FILES[file]
        white_rooks = len([r for r in board.pieces(chess.ROOK, chess.WHITE) if r in file_squares])
        white_queens = len([q for q in board.pieces(chess.QUEEN, chess.WHITE) if q in file_squares])
        black_rooks = len([r for r in board.pieces(chess.ROOK, chess.BLACK) if r in file_squares])
        black_queens = len([q for q in board.pieces(chess.QUEEN, chess.BLACK) if q in file_squares])
        if white_rooks >= 1 and white_queens >= 1:
            coordination_score += 30
        if black_rooks >= 1 and black_queens >= 1:
            coordination_score -= 30
    total_score += coordination_score

    # 10. Tính chủ động và Các mối đe dọa (Initiative and Threats)
    initiative_threats_score = 0
    white_initiative = 0
    black_initiative = 0
    white_threats = 0
    black_threats = 0

    # Initiative: Đếm nước chiếu và nước bắt
    for move in board.legal_moves:
        if board.gives_check(move):
            if board.turn == chess.WHITE:
                white_initiative += 15  # Thưởng cho nước chiếu
                board.push(move)
                safe_moves = len([m for m in board.legal_moves if m.from_square == board.king(not board.turn)])
                if safe_moves <= 1:  # Nước chiếu nguy hiểm
                    white_initiative += 20
                board.pop()
            else:
                black_initiative += 15
                board.push(move)
                safe_moves = len([m for m in board.legal_moves if m.from_square == board.king(not board.turn)])
                if safe_moves <= 1:  # Nước chiếu nguy hiểm
                    black_initiative += 20
                board.pop()
        if board.is_capture(move):
            if board.turn == chess.WHITE:
                white_initiative += 5  # Thưởng cho nước bắt
            else:
                black_initiative += 5

    # Initiative: Hạn chế Vua/Hậu đối phương
    white_king = board.king(chess.WHITE)
    black_king = board.king(chess.BLACK)
    white_queen = next(iter(board.pieces(chess.QUEEN, chess.WHITE)), None)
    black_queen = next(iter(board.pieces(chess.QUEEN, chess.BLACK)), None)

    white_king_safe_moves = len([m for m in board.legal_moves if m.from_square == white_king])
    black_king_safe_moves = len([m for m in board.legal_moves if m.from_square == black_king])
    if white_king_safe_moves < 3:
        black_initiative += 20  # Phạt Trắng nếu Vua bị hạn chế
    if black_king_safe_moves < 3:
        white_initiative += 20  # Phạt Đen nếu Vua bị hạn chế

    if white_queen:
        white_queen_safe_moves = len([m for m in board.legal_moves if m.from_square == white_queen])
        if white_queen_safe_moves < 3:
            black_initiative += 20
    if black_queen:
        black_queen_safe_moves = len([m for m in board.legal_moves if m.from_square == black_queen])
        if black_queen_safe_moves < 3:
            white_initiative += 20

    # Threats: Quân cờ đối phương bị tấn công
    for square, piece in board.piece_map().items():
        if piece.color == chess.BLACK:  # Quân Đen bị Trắng tấn công
            attackers = board.attackers(chess.WHITE, square)
            if attackers:
                defenders = board.attackers(chess.BLACK, square)
                if len(attackers) > len(defenders):  # Không được bảo vệ đủ
                    if piece.piece_type == chess.PAWN:
                        white_threats += 10
                    elif piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
                        white_threats += 20
                    elif piece.piece_type == chess.ROOK:
                        white_threats += 30
                    elif piece.piece_type == chess.QUEEN:
                        white_threats += 50
        elif piece.color == chess.WHITE:  # Quân Trắng bị Đen tấn công
            attackers = board.attackers(chess.BLACK, square)
            if attackers:
                defenders = board.attackers(chess.WHITE, square)
                if len(attackers) > len(defenders):  # Không được bảo vệ đủ
                    if piece.piece_type == chess.PAWN:
                        black_threats += 10
                    elif piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
                        black_threats += 20
                    elif piece.piece_type == chess.ROOK:
                        black_threats += 30
                    elif piece.piece_type == chess.QUEEN:
                        black_threats += 50

    # Threats: Phát hiện chạc (Fork)
    for piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
        for piece_square in board.pieces(piece_type, chess.WHITE):
            attacks = board.attacks(piece_square)
            attacked_pieces = [
                s for s in attacks
                if board.piece_at(s) and board.piece_at(s).color == chess.BLACK
                and board.piece_at(s).piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]
            ]
            if board.gives_check(chess.Move(piece_square, board.king(chess.BLACK))) and board.king(chess.BLACK) in attacks:
                attacked_pieces.append(board.king(chess.BLACK))  # Chạc bao gồm nước chiếu
            if len(attacked_pieces) >= 2:
                white_threats += 30 if board.king(chess.BLACK) in attacked_pieces else 20  # Thưởng cho chạc
        for piece_square in board.pieces(piece_type, chess.BLACK):
            attacks = board.attacks(piece_square)
            attacked_pieces = [
                s for s in attacks
                if board.piece_at(s) and board.piece_at(s).color == chess.WHITE
                and board.piece_at(s).piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]
            ]
            if board.gives_check(chess.Move(piece_square, board.king(chess.WHITE))) and board.king(chess.WHITE) in attacks:
                attacked_pieces.append(board.king(chess.WHITE))  # Chạc bao gồm nước chiếu
            if len(attacked_pieces) >= 2:
                black_threats += 30 if board.king(chess.WHITE) in attacked_pieces else 20  # Thưởng cho chạc

    # Threats: Phát hiện đinh (Pin)
    for square, piece in board.piece_map().items():
        if piece.color == chess.BLACK and board.is_pinned(chess.BLACK, square):  # Đinh tuyệt đối với Đen
            white_threats += 15
        elif piece.color == chess.WHITE and board.is_pinned(chess.WHITE, square):  # Đinh tuyệt đối với Trắng
            black_threats += 15
        # Đinh tương đối
        if piece.color == chess.BLACK:
            attackers = board.attackers(chess.WHITE, square)
            for attacker_square in attackers:
                attacker = board.piece_at(attacker_square)
                if attacker and attacker.piece_type in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
                    # Kiểm tra quân quan trọng (Hậu, Xe) phía sau
                    direction = (
                        (chess.square_rank(square) - chess.square_rank(attacker_square),
                         chess.square_file(square) - chess.square_file(attacker_square))
                    )
                    if direction[0] != 0 or direction[1] != 0:  # Đảm bảo có hướng
                        step = (
                            direction[0] // max(1, abs(direction[0])),
                            direction[1] // max(1, abs(direction[1]))
                        )
                        current_square = square
                        while True:
                            current_square = chess.square(
                                chess.square_file(current_square) + step[1],
                                chess.square_rank(current_square) + step[0]
                            )
                            if not (0 <= chess.square_file(current_square) < 8 and 0 <= chess.square_rank(current_square) < 8):
                                break
                            target_piece = board.piece_at(current_square)
                            if target_piece and target_piece.color == chess.BLACK and target_piece.piece_type in [chess.ROOK, chess.QUEEN]:
                                white_threats += 10  # Đinh tương đối
                                break
                            if target_piece:
                                break
        elif piece.color == chess.WHITE:
            attackers = board.attackers(chess.BLACK, square)
            for attacker_square in attackers:
                attacker = board.piece_at(attacker_square)
                if attacker and attacker.piece_type in [chess.BISHOP, chess.ROOK, chess.QUEEN]:
                    direction = (
                        chess.square_rank(square) - chess.square_rank(attacker_square),
                        chess.square_file(square) - chess.square_file(attacker_square)
                    )
                    if direction[0] != 0 or direction[1] != 0:
                        step = (
                            direction[0] // max(1, abs(direction[0])),
                            direction[1] // max(1, abs(direction[1]))
                        )
                        current_square = square
                        while True:
                            current_square = chess.square(
                                chess.square_file(current_square) + step[1],
                                chess.square_rank(current_square) + step[0]
                            )
                            if not (0 <= chess.square_file(current_square) < 8 and 0 <= chess.square_rank(current_square) < 8):
                                break
                            target_piece = board.piece_at(current_square)
                            if target_piece and target_piece.color == chess.WHITE and target_piece.piece_type in [chess.ROOK, chess.QUEEN]:
                                black_threats += 10  # Đinh tương đối
                                break
                            if target_piece:
                                break

    # Kết hợp Initiative và Threats
    initiative_score = white_initiative - black_initiative
    threats_score = white_threats - black_threats
    initiative_threats_weight = 1.0 * game_phase + 0.5 * (1 - game_phase)  # Nội suy: 1.0 (khai cuộc) -> 0.5 (tàn cuộc)
    initiative_threats_score = (initiative_score + threats_score) * initiative_threats_weight
    total_score += initiative_threats_score

    # Điều chỉnh điểm số dựa trên lượt đi
    return total_score if board.turn == chess.WHITE else -total_score