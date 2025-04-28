import chess
import time
import evaluation_simple
import evaluation_advanced
import random
import chess.polyglot
import sys

sys.setrecursionlimit(10000)

# Define infinity
INF = float('inf')

# Define transposition table flags
TT_EXACT = 0
TT_LOWERBOUND = 1
TT_UPPERBOUND = 2

# Define the initial delta for aspiration windows
ASPIRATION_WINDOW_DELTA = 10 # Centipawns
ASPIRATION_WINDOW_DELTA_AFTER = [25, 50, 100, INF]

# Transposition Table
transposition_table = {}

# Global tables for Killer Moves and History Heuristic
MAX_SEARCH_DEPTH = 20
KILLER_MOVES_COUNT = 2
killer_moves = [[None for _ in range(KILLER_MOVES_COUNT)] for _ in range(MAX_SEARCH_DEPTH)]
history_table = [[0 for _ in range(64)] for _ in range(64)]

# Path to opening book
OPENING_BOOK_PATH = "/home/linux-mint-cb303/Desktop/UET/HK2 2024/AI/Chess--BTL-AI-/Perfect2023.bin"

opening_book = None

def load_opening_book(book_path):
    global opening_book
    try:
        opening_book = chess.polyglot.open_reader(book_path)
        print(f"Opening book loaded from {book_path}")
    except Exception as e:
        print(f"Could not load opening book from {book_path}: {e}")
        opening_book = None

# Define piece values for MVV-LVA
PIECE_VALUES = {
    chess.PAWN: 100, chess.KNIGHT: 300, chess.BISHOP: 320,
    chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 20000
}

def calculate_mvv_lva(board, move):
    piece_type_score = {
        chess.PAWN: 1, chess.KNIGHT: 2, chess.BISHOP: 3,
        chess.ROOK: 4, chess.QUEEN: 5, chess.KING: 6
    }
    victim_piece_type = board.piece_type_at(move.to_square)
    aggressor_piece_type = board.piece_type_at(move.from_square)
    if victim_piece_type is None or aggressor_piece_type is None: return 0
    victim_score = piece_type_score.get(victim_piece_type, 0)
    aggressor_score = piece_type_score.get(aggressor_piece_type, 0)
    return victim_score * 10 + (10 - aggressor_score)

def order_moves(board, current_depth, principal_variation=None, hash_move=None):
    legal_moves = list(board.legal_moves)
    ordered_moves = []

    if hash_move and hash_move in legal_moves:
        ordered_moves.append(hash_move)
        legal_moves.remove(hash_move)

    if principal_variation:
         pv_move = principal_variation[0] if principal_variation else None
         if pv_move and pv_move in legal_moves:
             ordered_moves.append(pv_move)
             legal_moves.remove(pv_move)

    capture_moves = []
    quiet_moves = []
    for move in legal_moves:
        if board.is_capture(move):
            capture_moves.append(move)
        else:
            quiet_moves.append(move)

    capture_moves_with_scores = [(move, calculate_mvv_lva(board, move)) for move in capture_moves]
    capture_moves_with_scores.sort(key=lambda item: item[1], reverse=True)
    sorted_capture_moves = [move for move, score in capture_moves_with_scores]

    killer_moves_for_depth = []
    if 0 <= current_depth < MAX_SEARCH_DEPTH:
        killer_moves_for_depth = [move for move in killer_moves[current_depth] if move is not None] # Filter None

    killer_moves_to_add = []
    remaining_quiet_moves = []
    for move in quiet_moves:
        if move in killer_moves_for_depth:
            killer_moves_to_add.append(move)
        else:
            remaining_quiet_moves.append(move)

    quiet_moves_with_scores = [(move, history_table[move.from_square][move.to_square]) for move in remaining_quiet_moves]
    quiet_moves_with_scores.sort(key=lambda item: item[1], reverse=True)
    sorted_quiet_moves = [move for move, score in quiet_moves_with_scores]

    ordered_moves.extend(sorted_capture_moves)
    ordered_moves.extend(killer_moves_to_add)
    ordered_moves.extend(sorted_quiet_moves)

    seen = set()
    ordered_moves_unique = []
    for move in ordered_moves:
        if move not in seen:
            ordered_moves_unique.append(move)
            seen.add(move)

    return ordered_moves_unique

# Define parameters for Null Move Pruning
NMR_MIN_DEPTH = 3
NMR_REDUCTION = 2

# Define futility margins
FUTILITY_MARGINS = [0, 200, 300]

QS_MAX_DEPTH = 2 # A small QS depth is more typical

def quiescence_search(board, alpha, beta, color, qs_depth, stop_time):
    """
    Performs a limited depth search focusing on noisy positions. Includes time checks and TT.
    """
    # --- Time Check ---
    if time.time() > stop_time:
        return None, None

    # Check for immediate game over within QS (can happen after captures/checks)
    if board.is_game_over(claim_draw=True):
         if board.is_checkmate():
             return -INF, None # Checkmate is bad for the player whose turn it is
         else:
             return 0, None # Draw

    board_hash = chess.polyglot.zobrist_hash(board)

    # --- Transposition Table Lookup in QS ---
    if board_hash in transposition_table:
        entry = transposition_table[board_hash]
        if entry['depth'] >= qs_depth: # Check if stored QS depth is sufficient
           tt_value = entry['value']
           if entry['flag'] == TT_EXACT: return tt_value, entry.get('best_move')
           elif entry['flag'] == TT_LOWERBOUND: alpha = max(alpha, tt_value)
           elif entry['flag'] == TT_UPPERBOUND: beta = min(beta, tt_value)
           if alpha >= beta: return tt_value, entry.get('best_move')

    # --- Stand-pat evaluation ---
    stand_pat = evaluation_advanced.evaluate(board) * color

    # Initialize best_value with stand_pat
    best_value = stand_pat

    # Alpha-Beta Pruning with stand-pat
    alpha = max(alpha, stand_pat)
    if alpha >= beta:
        # Store stand-pat cutoff in TT (depth 0 or current qs_depth if cutoff happens here)
        # For simplicity, let's handle TT store after the loop for all outcomes.
        pass # TT store handled below

    # --- Generate and evaluate ONLY noisy moves (captures and checks) ---
    noisy_moves = []
    # Iterate legal moves and add captures
    for move in board.legal_moves:
         if board.is_capture(move):
             noisy_moves.append(move)
         # Optional: Add checks here by making the move and checking board.is_check()

    # Order noisy moves (MVV-LVA for captures is important here)
    # For simplicity, we just use the list of captures, but MVV-LVA sorting is recommended.
    # noisy_moves.sort(key=lambda move: calculate_mvv_lva(board, move), reverse=True) # Example sorting

    if not noisy_moves:
        # If no noisy moves, this is a quiet position. Return stand-pat.
        # Store this quiet position's evaluation in TT (depth 0 QS)
        if time.time() <= stop_time: # Only store if not timed out
            transposition_table[board_hash] = {'value': stand_pat, 'depth': 0, 'flag': TT_EXACT, 'best_move': None}
        return stand_pat, None

    original_alpha = alpha # Store original alpha for TT store flag

    # Iterate through noisy moves
    for move in noisy_moves:
        # --- Time Check ---
        if time.time() > stop_time:
             return None, None
        # --- End Time Check ---

        board.push(move)
        # Recursive call to quiescence search with reduced QS depth and stop_time
        value, _ = quiescence_search(board, -beta, -alpha, -color, qs_depth - 1, stop_time)
        board.pop()

        # --- Handle Time Termination from recursive call ---
        if value is None: return None, None

        value = -value

        if value > best_value:
            best_value = value

        # Alpha-Beta Pruning within QS
        alpha = max(alpha, best_value)
        if alpha >= beta:
            break

    # --- Transposition Table Store in QS ---
    if time.time() <= stop_time: # Only store if not timed out
        flag = TT_EXACT
        if best_value <= original_alpha: flag = TT_UPPERBOUND
        elif best_value >= beta: flag = TT_LOWERBOUND

        transposition_table[board_hash] = {
            'value': best_value,
            'depth': qs_depth, # Store the remaining QS depth
            'flag': flag,
            'best_move': None # Best move typically not stored for QS nodes
        }

    return best_value, None

def calculate_lmr_reduction(depth, move_index):
    reduction = 0
    if depth >= 3 and move_index >= 3:
        reduction = 1
        if depth >= 4 and move_index >= 5:
            reduction = 2
    return max(0, reduction)

FUTILITY_MARGINS = [0, 200, 300] # Margins for depths 0, 1, 2

NMR_MIN_DEPTH = 3
NMR_REDUCTION = 2

def negamax(board, depth, alpha, beta, color, stop_time, principal_variation=None):
    """
    Negamax with Alpha-Beta, Transposition Table, Time Control, Pruning, and Heuristic Updates.
    Uses a stop_time for consistent time checks.
    """
    # --- Time Check ---
    if time.time() > stop_time:
        return None, None

    # Check for immediate game over (before TT lookup at non-root nodes)
    if board.is_game_over(claim_draw=True):
         if board.is_checkmate(): return -INF, None
         else: return 0, None

    board_hash = chess.polyglot.zobrist_hash(board)

    # --- Transposition Table Lookup ---
    if board_hash in transposition_table:
       entry = transposition_table[board_hash]
       if entry['depth'] >= depth:
            tt_value = entry['value']
            # Adjust TT value for current player's perspective if needed (already handled by negamax structure)

            if entry['flag'] == TT_EXACT:
                 # Verify mate/draw scores from TT if necessary, otherwise trust
                 return tt_value, entry.get('best_move')
            elif entry['flag'] == TT_LOWERBOUND: alpha = max(alpha, tt_value)
            elif entry['flag'] == TT_UPPERBOUND: beta = min(beta, tt_value)

            if alpha >= beta:
                # Return the TT value that caused the cutoff
                return tt_value, entry.get('best_move')

    # --- Depth Limit Reached (Base case) ---
    if depth == 0:
        # If depth is 0 and game isn't over, go to quiescence search.
        value, _ = quiescence_search(board, alpha, beta, color, QS_MAX_DEPTH, stop_time)
        if value is None: return None, None # Handle timeout from QS
        return value, None

    """# --- Null Move Pruning ---
    if depth >= NMR_MIN_DEPTH and not board.is_check(): # Add endgame check
        original_turn = board.turn
        original_ep_square = board.ep_square
        board.turn = not board.turn
        board.ep_square = None

        # Perform a reduced-depth search after the null move
        null_move_value, _ = negamax(
            board, depth - NMR_REDUCTION - 1, -beta, -beta + 1, -color, stop_time, principal_variation
        )

        board.turn = original_turn
        board.ep_square = original_ep_square

        # --- Handle Time Termination from null move search ---
        if null_move_value is None: return None, None

        if -null_move_value >= beta:
             # Null move pruning allows a beta cutoff.
             return beta, None # Return beta and no specific move

    # --- Futility Pruning ---
    if depth < len(FUTILITY_MARGINS) and not board.is_check():
         static_eval = evaluation_advanced.evaluate(board) * color
         margin = FUTILITY_MARGINS[depth]
         if static_eval + margin <= alpha:
             return alpha, None # Futility pruning cutoff"""

    # --- Get hash move for move ordering ---
    hash_move = transposition_table.get(board_hash, {}).get('best_move')

    # --- Order moves using advanced heuristics ---
    move_order = order_moves(board, depth, principal_variation, hash_move)

    best_value = -INF
    best_move = None
    original_alpha = alpha

    # Flag to indicate if the search was terminated by time within this loop
    terminated_by_time = False

    for move_index, move in enumerate(move_order):
        # --- Time Check ---
        if time.time() > stop_time:
            terminated_by_time = True
            break
        # --- End Time Check ---

        board.push(move)

        # --- Principal Variation Search (PVS) and Late Move Reductions (LMR) ---
        should_do_full_depth_search = False
        current_search_depth = depth - 1
        apply_lmr = (move_index > 0 and depth >= 3 and not board.is_check()) # Add not in check for LMR safety

        if apply_lmr:
            reduction = calculate_lmr_reduction(depth, move_index)
            current_search_depth = depth - 1 - reduction
            current_search_depth = max(0, current_search_depth)

            if current_search_depth > 0:
                 # Null Window Search with Reduced Depth [-beta, -alpha + 1]
                 value, _ = negamax(board, current_search_depth, -beta, -(alpha + 1), -color, stop_time, principal_variation)

                 # --- Handle Time Termination ---
                 if value is None:
                      board.pop()
                      terminated_by_time = True
                      break
                 # --- End Time Termination Handling ---

                 value = -value # Negate value

                 # If null window search failed high (value > alpha), re-search full depth
                 if value > alpha:
                      should_do_full_depth_search = True
            else:
                 # If reduced depth is 0, proceed to full depth search (which hits QS)
                 should_do_full_depth_search = True


        # --- Full Depth Search (or Re-search) ---
        if not apply_lmr or should_do_full_depth_search:
             # Full window search [-beta, -alpha]
             value, _ = negamax(board, depth - 1, -beta, -alpha, -color, stop_time, principal_variation)

             # --- Handle Time Termination ---
             if value is None:
                  board.pop()
                  terminated_by_time = True
                  break
             # --- End Time Termination Handling ---

             value = -value # Negate value


        board.pop() # Unmake

        # --- Update best value and best move ---
        if value > best_value:
            best_value = value
            best_move = move

        # --- Alpha-Beta Pruning ---
        alpha = max(alpha, best_value)
        if alpha >= beta:
            # Update Killer and History Heuristics on Beta Cutoff for quiet moves
            if not board.is_capture(move):
                 if 0 <= depth < MAX_SEARCH_DEPTH:
                     if move not in killer_moves[depth]:
                         killer_moves[depth].insert(0, move)
                         if len(killer_moves[depth]) > KILLER_MOVES_COUNT:
                             killer_moves[depth].pop()
                 history_table[move.from_square][move.to_square] += depth

            break # Beta cutoff

    # --- Transposition Table Store ---
    if not terminated_by_time: # Only store if not timed out in this call
        flag = TT_EXACT
        if best_value <= original_alpha: flag = TT_UPPERBOUND
        elif best_value >= beta: flag = TT_LOWERBOUND

        transposition_table[board_hash] = {
            'value': best_value,
            'depth': depth,
            'flag': flag,
            'best_move': best_move
        }

    if terminated_by_time:
        return None, None
    else:
        # If best_move is still None here, it means no legal moves were available
        # in this position at this depth (should be caught by game over check)
        # or perhaps all moves led to positions where the recursive call returned None due to timeout.
        # In a normal completion, best_move should be set if there were moves.
        return best_value, best_move

def find_best_move_iterative_deepening_tt_book_aw(board, max_depth, time_limit_sec):
    """
    Finds the best move using iterative deepening with a time limit,
    transposition table, opening book, and aspiration windows.
    """
    # --- Opening Book Lookup ---
    if opening_book:
        try:
            book_move_entry = opening_book.weighted_choice(board)
            if book_move_entry:
                book_move = book_move_entry.move
                print(f"Found book move: {book_move}")
                return book_move
        except (IndexError, Exception) as e:
            pass # Continue to search if book fails

    start_time = time.time()
    stop_time = start_time + time_limit_sec # Calculate stop time once

    best_move_so_far = None
    previous_depth_score = 0
    principal_variation = []
    color = 1 if board.turn == chess.WHITE else -1

    for depth in range(1, max_depth + 1):
        # Check time before starting a new depth
        if time.time() > stop_time:
            print(f"Time limit reached before starting depth {depth}.")
            break

        # --- Aspiration Window Logic ---
        current_alpha = -INF
        current_beta = INF
        window = ASPIRATION_WINDOW_DELTA # Initial window size

        # Use aspiration window from depth 2 onwards, unless previous score was mate/draw
        if depth > 1 and abs(previous_depth_score) < INF:
            current_alpha = previous_depth_score - window
            current_beta = previous_depth_score + window

            # Ensure window is within bounds
            current_alpha = max(current_alpha, -INF)
            current_beta = min(current_beta, INF)


        # Loop for potential re-searches
        # Instead of iterating through a list of deltas, re-search with wider windows
        for asp_window_level in ASPIRATION_WINDOW_DELTA_AFTER:
            # Perform a depth-limited search with the current alpha-beta window and stop_time
            search_value, current_best_move = negamax(
                board.copy(), # Pass a copy for the top-level search
                depth,
                current_alpha,
                current_beta,
                color,
                stop_time, # Pass the calculated stop time
                principal_variation
            )

            # --- Check if the search was terminated by time ---
            if search_value is None:
                print(f"Depth {depth} search terminated by time.")
                # If search timed out, use the best move found in the last *completed* depth.
                break # Exit the while True loop and the depth loop

            # --- Aspiration Window Re-search Logic ---
            # If the search was NOT terminated by time, check for aspiration window failure
            if search_value < current_alpha:
                # Fail low: The true value is <= the lower bound of the window.
                # The window was too high. Re-search with a wider window
                #print(f"Depth {depth} Fail Low (Value: {search_value}, Window: [{current_alpha}, {current_beta}]). Re-searching.")
                current_beta = search_value + asp_window_level
                current_alpha = search_value - asp_window_level
                cnt = 0
                # The next iteration of the while loop will perform the re-search
            elif search_value > current_beta:
                # Fail high: The true value is >= the upper bound of the window.
                # The window was too low. Re-search with a wider window
                #print(f"Depth {depth} Fail High (Value: {search_value}, Window: [{current_alpha}, {current_beta}]). Re-searching.")
                current_beta = search_value + asp_window_level
                current_alpha = search_value - asp_window_level
                cnt = 0
                # The next iteration of the while loop will perform the re-search
            else:
                # Success: The search value is within the aspiration window. No re-search needed.
                break  # Exit the while True loop


        # --- End Aspiration Window Logic ---

        # If the search for this depth completed successfully (not timed out)
        # and resulted in a valid move
        if search_value is not None and current_best_move is not None:
            best_move_so_far = current_best_move # Update the best move found so far from a completed depth
            previous_depth_score = search_value # Store the value for the next iteration's window
            if best_move_so_far:
                 principal_variation = [best_move_so_far] # Update PV

            print(f"Depth {depth} completed. Best move: {best_move_so_far}, Value: {search_value}")
        else:
            # If search_value is None (timed out) or current_best_move is None (shouldn't happen on success),
            # break the iterative deepening loop.
            break

    # Return the best move found from the last *successfully completed* depth.
    # If no depth completed, best_move_so_far will be None.
    if best_move_so_far is None and board.legal_moves:
        print("Warning: No best move found by search, returning a random legal move.")
        return random.choice(list(board.legal_moves))

    return best_move_so_far


def game_end(board):
    if board.is_checkmate(): return True
    if board.is_insufficient_material(): return True
    if board.is_stalemate(): return True
    if board.can_claim_threefold_repetition(): return True
    if board.is_fifty_moves(): return True # Add 50-move rule check
    return False

# Example usage:
if __name__ == "__main__":
    load_opening_book(OPENING_BOOK_PATH) # Load the book once at the start

    board = chess.Board()
    # board.set_fen("r2qkb1r/1pp2ppp/p3p3/1Q1p4/1n1PNBb1/5N2/PPP2PPP/2KR1B1R b kq - 0 1") # Example FEN

    while not game_end(board):
        print(board)
        print("")
        tic = time.perf_counter()
        # Pass max_depth and time_limit_sec
        best_move = find_best_move_iterative_deepening_tt_book_aw(board, 15, 10) # Search up to depth 15, 10 sec time limit
        toc = time.perf_counter()
        print(f"Search time: {toc - tic:.4f} seconds")
        print(f"Best move found: {best_move}")

        if best_move is not None:
            board.push(best_move) # Push the move object directly
        else:
            # Fallback to a random move if no best move was found (should be rare with the implemented fallbacks)
             print("Error: No move returned by the AI. Making a random legal move.")
             if list(board.legal_moves):
                  random_move = random.choice(list(board.legal_moves))
                  board.push(random_move)
             else:
                  print("No legal moves available. Game over.")
                  break # No legal moves, game is over


    print(board.outcome())