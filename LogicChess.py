import chess
"""
#Notes: FEN là định dạng tiêu chuẩn  để mô tả một vị trí cụ thể trên bàn cờ vua.
Nó là một chuỗi ASCII duy nhất chứa tất cả thông tin cần thiết để tái tạo một thế cờ.
"""

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
            if isinstance(move_uci, chess.Move):
                move = move_uci  # đã là Move rồi thì không cần chuyển đổi
            else:
                move = chess.Move.from_uci(move_uci)  # nếu là chuỗi, mới cần chuyển

            # move = chess.Move.from_uci(move_uci)

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
            self.game_over_status = "White wins"
        elif winner_color == chess.BLACK:
            self.game_over_status = "Black wins"



