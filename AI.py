import chess
import time
from LogicChess import ChessGame

class ChessAI:
    """
    Lớp AI cờ vua sử dụng thuật toán minimax với cắt tỉa alpha-beta
    """

    def __init__(self, depth=5):
        """
        Khởi tạo AI cờ vua

        :param depth: Độ sâu tìm kiếm tối đa
        """
        self.depth = depth
        self.nodes_evaluated = 0  # Đếm số nút đã đánh giá
        self.transposition_table = {}  # Bảng chuyển vị để lưu trữ các đánh giá đã tính

        # Giá trị của các quân cờ
        self.piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }

        # Bảng vị trí cho từng quân cờ (đơn giản hóa)
        # Các quân cờ được khuyến khích di chuyển vào trung tâm bàn cờ
        self.pawn_position_values = [
            0, 0, 0, 0, 0, 0, 0, 0,
            50, 50, 50, 50, 50, 50, 50, 50,
            10, 10, 20, 30, 30, 20, 10, 10,
            5, 5, 10, 25, 25, 10, 5, 5,
            0, 0, 0, 20, 20, 0, 0, 0,
            5, -5, -10, 0, 0, -10, -5, 5,
            5, 10, 10, -20, -20, 10, 10, 5,
            0, 0, 0, 0, 0, 0, 0, 0
        ]

        self.knight_position_values = [
            -50, -40, -30, -30, -30, -30, -40, -50,
            -40, -20, 0, 0, 0, 0, -20, -40,
            -30, 0, 10, 15, 15, 10, 0, -30,
            -30, 5, 15, 20, 20, 15, 5, -30,
            -30, 0, 15, 20, 20, 15, 0, -30,
            -30, 5, 10, 15, 15, 10, 5, -30,
            -40, -20, 0, 5, 5, 0, -20, -40,
            -50, -40, -30, -30, -30, -30, -40, -50
        ]

        self.bishop_position_values = [
            -20, -10, -10, -10, -10, -10, -10, -20,
            -10, 0, 0, 0, 0, 0, 0, -10,
            -10, 0, 10, 10, 10, 10, 0, -10,
            -10, 5, 5, 10, 10, 5, 5, -10,
            -10, 0, 5, 10, 10, 5, 0, -10,
            -10, 5, 5, 5, 5, 5, 5, -10,
            -10, 0, 5, 0, 0, 5, 0, -10,
            -20, -10, -10, -10, -10, -10, -10, -20
        ]

        self.rook_position_values = [
            0, 0, 0, 0, 0, 0, 0, 0,
            5, 10, 10, 10, 10, 10, 10, 5,
            -5, 0, 0, 0, 0, 0, 0, -5,
            -5, 0, 0, 0, 0, 0, 0, -5,
            -5, 0, 0, 0, 0, 0, 0, -5,
            -5, 0, 0, 0, 0, 0, 0, -5,
            -5, 0, 0, 0, 0, 0, 0, -5,
            0, 0, 0, 5, 5, 0, 0, 0
        ]

        self.queen_position_values = [
            -20, -10, -10, -5, -5, -10, -10, -20,
            -10, 0, 0, 0, 0, 0, 0, -10,
            -10, 0, 5, 5, 5, 5, 0, -10,
            -5, 0, 5, 5, 5, 5, 0, -5,
            0, 0, 5, 5, 5, 5, 0, -5,
            -10, 5, 5, 5, 5, 5, 0, -10,
            -10, 0, 5, 0, 0, 0, 0, -10,
            -20, -10, -10, -5, -5, -10, -10, -20
        ]

        self.king_position_values_middlegame = [
            -30, -40, -40, -50, -50, -40, -40, -30,
            -30, -40, -40, -50, -50, -40, -40, -30,
            -30, -40, -40, -50, -50, -40, -40, -30,
            -30, -40, -40, -50, -50, -40, -40, -30,
            -20, -30, -30, -40, -40, -30, -30, -20,
            -10, -20, -20, -20, -20, -20, -20, -10,
            20, 20, 0, 0, 0, 0, 20, 20,
            20, 30, 10, 0, 0, 10, 30, 20
        ]

        self.king_position_values_endgame = [
            -50, -40, -30, -20, -20, -30, -40, -50,
            -30, -20, -10, 0, 0, -10, -20, -30,
            -30, -10, 20, 30, 30, 20, -10, -30,
            -30, -10, 30, 40, 40, 30, -10, -30,
            -30, -10, 30, 40, 40, 30, -10, -30,
            -30, -10, 20, 30, 30, 20, -10, -30,
            -30, -30, 0, 0, 0, 0, -30, -30,
            -50, -30, -30, -30, -30, -30, -30, -50
        ]

    def get_position_value(self, piece, square, is_endgame=False):
        """
        Lấy giá trị vị trí của một quân cờ

        :param piece: Loại quân cờ
        :param square: Vị trí trên bàn cờ (0-63)
        :param is_endgame: Có phải đang ở giai đoạn cuối trò chơi
        :return: Giá trị vị trí
        """
        # Lật bảng giá trị vị trí cho quân đen
        mirror_square = square
        if not piece.color:  # Nếu là quân đen
            mirror_square = chess.square_mirror(square)

        if piece.piece_type == chess.PAWN:
            return self.pawn_position_values[mirror_square]
        elif piece.piece_type == chess.KNIGHT:
            return self.knight_position_values[mirror_square]
        elif piece.piece_type == chess.BISHOP:
            return self.bishop_position_values[mirror_square]
        elif piece.piece_type == chess.ROOK:
            return self.rook_position_values[mirror_square]
        elif piece.piece_type == chess.QUEEN:
            return self.queen_position_values[mirror_square]
        elif piece.piece_type == chess.KING:
            if is_endgame:
                return self.king_position_values_endgame[mirror_square]
            else:
                return self.king_position_values_middlegame[mirror_square]
        return 0

    def is_endgame(self, board):
        """
        Kiểm tra xem có phải đang ở giai đoạn cuối trò chơi không

        :param board: Bàn cờ hiện tại
        :return: True nếu đang ở giai đoạn cuối trò chơi
        """
        queens = 0
        minor_pieces = 0

        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                if piece.piece_type == chess.QUEEN:
                    queens += 1
                elif piece.piece_type in [chess.ROOK, chess.BISHOP, chess.KNIGHT]:
                    minor_pieces += 1

        # Giai đoạn cuối trò chơi khi không còn hậu hoặc mỗi bên chỉ còn ít quân cờ
        return queens == 0 or (queens == 2 and minor_pieces <= 4)

    def evaluate_board(self, board):
        """
        Đánh giá trạng thái bàn cờ

        :param board: Bàn cờ cần đánh giá
        :return: Điểm số cho trạng thái bàn cờ (cao hơn là tốt hơn cho quân trắng)
        """
        if board.is_checkmate():
            # Nếu chiếu tướng, trả về điểm rất cao/thấp tùy vào bên nào thắng
            return -10000 if board.turn else 10000

        if board.is_stalemate() or board.is_insufficient_material() or board.is_seventyfive_moves() or board.is_fivefold_repetition():
            return 0  # Hòa

        total_score = 0
        is_endgame = self.is_endgame(board)

        # Đánh giá vật chất và vị trí của mỗi quân cờ
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                # Điểm cơ bản của quân cờ
                value = self.piece_values[piece.piece_type]

                # Điểm vị trí
                position_value = self.get_position_value(piece, square, is_endgame)

                # Điểm số cuối cùng (dương cho quân trắng, âm cho quân đen)
                piece_score = value + position_value
                total_score += piece_score if piece.color else -piece_score

        # Các yếu tố chiến thuật bổ sung

        # Điểm cho khả năng di chuyển (số nước đi hợp lệ)
        mobility_white = len(list(board.generate_legal_moves()))

        # Đổi lượt để tính khả năng di chuyển của đối phương
        board.push(chess.Move.null())
        mobility_black = len(list(board.generate_legal_moves()))
        board.pop()  # Trở lại trạng thái ban đầu

        mobility_score = (mobility_white - mobility_black) * 5  # Hệ số cho khả năng di chuyển
        total_score += mobility_score

        # Kiểm tra chiếu
        if board.is_check():
            total_score += 50 if not board.turn else -50

        return total_score

    def order_moves(self, board, moves):
        """
        Sắp xếp nước đi theo thứ tự để tối ưu hóa cắt tỉa alpha-beta

        :param board: Bàn cờ hiện tại
        :param moves: Danh sách nước đi cần sắp xếp
        :return: Danh sách nước đi đã sắp xếp
        """
        move_scores = []

        for move in moves:
            score = 0

            # Ưu tiên chiếu tướng
            if board.gives_check(move):
                score += 10000

            # Ưu tiên bắt quân
            if board.is_capture(move):
                victim_value = 0
                aggressor_value = 0

                victim_piece = board.piece_at(move.to_square)
                if victim_piece:
                    victim_value = self.piece_values[victim_piece.piece_type]

                aggressor_piece = board.piece_at(move.from_square)
                if aggressor_piece:
                    aggressor_value = self.piece_values[aggressor_piece.piece_type]

                # MVV-LVA (Most Valuable Victim - Least Valuable Aggressor)
                score += victim_value - aggressor_value / 10

            # Ưu tiên phong hậu
            if move.promotion:
                score += self.piece_values[move.promotion] - self.piece_values[chess.PAWN]

            move_scores.append((move, score))

        # Sắp xếp giảm dần theo điểm
        move_scores.sort(key=lambda x: x[1], reverse=True)
        return [move for move, _ in move_scores]

    def minimax(self, board, depth, alpha, beta, maximizing_player):
        """
        Thuật toán minimax với cắt tỉa alpha-beta

        :param board: Bàn cờ hiện tại
        :param depth: Độ sâu còn lại để tìm kiếm
        :param alpha: Giá trị alpha cho cắt tỉa
        :param beta: Giá trị beta cho cắt tỉa
        :param maximizing_player: True nếu đang tối đa hóa (quân trắng), False nếu tối thiểu hóa (quân đen)
        :return: Điểm đánh giá tốt nhất có thể đạt được
        """
        self.nodes_evaluated += 1

        # Tạo khóa bảng chuyển vị từ FEN
        board_key = board.fen()

        # Kiểm tra xem đã đánh giá vị trí này chưa
        if board_key in self.transposition_table and self.transposition_table[board_key][0] >= depth:
            return self.transposition_table[board_key][1]

        # Điều kiện dừng
        if depth == 0 or board.is_game_over():
            evaluation = self.evaluate_board(board)
            # Lưu kết quả vào bảng chuyển vị
            self.transposition_table[board_key] = (depth, evaluation)
            return evaluation

        legal_moves = list(board.legal_moves)

        # Sắp xếp nước đi để tối ưu hóa cắt tỉa
        ordered_moves = self.order_moves(board, legal_moves)

        if maximizing_player:  # Người chơi quân trắng (tối đa hóa)
            max_eval = float('-inf')
            for move in ordered_moves:
                board.push(move)
                eval = self.minimax(board, depth - 1, alpha, beta, False)
                board.pop()

                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break  # Cắt tỉa beta

            # Lưu kết quả vào bảng chuyển vị
            self.transposition_table[board_key] = (depth, max_eval)
            return max_eval
        else:  # Người chơi quân đen (tối thiểu hóa)
            min_eval = float('inf')
            for move in ordered_moves:
                board.push(move)
                eval = self.minimax(board, depth - 1, alpha, beta, True)
                board.pop()

                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break  # Cắt tỉa alpha

            # Lưu kết quả vào bảng chuyển vị
            self.transposition_table[board_key] = (depth, min_eval)
            return min_eval

    def get_best_move(self, game, max_time=5):
        """
        Tìm nước đi tốt nhất cho trạng thái bàn cờ hiện tại

        :param game: Đối tượng ChessGame
        :param max_time: Thời gian tối đa để tìm kiếm (giây)
        :return: Nước đi tốt nhất dưới dạng UCI string
        """
        board = game.get_board()
        start_time = time.time()
        self.nodes_evaluated = 0
        self.transposition_table = {}
        best_move = None

        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None

        # Sắp xếp nước đi để tối ưu hóa cắt tỉa
        ordered_moves = self.order_moves(board, legal_moves)

        best_eval = float('-inf') if board.turn else float('inf')
        maximizing = board.turn  # Trắng = True, Đen = False

        # Iterative deepening (tăng dần độ sâu tìm kiếm)
        for current_depth in range(1, self.depth + 1):
            if time.time() - start_time > max_time:
                break

            current_best_move = None
            current_best_eval = float('-inf') if maximizing else float('inf')

            for move in ordered_moves:
                board.push(move)
                eval = self.minimax(
                    board,
                    current_depth - 1,
                    float('-inf'),
                    float('inf'),
                    not maximizing
                )
                board.pop()

                if maximizing and eval > current_best_eval:
                    current_best_eval = eval
                    current_best_move = move
                elif not maximizing and eval < current_best_eval:
                    current_best_eval = eval
                    current_best_move = move

                # Cập nhật nếu tìm thấy chiếu tướng
                if (maximizing and current_best_eval > 9000) or (not maximizing and current_best_eval < -9000):
                    break

            if current_best_move is not None:
                best_move = current_best_move
                best_eval = current_best_eval

        elapsed_time = time.time() - start_time
        print(f"Đã đánh giá {self.nodes_evaluated} nút trong {elapsed_time:.2f} giây")
        print(f"Điểm đánh giá: {best_eval}")

        return best_move.uci() if best_move else None


def play_game():
    """
    Hàm chính để chơi cờ vua với AI
    """
    game = ChessGame()
    # Độ sâu 3 là mặc định, có thể điều chỉnh lên 4 hoặc 5 cho AI mạnh hơn
    # nhưng sẽ chậm hơn nhiều
    ai = ChessAI(depth=3)

    print("Chào mừng đến với trò chơi Cờ vua AI!")
    print("Bạn chơi quân trắng, AI chơi quân đen.")
    print("Để di chuyển, hãy nhập nước đi dưới dạng UCI (ví dụ: e2e4)")
    print("Nhập 'quit' để thoát game.")

    while not game.is_game_over():
        print("\nTrạng thái bàn cờ:")
        print(game.get_board())

        if game.get_board().turn:  # Lượt người chơi (quân trắng)
            legal_moves = game.get_legal_moves()
            print(f"Các nước đi hợp lệ: {legal_moves}")

            move = input("\nNhập nước đi của bạn: ")
            if move.lower() == 'quit':
                break

            if game.push_move(move):
                print("Nước đi hợp lệ!")
            else:
                print("Nước đi không hợp lệ, vui lòng thử lại.")
                continue
        else:  # Lượt AI (quân đen)
            print("AI đang suy nghĩ...")
            ai_move = ai.get_best_move(game)

            if ai_move:
                print(f"AI chọn nước đi: {ai_move}")
                game.push_move(ai_move)
            else:
                print("AI không thể tìm thấy nước đi tốt!")

        # Kiểm tra kết thúc sau mỗi nước đi
        if game.is_game_over():
            print("\nTrò chơi kết thúc!")
            print(f"Kết quả: {game.get_game_result()}")
            print(game.get_board())

            if game.get_board().is_checkmate():
                winner = "Người chơi" if not game.get_board().turn else "AI"
                print(f"{winner} đã chiến thắng bằng chiếu tướng!")
            elif game.get_board().is_stalemate():
                print("Hòa do hết nước đi (stalemate)!")
            elif game.get_board().is_insufficient_material():
                print("Hòa do không đủ quân để chiếu tướng!")
            elif game.get_board().is_seventyfive_moves():
                print("Hòa do quy tắc 75 nước đi!")
            elif game.get_board().is_fivefold_repetition():
                print("Hòa do lặp lại vị trí 5 lần!")

    print("Cảm ơn bạn đã chơi!")


if __name__ == "__main__":
    play_game()