import chess
"""
#Notes: FEN là định dạng tiêu chuẩn  để mô tả một vị trí cụ thể trên bàn cờ vua.
Nó là một chuỗi ASCII duy nhất chứa tất cả thông tin cần thiết để tái tạo một thế cờ.
"""
def minimax(board, depth, alpha, beta, is_maximizing):
        if depth == 0 or board.is_game_over():
            return evaluate_board(board), None

        best_move = None

        if is_maximizing:
            max_eval = float("-inf")
            for move in board.legal_moves:
                board.push(move)
                eval, _ = minimax(board, depth - 1, alpha, beta, False)
                board.pop()
                if eval > max_eval:
                    max_eval = eval
                    best_move = move
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval, best_move

        else:
            min_eval = float("inf")
            for move in board.legal_moves:
                board.push(move)
                eval, _ = minimax(board, depth - 1, alpha, beta, True)
                board.pop()
                if eval < min_eval:
                    min_eval = eval
                    best_move = move
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval, best_move
        
def evaluate_board(board):
    if board.is_checkmate():
        return -9999 if board.turn else 9999
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    value = 0

    # Giá trị từng quân
    piece_values = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000
    }

    # Vị trí ưu tiên cho các quân
    center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
    king_safety_bonus = [chess.G1, chess.H1, chess.G8, chess.H8]  # vị trí gần castling

    for piece_type in piece_values:
        white_squares = board.pieces(piece_type, chess.WHITE)
        black_squares = board.pieces(piece_type, chess.BLACK)

        value += len(white_squares) * piece_values[piece_type]
        value -= len(black_squares) * piece_values[piece_type]

        # Ưu tiên kiểm soát trung tâm
        for sq in white_squares:
            if sq in center_squares:
                value += 10
        for sq in black_squares:
            if sq in center_squares:
                value -= 10

    # King safety (hạn chế vua lang thang sớm)
    king_pos_white = board.king(chess.WHITE)
    king_pos_black = board.king(chess.BLACK)

    if king_pos_white in king_safety_bonus:
        value += 20
    if king_pos_black in king_safety_bonus:
        value -= 20

    return value if board.turn == chess.WHITE else -value


    
class ChessGame:
    """
    Lớp chứa logic của trò chơi cờ vua.
    Các chức năng chính:
      - Khởi tạo bàn cờ.
      - Cung cấp danh sách nước đi hợp lệ.
      - Thực hiện nước đi và cập nhật trạng thái bàn cờ.
      - Kiểm tra điều kiện kết thúc game.
      - Xử lý nhập thành, phong hậu, bắt tốt qua đường.
    """

    def __init__(self):
        """Khởi tạo bàn cờ với trạng thái mặc định."""
        self.board = chess.Board()
        self.game_over_status = None

    def get_board(self):
        """Trả về đối tượng bàn cờ hiện tại."""
        return self.board

    def get_fen(self):
        """Trả về chuỗi FEN thể hiện trạng thái hiện tại của bàn cờ."""
        return self.board.fen()

    def get_legal_moves(self):
        """Trả về danh sách các nước đi hợp lệ dưới dạng UCI string."""
        return [move.uci() for move in self.board.legal_moves]

    def push_move(self, move_uci):
        """
        Thực hiện nước đi dựa trên chuỗi UCI nhận vào.

        Nếu nước đi hợp lệ, quân cờ sẽ được di chuyển.
        Kiểm tra xem có nhập thành, phong hậu hoặc bắt tốt qua đường không.

        :param move_uci: Nước đi dưới dạng UCI (ví dụ 'e2e4')
        :return: True nếu nước đi được thực hiện thành công, False nếu không hợp lệ.
        """
        try:
            move = chess.Move.from_uci(move_uci)

            if move in self.board.legal_moves:
                piece = self.board.piece_at(move.from_square)
                """
                Kiểm tra phong hậu (nếu tốt đi đến hàng cuối mà chưa có ký hiệu phong quân,
                mặc định chọn hậu
                """
                # if self.board.piece_at(move.from_square).piece_type == chess.PAWN and (
                #         chess.square_rank(move.to_square) in [0, 7]):
                #     move.promotion = chess.QUEEN  # Mặc định phong hậu nếu không có chỉ định
                if piece and piece.piece_type == chess.PAWN:
                    if chess.square_rank(move.to_square) in [0, 7] and move.promotion is None:
                        move = chess.Move(move.from_square, move.to_square, promotion=chess.QUEEN)
                self.board.push(move)
                return True
            else:
                return False
        except ValueError as e:
            print("Lỗi định dạng nước đi:", e)
            return False

    def is_game_over(self):
        """Kiểm tra tình trạng kết thúc trò chơi."""
        return self.board.is_game_over() or self.game_over_status is not None

    def get_game_result(self):
        """Trả về kết quả ván cờ dưới dạng chuỗi, ví dụ: '1-0', '0-1', '1/2-1/2'."""
        if self.game_over_status:
            return self.game_over_status
        return self.board.result()

    def reset_game(self):
        """Thiết lập lại bàn cờ để bắt đầu ván mới."""
        self.board.reset()
        self.game_over_status = None

    def declare_winner(self, winner_color):
        if winner_color == chess.WHITE:
            self.game_over_status = "White wins on time"
        elif winner_color == chess.BLACK:
            self.game_over_status = "Black wins on time"
    


