from LogicChess import ChessGame

def main():
    #Khởi tạo đối tượng ChessGame.
    game = ChessGame()

    #Vòng lặp game chính
    while not game.is_game_over():
        # Hiển thị bàn cờ
        print("\nBàn cờ hiện tại:")
        print(game.get_board())

        # Hiển thị nước đi hợp lệ
        legal_moves = game.get_legal_moves()
        print("\nCác nước đi hợp lệ:", legal_moves)

        # Nhập nước đi
        move_input = input("Nhập nước đi (UCI format, ví dụ 'e2e4'): ")

        if move_input in legal_moves:
            game.push_move(move_input)
        else:
            print("⚠ Nước đi không hợp lệ. Vui lòng nhập lại!")

    # Kết thúc trò chơi
    print("\n🏁 Trò chơi kết thúc!")
    print("Kết quả:", game.get_game_result())

if __name__ == "__main__":
    main()