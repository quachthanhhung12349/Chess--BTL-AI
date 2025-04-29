# Bài tập lớn bộ môn Trí tuệ nhân tạo - Game Cờ Vua
 
## Tác giả
1. [Nguyễn Hữu Lưu](https://github.com/legendy05) - 23021617
2. [Đoàn Thái Hùng](https://github.com/TachibanaHungDoan) - 23021565
3. [Quách Thanh Hưng](https://github.com/quachthanhhung12349) - 23021585
4. [Nguyễn Khánh Tùng](https://github.com/nktung20) - 23021713

## Mô tả
Bài tập lớn bộ môn AI, thiết kế một game Cờ vua. Chúng mình đã xây dựng một hệ thống cho phép người chơi chơi cờ vua đấu với nhau hoặc đấu với máy, sử dụng các thuật toán AI để đưa ra các nước đi tối ưu (đối với đấu với máy).   
Link demo: 

## Tính năng
### Chế độ chơi:  
+ PvP: người chơi đấu với người chơi
+ PvE: Người chơi đấu với bot
### Thuật toán AI sử dụng
Minimax + Cắt tỉa alpha-beta để tìm ra nước đi tối ưu cho máy
### Thư viện sử dụng
+ Pygame, Tkinter: UI-UX
+ Python-chess: Logic game 
+ Stockfish: Chỉ sử dụng với mục đích test (không áp dụng vào bot)

## Cài đặt
### Yêu cầu:
Python 3.8+
Git
Stockfish, python-chess
### Hướng dẫn
1. **Clone repository**:
   ```bash
   git clone https://github.com/quachthanhhung12349/Chess--BTL-AI.git
   cd Chess--BTL-AI
   ```

2. **Cài đặt thư viện**:
   ```bash
   pip install pygame python-chess
   ```

3. **Cài đặt Stockfish**:
   - Tải từ [stockfishchess.org](https://stockfishchess.org/download/).  
   - Đặt file thực thi vào thư mục dự án (ví dụ: `stockfish/`).  
   - Chương trình tự động chọn file Stockfish dựa trên hệ điều hành.  

4. **Chạy chương trình**:
   ```bash
   python mainwithui.py
   ```




