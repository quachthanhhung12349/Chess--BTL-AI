import chess
import time
import evaluation_simple
import evaluation_advanced
import random
import chess.polyglot # Import polyglot for opening book

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


def order_moves(board, principal_variation=None, hash_move=None):
    """
    Orders moves for better alpha-beta pruning.
    Prioritizes hash move, principal variation, MVV-LVA captures, then other moves.
    """
    legal_moves = list(board.legal_moves)

    ordered_moves = []

    # Prioritize the hash move from the transposition table
    if hash_move and hash_move in legal_moves:
        ordered_moves.append(hash_move)
        legal_moves.remove(hash_move)

    # Prioritize the principal variation from the previous iterative deepening iteration
    if principal_variation:
         pv_move = principal_variation[0] if principal_variation else None
         if pv_move and pv_move in legal_moves:
             ordered_moves.append(pv_move)
             legal_moves.remove(pv_move)

    # Separate captures and non-captures from the remaining legal moves
    capture_moves = []
    other_moves = []
    for move in legal_moves:
        if board.is_capture(move):
            capture_moves.append(move)
        else:
            other_moves.append(move)

    # --- Implement MVV-LVA for Capture Moves ---
    # Calculate MVV-LVA score for each capture move
    capture_moves_with_scores = [(move, calculate_mvv_lva(board, move)) for move in capture_moves]

    # Sort capture moves by MVV-LVA score in descending order
    capture_moves_with_scores.sort(key=lambda item: item[1], reverse=True)

    # Extract the sorted capture moves
    sorted_capture_moves = [move for move, score in capture_moves_with_scores]
    # --- End MVV-LVA ---

    # Extend the ordered moves list with sorted captures and then other moves
    ordered_moves.extend(sorted_capture_moves)
    ordered_moves.extend(other_moves) # Non-captures are added after captures

    # Remove potential duplicates that might have been added if PV or hash move was also a capture
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
    Negamax implementation with Alpha-Beta Pruning, Transposition Table, and Time Control.

    Args:
        board: The current chess board state.
        depth: The remaining depth to search.
        alpha: The alpha cutoff value.
        beta: The beta cutoff value.
        color: 1 for the maximizing player (White), -1 for the minimizing player (Black).
        start_time: The time when the search started (from time.time()).
        time_limit_sec: The maximum time allowed for the search in seconds.
        principal_variation: The expected best line of play from shallower searches.


    Returns:
        A tuple containing the negamax value of the current node and the best move found.
        Returns (None, None) if the time limit is exceeded.
    """
    # --- Time Check at the beginning of the function ---
    if time.time() - start_time > time_limit_sec:
        return None, None # Signal termination due to time
    # --- End Time Check ---


    board_hash = chess.polyglot.zobrist_hash(board)

    # --- Transposition Table Lookup ---
    # (Keep the existing TT lookup logic here)
    if board_hash in transposition_table:
       entry = transposition_table[board_hash]
       if entry['depth'] >= depth:
           tt_value = entry['value']

           if entry['flag'] == TT_EXACT:
               return tt_value, entry.get('best_move')
           elif entry['flag'] == TT_LOWERBOUND:
               alpha = max(alpha, tt_value)
           elif entry['flag'] == TT_UPPERBOUND:
               beta = min(beta, tt_value)

           if alpha >= beta:
               return tt_value, entry.get('best_move')


    # --- Base case: Reached search depth or game over ---
    if depth == 0:
        if board.is_game_over():
             if board.is_checkmate():
                 return -INF * color, None
             elif board.is_stalemate():
                  return 0, None
        else:
            # Call quiescence search with time parameters
            value, _ = quiescence_search(board, alpha, beta, color, QS_MAX_DEPTH, start_time, time_limit_sec)
            # --- Handle Time Termination from QS ---
            if value is None:
                return None, None # Propagate the termination signal
            # --- End Time Termination Handling ---
            return value, None # QS returns the value, not a move for the main search


    # --- Rest of Negamax (Move ordering, loop, recursive call, TT store) ---
    hash_move = transposition_table.get(board_hash, {}).get('best_move')
    move_order = order_moves(board, principal_variation, hash_move)

    best_value = -INF
    best_move = None

    original_alpha = alpha # Store original alpha for TT

    for move in move_order:
        # --- Time Check before making a move and recursing ---
        if time.time() - start_time > time_limit_sec:
             return None, None # Signal termination due to time
        # --- End Time Check ---

        board.push(move)
        # Recursive call to negamax with time parameters
        value, _ = negamax(board, depth - 1, -beta, -alpha, -color, start_time, time_limit_sec, principal_variation)
        board.pop()

        # --- Handle Time Termination from recursive call ---
        if value is None:
             return None, None # Propagate the termination signal
        # --- End Time Termination Handling ---

        value = -value # Negate value after the recursive call returns a valid score

        if value > best_value:
            best_value = value
            best_move = move

        alpha = max(alpha, best_value)
        if alpha >= beta:
            break # Beta cutoff

    # --- Transposition Table Store ---
    # Only store in TT if the search was not terminated by time
    # (If we reached here, it means the loop completed or broke due to pruning, not time)
    flag = TT_EXACT
    if best_value <= original_alpha:
        flag = TT_UPPERBOUND
    elif best_value >= beta:
        flag = TT_LOWERBOUND

    transposition_table[board_hash] = {
        'value': best_value,
        'depth': depth,
        'flag': flag,
        'best_move': best_move
    }
    # --- End Transposition Table Store ---

    return best_value, best_move



def find_best_move_iterative_deepening_tt_book(board, max_depth, time_limit_sec):
    """
    Finds the best move using iterative deepening with a time limit,
    transposition table, and opening book.

    Args:
        board: The starting chess board state.
        max_depth: The maximum depth to search if time allows.
        time_limit_sec: The maximum time allowed for the search in seconds.

    Returns:
        The best move found within the time limit or from the opening book.
    """
    # --- Opening Book Lookup ---
    if opening_book:
        try:
            # Look up the current position in the opening book
            # weighted_choice() picks a move based on its weight in the book
            book_move_entry = opening_book.weighted_choice(board)
            if book_move_entry:
                book_move = book_move_entry.move
                print(f"Found book move: {book_move}")
                return book_move # Return the book move immediately
        except IndexError:
            # Position not found in the book or no moves available
            pass
        except Exception as e:
            print(f"Error reading opening book: {e}")
            pass # Continue to search if book reading fails
    # --- End Opening Book Lookup ---

    start_time = time.time()
    best_move_so_far = None
    principal_variation = []

    color = 1 if board.turn == chess.WHITE else -1

    for depth in range(1, max_depth + 1):
        if time.time() - start_time > time_limit_sec:
            print(f"Time limit reached at depth {depth - 1}.")
            break

        time_left = time_limit_sec - time.time() - start_time
        # Perform a depth-limited search using the transposition table
        # Pass a copy of the board to avoid modifying the original during search
        current_value, current_best_move = negamax(board.copy(), depth, -INF, INF, color, start_time, time_left, principal_variation)
        print(start_time)
        print(time_left)

        if time.time() - start_time <= time_limit_sec:
            best_move_so_far = current_best_move
            if best_move_so_far:
                 principal_variation = [best_move_so_far]

            print(f"Depth {depth} completed. Best move: {best_move_so_far}, Value: {current_value}")
        else:
            print(f"Depth {depth} did not complete within the time limit.")
            break

    # If no move was found (e.g., very short time limit and no book move),
    # fall back to a legal move to avoid crashing. This is a safeguard.
    if best_move_so_far is None and board.legal_moves:
        print("Warning: No best move found, returning a random legal move.")
        return random.choice(list(board.legal_moves))

    return best_move_so_far


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

    legal_moves = []
    while True:
        tic = time.perf_counter()
        best_move = find_best_move_iterative_deepening_tt_book_aw(board, 7, 10)
        toc = time.perf_counter()
        print(toc - tic)
        print(best_move)
        board.push_san(str(best_move))
        print(board)
        print("")
        if game_end(board):
            break

        tic = time.perf_counter()
        best_move = find_best_move_iterative_deepening_tt_book_aw(board, 7, 10)
        toc = time.perf_counter()
        print(toc - tic)
        print(best_move)
        board.push_san(str(best_move))
        print(board)
        print("")
        if game_end(board):
            break

    print(board.outcome())
