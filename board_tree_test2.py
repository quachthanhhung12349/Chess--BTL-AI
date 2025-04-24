import chess
import time
import evaluation_simple
import evaluation_advanced
import random
import chess.polyglot # Import polyglot for opening book
import sys

sys.setrecursionlimit(10000) # Increase recursion limit for deep searches

# Define infinity
INF = float('inf')

# Define transposition table flags
TT_EXACT = 0
TT_LOWERBOUND = 1
TT_UPPERBOUND = 2

# Define the initial delta for aspiration windows
ASPIRATION_WINDOW_DELTA = 10 # Centipawns is a common unit
ASPIRATION_WINDOW_DELTA_AFTER = [25, 50, 100, INF]
# Transposition Table (using a dictionary for simplicity)
transposition_table = {}

# Add global tables for Killer Moves and History Heuristic
MAX_SEARCH_DEPTH = 20 # Define a reasonable maximum search depth for table size
KILLER_MOVES_COUNT = 2 # Store up to 2 killer moves per depth

# Initialize killer moves table with None (or chess.Move.null())
# killer_moves[depth][move_index]
killer_moves = [[None for _ in range(KILLER_MOVES_COUNT)] for _ in range(MAX_SEARCH_DEPTH)]

# Initialize history table
# history_table[from_square][to_square]
history_table = [[0 for _ in range(64)] for _ in range(64)]


# Define the path to your opening book file
# Make sure you have a Polyglot (.bin) opening book file
OPENING_BOOK_PATH = "/home/linux-mint-cb303/Desktop/UET/HK2 2024/AI/Chess--BTL-AI-/Perfect2023.bin" # <--- Update this path

# Global variable to hold the loaded opening book
opening_book = None

def load_opening_book(book_path):
    """Loads the opening book."""
    global opening_book
    try:
        opening_book = chess.polyglot.open_reader(book_path)
        print(f"Opening book loaded from {book_path}")
    except Exception as e:
        print(f"Could not load opening book from {book_path}: {e}")
        opening_book = None # Ensure book is None if loading fails


# Call this function once at the start of your program
# load_opening_book(OPENING_BOOK_PATH)


PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 300,
    chess.BISHOP: 320, # Bishops are often slightly more valuable than knights
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000 # King's value is high, but not typically used in material count for evaluation
}

# Helper function to calculate MVV-LVA score
def calculate_mvv_lva(board, move):
    """Calculates the MVV-LVA score for a capture move."""
    # Get the piece being captured (victim)
    victim_piece_type = board.piece_type_at(move.to_square)
    if victim_piece_type is None: # Should not happen for a capture, but good practice
        return 0

    # Get the piece performing the capture (aggressor)
    aggressor_piece_type = board.piece_type_at(move.from_square)
    if aggressor_piece_type is None: # Should not happen
        return 0

    # Get the base values
    victim_value = PIECE_VALUES.get(victim_piece_type, 0)
    aggressor_value = PIECE_VALUES.get(aggressor_piece_type, 0)

    # MVV-LVA score: Prioritize capturing high-value pieces.
    # As a tie-breaker, prioritize using low-value pieces to capture.
    mvv_lva_score = victim_value * 100 + (100 - aggressor_value)



    return mvv_lva_score


def order_moves(board, current_depth, principal_variation=None, hash_move=None):
    """
    Orders moves for better alpha-beta pruning using MVV-LVA, Killer Moves, and History Heuristic.
    Args:
        board: The current chess board state.
        current_depth: The current search depth (needed for Killer Moves).
        principal_variation: The expected best line of play from shallower searches.
        hash_move: The best move from the transposition table for this position.

    Returns:
        A list of legal moves ordered by heuristics.
    """
    legal_moves = list(board.legal_moves)

    # 1. Prioritize Hash Move
    ordered_moves = []
    if hash_move and hash_move in legal_moves:
        ordered_moves.append(hash_move)
        legal_moves.remove(hash_move) # Remove from legal_moves to avoid duplicates later

    # 2. Prioritize Principal Variation Move
    if principal_variation:
         pv_move = principal_variation[0] if principal_variation else None
         if pv_move and pv_move in legal_moves:
             ordered_moves.append(pv_move)
             legal_moves.remove(pv_move) # Remove from legal_moves

    # Separate remaining moves into captures and quiet moves
    capture_moves = []
    quiet_moves = []
    for move in legal_moves:
        if board.is_capture(move):
            capture_moves.append(move)
        else:
            quiet_moves.append(move)

    # 3. Order Captures using MVV-LVA
    # Calculate MVV-LVA score for each capture move
    capture_moves_with_scores = [(move, calculate_mvv_lva(board, move)) for move in capture_moves]
    # Sort capture moves by MVV-LVA score in descending order
    capture_moves_with_scores.sort(key=lambda item: item[1], reverse=True)
    sorted_capture_moves = [move for move, score in capture_moves_with_scores]

    # 4. Prioritize Killer Moves (for the current depth) within Quiet Moves
    killer_moves_for_depth = []
    if 0 <= current_depth < MAX_SEARCH_DEPTH:
        killer_moves_for_depth = killer_moves[current_depth]

    killer_moves_to_add = []
    remaining_quiet_moves = []
    for move in quiet_moves:
        if move in killer_moves_for_depth:
            killer_moves_to_add.append(move)
        else:
            remaining_quiet_moves.append(move)

    # 5. Order Remaining Quiet Moves using History Heuristic
    # Calculate history score for each remaining quiet move
    quiet_moves_with_scores = [(move, history_table[move.from_square][move.to_square]) for move in remaining_quiet_moves]
    # Sort quiet moves by history score in descending order
    quiet_moves_with_scores.sort(key=lambda item: item[1], reverse=True)
    sorted_quiet_moves = [move for move, score in quiet_moves_with_scores]


    # Combine all ordered move types
    ordered_moves.extend(sorted_capture_moves)
    ordered_moves.extend(killer_moves_to_add) # Add killer moves after captures
    ordered_moves.extend(sorted_quiet_moves) # Add history-ordered quiet moves after killers

    # Remove any potential duplicates that might have slipped through (less likely now but safe)
    seen = set()
    ordered_moves_unique = []
    for move in ordered_moves:
        if move not in seen:
            ordered_moves_unique.append(move)
            seen.add(move)

    return ordered_moves_unique



QS_MAX_DEPTH = 0
# Assuming quiescence_search is implemented as previously discussed
# (It will also need to accept start_time and time_limit_sec)
def quiescence_search(board, alpha, beta, color, qs_depth, start_time, time_limit_sec):
    """
    Performs a limited depth search focusing on noisy positions (captures, checks).
    Includes time checks.
    """
    # --- Time Check ---
    if time.time() - start_time > time_limit_sec:
        return None, None # Signal termination due to time
    # --- End Time Check ---

    if qs_depth == 0:
        return evaluation_advanced.evaluate(board) * color, None # Return value and None for move

    stand_pat = evaluation_advanced.evaluate(board) * color
    alpha = max(alpha, stand_pat)
    if alpha >= beta:
        return stand_pat, None

    legal_moves = list(board.legal_moves)
    capture_moves = [move for move in legal_moves if board.is_capture(move)]
    noisy_moves = capture_moves # + check_moves if implemented

    if not noisy_moves:
        return stand_pat, None

    best_value = stand_pat
    best_move = None # Keep track of best move in QS if needed, though typically not returned

    for move in noisy_moves:
        board.push(move)
        # Recursive call to quiescence search with time parameters
        value, _ = quiescence_search(board, -beta, -alpha, -color, qs_depth - 1, start_time, time_limit_sec)
        board.pop()

        # --- Handle Time Termination from recursive call ---
        if value is None:
             return None, None # Propagate the termination signal
        # --- End Time Termination Handling ---

        value = -value # Negate value after the recursive call returns a valid score

        if value > best_value:
            best_value = value
            # best_move = move # Optional: track best move in QS

        alpha = max(alpha, best_value)
        if alpha >= beta:
            break

    return best_value, best_move # Return best value found in QS



def negamax(board, depth, alpha, beta, color, start_time, time_limit_sec, principal_variation=None):
    """
    Negamax implementation with Alpha-Beta, Transposition Table, Time Control,
    and updates for Killer/History heuristics.
    """
    # --- Time Check ---
    if time.time() - start_time > time_limit_sec:
        return None, None # Signal termination due to time

    # --- Check for Immediate Game Over ---
    # Check this BEFORE transposition table lookup or depth check for terminal nodes
    if board.is_game_over(claim_draw=True): # claim_draw=True includes 50-move, 3-fold rep
        if board.is_checkmate():
            # The player whose turn it IS is checkmated. This is the worst possible outcome.
            return -INF, None
        else:
            # Any other draw condition (stalemate, repetition, 50-move, insufficient material)
            return 0, None
    # --- End Immediate Game Over Check ---

    board_hash = chess.polyglot.zobrist_hash(board)

    # --- Transposition Table Lookup ---
    # (Keep existing TT lookup logic)
    if board_hash in transposition_table:
       entry = transposition_table[board_hash]
       # Check if TT entry depth is sufficient ONLY IF the game isn't already over
       # (The game over check above takes precedence over TT)
       if entry['depth'] >= depth:
            tt_value = entry['value']
            # Be careful using TT values for checkmate/stalemate if not stored correctly
            # The absolute -INF/0 values from the game over check are more reliable

            if entry['flag'] == TT_EXACT:
                # Ensure we don't return a TT score that contradicts a proven mate/draw
                if tt_value == -INF or tt_value == 0: # Assuming TT stores absolute mate/draw scores correctly
                     return tt_value, entry.get('best_move')
                # Otherwise, proceed with caution or re-verify if needed
                # For now, let's trust the TT if flag is EXACT and depth sufficient
                return tt_value, entry.get('best_move')

            elif entry['flag'] == TT_LOWERBOUND:
                alpha = max(alpha, tt_value)
            elif entry['flag'] == TT_UPPERBOUND:
                beta = min(beta, tt_value)

            if alpha >= beta:
                # Return the TT value that caused the cutoff
                return tt_value, entry.get('best_move')


    # --- Depth Limit Reached (Base case) ---
    if depth == 0:
        # If depth is 0 and we already know game isn't over (from check above),
        # go to quiescence search.
        # Quiescence search should return the score relative to the current player.
        value, _ = quiescence_search(board, alpha, beta, color, QS_MAX_DEPTH, start_time, time_limit_sec)
        if value is None: return None, None # Handle timeout from QS
        return value, None

    # --- Get hash move for move ordering ---
    hash_move = transposition_table.get(board_hash, {}).get('best_move')

    # --- Order moves using advanced heuristics ---
    move_order = order_moves(board, depth, principal_variation, hash_move)

    best_value = -INF # Start with the worst possible score
    best_move = None
    original_alpha = alpha # Store original alpha for TT flag determination

    for move in move_order:
        # --- Time Check ---
        if time.time() - start_time > time_limit_sec:
            return None, None

        board.push(move)
        # print(board) # Optional: Keep for debugging if needed
        # print("")

        # Recursive call to negamax
        # Pass -beta, -alpha and -color
        value, _ = negamax(board, depth - 1, -beta, -alpha, -color, start_time, time_limit_sec, principal_variation)
        board.pop()

        # --- Handle Time Termination ---
        if value is None:
            return None, None # Propagate the termination signal

        # --- Negate the result ---
        # The recursive call returns the value from the opponent's perspective.
        # Negate it to get the value from the current player's perspective.
        value = -value

        # --- Update Best Move and Alpha ---
        if value > best_value:
            best_value = value
            best_move = move

        # --- Alpha-Beta Pruning ---
        alpha = max(alpha, best_value)
        if alpha >= beta:
             # Beta Cutoff: This move is too good, the opponent won't allow this line.
             # Update Killer/History Heuristics for the move that caused the cutoff
             if not board.is_capture(move): # Only update for quiet moves
                  # Update Killer Moves
                  if 0 <= depth < MAX_SEARCH_DEPTH:
                       if move not in killer_moves[depth]:
                            killer_moves[depth].insert(0, move)
                            if len(killer_moves[depth]) > KILLER_MOVES_COUNT:
                                 killer_moves[depth].pop()
                  # Update History Heuristic
                  history_table[move.from_square][move.to_square] += depth * depth # Square depth for more impact

             break # Prune remaining moves

    # --- Transposition Table Store ---
    if time.time() - start_time <= time_limit_sec: # Check time again before storing
        flag = TT_EXACT
        if best_value <= original_alpha: # Failed low (didn't improve alpha)
            flag = TT_UPPERBOUND
        elif best_value >= beta: # Failed high (caused beta cutoff)
            flag = TT_LOWERBOUND

        # Ensure we store meaningful values, especially for mates
        # If best_value indicates a mate found at this depth, adjust score relative to ply
        # (This helps prioritize faster mates, but is complex. Let's stick to INF for now)
        # If best_value is -INF, it means we are getting mated.

        transposition_table[board_hash] = {
            'value': best_value,
            'depth': depth,
            'flag': flag,
            'best_move': best_move
        }

    # print(best_value, best_move) # Optional debug

    return best_value, best_move

def find_best_move_iterative_deepening_tt_book_aw(board, max_depth, time_limit_sec):
    """
    Finds the best move using iterative deepening with a time limit,
    transposition table, opening book, and aspiration windows.
    """
    # --- Opening Book Lookup ---
    global current_best_move, search_value
    if opening_book:
        try:
            book_move_entry = opening_book.weighted_choice(board)
            if book_move_entry:
                book_move = book_move_entry.move
                print(f"Found book move: {book_move}")
                return book_move
        except (IndexError, Exception) as e:
            # print(f"Error or position not in book: {e}") # Optional: log book errors
            pass  # Continue to search if book fails
    # --- End Opening Book Lookup ---

    start_time = time.time()
    best_move_so_far = None
    # Store the score from the previous depth for aspiration windows
    previous_depth_score = 0  # Initialize to 0 or a reasonable default
    principal_variation = []

    color = 1 if board.turn == chess.WHITE else -1

    for depth in range(1, max_depth + 1):
        # Check if time is running out before starting a new depth
        if time.time() - start_time > time_limit_sec:
            print(f"Time limit reached at depth {depth - 1}.")
            break

        # --- Aspiration Window Logic ---
        # Use a loop to handle potential re-searches if the initial window fails
        # The window is used from depth 2 onwards
        current_alpha = -INF
        current_beta = INF
        if depth > 1:
            # Set the initial narrow window around the previous depth's score
            current_alpha = previous_depth_score - ASPIRATION_WINDOW_DELTA
            current_beta = previous_depth_score + ASPIRATION_WINDOW_DELTA

            # Ensure the window is within the bounds of -INF to INF
            current_alpha = max(current_alpha, -INF)
            current_beta = min(current_beta, INF)

        # Loop for potential re-searches
        for asp_window_level in ASPIRATION_WINDOW_DELTA_AFTER:
            time_left = time_limit_sec - (time.time() - start_time)
            # Perform a depth-limited search with the current alpha-beta window
            search_value, current_best_move = negamax(board.copy(), depth, current_alpha, current_beta, color, start_time, time_left,
                                                      principal_variation)
            #print(start_time)
            #print(time_left)

            # Check for timeout during the search
            if time.time() - start_time > time_limit_sec or search_value is None:
                print(f"Depth {depth} search timed out.")
                # If a move was found in a previous, completed depth, return it.
                # Otherwise, the function will return None and the fallback handles it.
                break  # Exit the while True loop and the for loop

            # --- Aspiration Window Re-search Logic ---
            if search_value < current_alpha:
                # Fail low: The true value is <= the lower bound of the window.
                # The window was too high. Re-search with a wider window
                print(
                    f"Depth {depth} Fail Low (Value: {search_value}, Window: [{current_alpha}, {current_beta}]). Re-searching.")
                current_beta = search_value + asp_window_level
                current_alpha = search_value - asp_window_level
                # The next iteration of the while loop will perform the re-search
            elif search_value > current_beta:
                # Fail high: The true value is >= the upper bound of the window.
                # The window was too low. Re-search with a wider window
                print(
                    f"Depth {depth} Fail High (Value: {search_value}, Window: [{current_alpha}, {current_beta}]). Re-searching.")
                current_beta = search_value + asp_window_level
                current_alpha = search_value - asp_window_level
                # The next iteration of the while loop will perform the re-search
            else:
                # Success: The search value is within the aspiration window. No re-search needed.
                break  # Exit the while True loop

        # --- End Aspiration Window Logic ---

        # If the search for this depth completed within the time limit (checked above)
        # and the search was successful (not timed out)
        if time.time() - start_time <= time_limit_sec and current_best_move is not None:
            best_move_so_far = current_best_move
            previous_depth_score = search_value  # Store the value for the next iteration's window
            if best_move_so_far:
                principal_variation = [best_move_so_far]  # Update PV for move ordering

            print(f"Depth {depth} completed. Best move: {best_move_so_far}, Value: {search_value}")
        else:
            # If the search timed out or no move was found, break the main loop
            break

    # If no move was found (e.g., very short time limit and no book move),
    # fall back to a legal move.
    if best_move_so_far is None and board.legal_moves:
        print("Warning: No best move found by search, returning a random legal move.")
        return random.choice(list(board.legal_moves))

    return best_move_so_far


def game_end(board):
    if board.is_checkmate():
        print(1)
        return True
    if board.is_insufficient_material():
        print(2)
        return True
    if board.is_stalemate():
        print(3)
        return True
    if board.can_claim_threefold_repetition():
        print(4)
        return True
    return False

# Example usage:
# Assuming 'initial_board' is a chess.Board object
if __name__ == "__main__":
    board = chess.Board()
    while True:
        tic = time.perf_counter()
        best_move = find_best_move_iterative_deepening_tt_book_aw(board, 15, 10)
        toc = time.perf_counter()
        print(toc - tic)
        print(best_move)
        board.push_san(str(best_move))
        print(board)
        print("")
        if game_end(board):
            break

        """legal_move_made = False
        while not legal_move_made:
            try:
                move = input("Enter your move: ")
                board.push_san(move)
                print(board)
                print("")
                legal_move_made = True
            except ValueError:
                print("Invalid move. Please try again.")"""

    print(board.outcome())
