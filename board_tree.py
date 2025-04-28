import chess
import chess.engine
import chess.syzygy
import time
import evaluation_simple
import evaluation_advanced
import random
import chess.polyglot # Import polyglot for opening book
import sys
import stockfish
import os
import asyncio
import platform

script_dir = os.path.dirname(__file__)

OPENING_BOOK_PATH = os.path.join(script_dir, "Data/Perfect2023.bin") # Update this path to your opening book file
# Define the path to your opening book file
SYZYGY_PATH = os.path.join(script_dir, "Data/syzygy_endgame") # Update this path to your Syzygy tablebase directory
if platform.system() == "Windows":
    STOCKFISH_PATH = os.path.join(script_dir, "stockfishForWin/stockfish-windows-x86-64-avx2.exe")  # Đường dẫn cho Windows
else:
    STOCKFISH_PATH = os.path.join(script_dir, "stockfish/stockfish-ubuntu-x86-64-avx2")  # Đường dẫn cho Linux
sys.setrecursionlimit(10000) # Increase recursion limit for deep searches

# Define infinity
INF = float('inf')

# Define transposition table flags
TT_EXACT = 0
TT_LOWERBOUND = 1
TT_UPPERBOUND = 2

# Define the initial delta for aspiration windows
ASPIRATION_WINDOW_DELTA = 50 # Centipawns is a common unit
ASPIRATION_WINDOW_DELTA_AFTER = [100, INF]
# Transposition Table (using a dictionary for simplicity)
transposition_table = {}

# Add global tables for Killer Moves and History Heuristic
MAX_SEARCH_DEPTH = 20 # Define a reasonable maximum search depth for table size
KILLER_MOVES_COUNT = 2 # Store up to 2 killer moves per depth
TABLEBASE_PIECE_LIMIT = 5 # Define the maximum number of pieces for Syzygy tablebase probing
QS_MAX_DEPTH = 3 # Define the maximum depth for quiescence search

FUTILITY_MARGINS = [0, 200, 300] # Margins for depths 0, 1, 2 (adjust as needed)

NMR_MIN_DEPTH = 3 # Minimum remaining depth to apply NMR
NMR_REDUCTION = 2 # Depth reduction for the null move search

move_sequence = []
# Initialize killer moves table with None (or chess.Move.null())
# killer_moves[depth][move_index]
killer_moves = [[None for _ in range(KILLER_MOVES_COUNT)] for _ in range(MAX_SEARCH_DEPTH)]
# Initialize history table
# history_table[from_square][to_square]
history_table = [[0 for _ in range(64)] for _ in range(64)]

# Global variable to hold the loaded opening book
opening_book = None
syzygy_tablebase = None

def piece_count(board):
    """Counts the number of pieces on the board."""
    piece_count = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is not None:
            piece_count += 1
    return piece_count

def load_opening_book(book_path):
    """Loads the opening book."""
    global opening_book
    try:
        opening_book = chess.polyglot.open_reader(book_path)
        print(f"Opening book loaded from {book_path}")
    except Exception as e:
        print("Could not load opening book from {book_path}: {e}")
        opening_book = None # Ensure book is None if loading fails

def load_syzygy_tablebase(syzygy_path):
    """Loads the Syzygy tablebase."""
    global syzygy_tablebase
    try:
        syzygy_tablebase = chess.syzygy.open_tablebase(syzygy_path)
        print(f"Syzygy tablebase loaded from {syzygy_path}")
    except Exception as e:
        print("Could not load Syzygy tablebase from {SYZYGY_PATH}: {e}")
        syzygy_path = None # Ensure tablebase is None if loading fails

PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3.2, # Bishops are often slightly more valuable than knights
    chess.ROOK: 5,
    chess.QUEEN: 9,
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

def order_moves_tablebase(board):
    """
    Orders moves using the Syzygy tablebase.
    This is a placeholder function and should be implemented based on your needs.
    """
    # For now, let's just return the legal moves in random order
    zeroing_moves = []
    other_moves = []
    for move in board.legal_moves:
        if board.is_zeroing(move):
            zeroing_moves.append(move)
        else:
            other_moves.append(move)
    return zeroing_moves + other_moves
    
cnt = 0
# Assuming quiescence_search is implemented as previously discussed
# (It will also need to accept start_time and stop_time)
def quiescence_search(board, alpha, beta, color, qs_depth, start_time, stop_time):
    global move_sequence
    """
    Performs a limited depth search focusing on noisy positions (captures, checks).
    Includes time checks.
    """
    # --- Time Check ---
    if time.time() > stop_time:
        return None, None # Signal termination due to time
    # --- End Time Check ---

    if qs_depth == 0:
        #print(board)
        #print(move_sequence, evaluation_advanced.evaluate(board))
        time.sleep(0.05)
        return evaluation_advanced.evaluate(board) * color, None # Return value and None for move

    stand_pat = evaluation_advanced.evaluate(board) * color
    alpha = max(alpha, stand_pat)
    if alpha >= beta:
        return stand_pat, None

    legal_moves = list(board.legal_moves)
    capture_moves = [move for move in legal_moves if board.is_capture(move)]
    check_moves = [move for move in legal_moves if board.gives_check(move)]
    noisy_moves = capture_moves + check_moves # + check_moves if implemented

    if not noisy_moves:
        #print(board)
        #print(move_sequence, evaluation_advanced.evaluate(board))
        return stand_pat, None

    best_value = stand_pat
    best_move = None # Keep track of best move in QS if needed, though typically not returned

    for move in noisy_moves:
        board.push(move)
        move_sequence.append(str(move))
        
        # Recursive call to quiescence search with time parameters
        value, _ = quiescence_search(board, -beta, -alpha, -color, qs_depth - 1, start_time, stop_time)
        board.pop()
        move_sequence.pop() # Unmake the move from the sequence

        # --- Handle Time Termination from recursive call ---
        if _ is None and value is None:
             return None, None # Propagate the termination signal
        # --- End Time Termination Handling ---

        value = -value # Negate value after the recursive call returns a valid score

        if value > best_value:
            best_value = value
            # best_move = move # Optional: track best move in QS

        alpha = max(alpha, best_value)
        if alpha >= beta:
            break
    
    #if (qs_depth > 0): print(best_value, best_move)
    return best_value, best_move # Return best value found in QS

def calculate_lmr_reduction(depth, move_index):
    # Simple example: Reduction increases with move index and depth
    reduction = 0
    if depth >= 3 and move_index >= 3: # Apply LMR from a certain depth and move index
        reduction = 1
        if depth >= 4 and move_index >= 5:
            reduction = 2
            if depth >= 6 and move_index >= 10:
                reduction = 3
                if depth >= 8 and move_index >= 15:
                    reduction = 4
                    if depth >= 10 and move_index >= 20:
                        reduction = 5
        # More complex formulas involve logarithms or tables

    # Ensure reduction doesn't make depth negative
    return max(0, reduction)

max_depth_current = 0
def negamax(board, depth, alpha, beta, color, start_time, stop_time, principal_variation=None):
    """
    Negamax implementation with Alpha-Beta, Transposition Table, Time Control,
    and updates for Killer/History heuristics.
    """
    global cnt, max_depth_current
    # --- Time Check ---
    if time.time() > stop_time:
        return None, None # Signal termination due to time

    if max_depth_current - 1 == depth:
        cnt += 1
        #print(cnt)
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
        value, _ = quiescence_search(board, alpha, beta, color, QS_MAX_DEPTH, start_time, stop_time)
        if value is None and _ is None: return None, None # Handle timeout from QS
        return value, None

    # --- Null Move Pruning ---
    # Conditions for applying NMR:
    # 1. Sufficient remaining depth.
    # 2. Not in check (Null Move is unsound when in check).
    # 3. Not in an endgame (NMR can be unsound in positions with few pieces due to zugzwang).
    #    A simple endgame check could be based on the total number of pieces or material.
    # 4. Sufficient material (e.g., not just a lone king).

    # A very simple endgame check: Check if total material is below a threshold.
    # This requires a material count function or iterating over the board.
    # For simplicity in this example, we'll skip the endgame check, but it's important
    # in a real engine.

    if depth >= NMR_MIN_DEPTH + 1 and not board.is_check() and evaluation_advanced.get_game_phase(board) > 0.2: # Add endgame check here
        
        # Make a null move (toggle turn, handle potential en passant square cleanup)
        original_turn = board.turn
        original_ep_square = board.ep_square
        board.turn = not board.turn
        board.ep_square = None # En passant target is cleared after a null move
        # Perform a reduced-depth search after the null move
        # Use a narrow window [-beta, -beta + 1] for the null move probe
        # Value is from the perspective of the player *after* the null move (the opponent)
        null_move_value, _ = negamax(
            board,
            depth - NMR_REDUCTION - 1, # Subtract reduction and 1 ply for the null move
            -beta,
            -beta + 1, # Null window
            -color, # Opponent's turn
            start_time,
            stop_time,
            principal_variation # Pass PV (though its usefulness in null move is debatable)
        )
        # Unmake the null move
        board.turn = original_turn
        board.ep_square = original_ep_square

        # --- Handle Time Termination from null move search ---
        if null_move_value is None:
            return None, None # Propagate termination
        # --- End Time Termination Handling ---

        # If the null move search resulted in a value >= beta (for the opponent),
        # it means the opponent can't improve the position even with an extra move.
        # This position is likely very good for the current player, so prune.
        # The value from the null move search is from the opponent's perspective,
        # so if null_move_value >= beta, it means the value for the current player is <= -beta.
        # The cutoff condition is effectively if -null_move_value >= beta.
        
        if -null_move_value >= beta and cnt > 1:
             #print("Null Move Pruning: {null_move_value} >= {beta} (depth {depth})")
             # Null move pruning allows a beta cutoff. Return beta as the value.
             return beta, None # Return beta and no specific move

    # --- End Null Move Pruning ---
    
        # --- Futility Pruning ---
    # Only apply at shallow depths and if not in check (checks introduce complexity)
    # And if the alpha-beta window is not indicating a high-scoring node already
    if depth < len(FUTILITY_MARGINS) and not board.is_check():
         # Calculate the static evaluation from the current player's perspective
         static_eval = evaluation_advanced.evaluate(board) * color
         margin = FUTILITY_MARGINS[depth]

         # If static eval + margin is still less than alpha, prune
         if static_eval + margin <= alpha and cnt > 1:
             # Return alpha (or alpha + 1) to signal that this branch is not better
             # than the current best found so far.
             # Using alpha is a common way to implement this cutoff.
             return alpha, None # Return alpha and no specific move"""

    # --- Get hash move for move ordering ---
    hash_move = transposition_table.get(board_hash, {}).get('best_move')

    # --- Order moves using advanced heuristics ---
    move_order = order_moves(board, depth, principal_variation, hash_move)

    best_value = -INF # Start with the worst possible score
    best_move = None
    original_alpha = alpha # Store original alpha for TT flag determination

    for move_index, move in enumerate(move_order):

        # --- Time Check ---
        if time.time() > stop_time:
             return None, None
        # --- End Time Check ---

        board.push(move)
        move_sequence.append(str(move))

        # --- Principal Variation Search (PVS) and Late Move Reductions (LMR) ---
        should_do_full_depth_search = False
        current_search_depth = depth - 1

        # Condition for applying LMR (e.g., not the first move, and sufficient depth)
        apply_lmr = (move_index > 0 and depth >= 3) # Simple condition

        if apply_lmr:
            reduction = calculate_lmr_reduction(depth, move_index)
            current_search_depth = depth - 1 - reduction # Reduced depth

            # Ensure reduced depth is at least 0
            current_search_depth = max(0, current_search_depth)

            # --- Null Window Search with Reduced Depth ---
            # Only do null window if reduced depth is > 0. If reduced depth is 0,
            # it will go directly to quiescence search.
            if current_search_depth > 0:
                 # Perform a null window search [beta - 1, beta]
                 value, _ = negamax(board, current_search_depth, -beta, -(alpha + 1), -color, start_time, stop_time, principal_variation) # Note: alpha + 1 for null window
                 # --- Handle Time Termination ---
                 if value is None:
                      board.pop() # Unmake before returning on time out
                      move_sequence.pop()
                      return None, None
                 # --- End Time Termination Handling ---
                 value = -value # Negate the value from the recursive call
                 # If the null window search failed high (value >= beta),
                 # it means the move might be better than expected.
                 # We need to re-search with a full window and full depth.
                 if value > alpha: # Check against the original alpha
                      should_do_full_depth_search = True # Flag for a full depth re-search
                      #print("LMR Fail High: Re-searching move {move} at depth {depth}") # Optional: log LMR failures
            else:
                 
                 # If reduced depth is 0, we don't do a recursive call here.
                 # A full depth search (which will go to QS) is needed.
                 should_do_full_depth_search = True # Flag for a full depth search


        # --- Full Depth Search (or Re-search after LMR failure) ---
        # This branch is executed for the first move, or if LMR was not applied,
        # or if the reduced-depth null window search failed high.
        if not apply_lmr or should_do_full_depth_search:
             # Determine the window for the full depth search/re-search
             # For the first move, it's the full (alpha, beta) window.
             # For a re-search after LMR failure, it's still the full (alpha, beta) window.
             # If LMR wasn't applied, it's the full (alpha, beta) window.

             # The window for the recursive call is always [-beta, -alpha] from the opponent's perspective.
             # The value is negated after the call.
             

             value, _ = negamax(board, depth - 1, -beta, -alpha, -color, start_time, stop_time, principal_variation)


             # --- Handle Time Termination ---
             if value is None and _ is None:
                  board.pop()
                  move_sequence.pop() # Unmake before returning on time out
                  return None, None
             value = -value # Negate value
             # --- End Time Termination Handling ---


        board.pop() # Unmake the move
        move_sequence.pop() # Unmake the move from the sequence

        # --- Update best value and best move ---
        if value > best_value:
            best_value = value
            best_move = move

        # --- Alpha-Beta Pruning ---
        alpha = max(alpha, best_value)

        # --- Update Killer and History Heuristics ---
        # Update killer/history for the move if it caused a beta cutoff
        # (value >= beta) and is a quiet move.
        # The update logic is the same as before.
        if value >= beta:
            # This move caused a beta cutoff. Update Killer and History.
            if not board.is_capture(move):
                 # Update Killer Moves (using 'depth' of the current node)
                 if 0 <= depth < MAX_SEARCH_DEPTH:
                     if move not in killer_moves[depth]:
                         killer_moves[depth].insert(0, move)
                         if len(killer_moves[depth]) > KILLER_MOVES_COUNT:
                             killer_moves[depth].pop()

                 # Update History Heuristic (using the move's squares)
                 history_table[move.from_square][move.to_square] += depth # Or another scoring method


            break # Beta cutoff
    #if (depth == max_depth_current): print("")
    # --- Transposition Table Store ---
    if time.time() - start_time <= stop_time: # Check time again before storing
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

def find_best_move_iterative_deepening_tt_book_aw(board, max_depth, stop_time):
    """
    Finds the best move using iterative deepening with a time limit,
    transposition table, opening book, and aspiration windows.
    """
    # --- Opening Book Lookup ---
    global current_best_move, search_value, cnt, max_depth_current

    current_best_move = None
    search_value = None
    cnt = 0
    max_depth_current = 0

    if opening_book:
        try:
            book_move_entry = opening_book.weighted_choice(board)
            if book_move_entry:
                book_move = book_move_entry.move
                print("Found book move: {book_move}")
                return book_move
        except (IndexError, Exception) as e:
            # print("Error or position not in book: {e}") # Optional: log book errors
            pass  # Continue to search if book fails
    # --- End Opening Book Lookup ---
    else:
        load_opening_book(OPENING_BOOK_PATH)

    if syzygy_tablebase and piece_count(board) <= TABLEBASE_PIECE_LIMIT:
        best_move_so_far = None
        best_dtz = None
        best_move_has_priority = False
        move_order = order_moves_tablebase(board)
        try:
            for move in move_order:
                move_has_priority = False
                if (board.is_zeroing(move)):
                    move_has_priority = True
                board.push(move)
                dtz = syzygy_tablebase.probe_dtz(board)
                #print(move, dtz)
                if (dtz < 0):
                    #If we found a winning move: always prioritize zeroing moves that leads to zeroing the fastest. 
                    #If there's no winning zeroing move (but still has another winning move otherwise), we will prioritize the other moves that leads to zeroing the fastest.
                    if best_dtz is None or best_dtz >= 0 or (dtz > best_dtz and (move_has_priority or not best_move_has_priority)):
                        best_dtz = dtz
                        best_move_so_far = move
                        best_move_has_priority = move_has_priority
                elif (dtz > 0 and (best_dtz is None or best_dtz > 0)):
                    if best_dtz is None or dtz > best_dtz:
                        best_dtz = dtz
                        best_move_so_far = move
                elif (dtz == 0 and (best_dtz is None or best_dtz >= 0)):
                    if best_dtz is None or best_dtz > 0:
                        best_dtz = dtz
                        best_move_so_far = move
                board.pop()
            print(f"Best move from tablebase: {best_move_so_far}, DTZ: {best_dtz}")
            return best_move_so_far

        except Exception as e:
            # Handle potential errors during tablebase probing
            print(f"Error during tablebase probing: {e}")
            pass # Fall through to search
    elif not syzygy_tablebase:
        load_syzygy_tablebase(SYZYGY_PATH)
    
    start_time = time.time()
    stop_time = start_time + stop_time

    best_move_so_far = None
    # Store the score from the previous depth for aspiration windows
    previous_depth_score = 0  # Initialize to 0 or a reasonable default
    principal_variation = []
    color = 1 if board.turn == chess.WHITE else -1

    for depth in range(1, max_depth + 1):
        cnt = 0
        max_depth_current = depth
        # Check if time is running out before starting a new depth
        if time.time() > stop_time:
            print("Time limit reached at depth {depth - 1}.")
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
            time_left = stop_time - (time.time() - start_time)
            # Perform a depth-limited search with the current alpha-beta window
            search_value, current_best_move = negamax(board.copy(), depth, current_alpha, current_beta, color, start_time, stop_time,
                                                      principal_variation)
            #print(start_time)
            #print(time_left)

            # Check for timeout during the search
            if time.time() > stop_time or search_value is None:
                print(f"Depth {depth} search timed out.")
                # If a move was found in a previous, completed depth, return it.
                # Otherwise, the function will return None and the fallback handles it.
                break  # Exit the while True loop and the for loop

            # --- Aspiration Window Re-search Logic ---
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

        # If the search for this depth completed within the time limit (checked above)
        # and the search was successful (not timed out)
        if time.time() - start_time <= stop_time and current_best_move is not None:
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

def calculate_elo_change(rating_a, rating_b, result):
    """Calculate Elo rating change based on result (1.0 for win, 0.5 for draw, 0.0 for loss)"""
    k_factor = 32  # Standard K-factor for Elo calculations
    expected_a = 1.0 / (1.0 + 10**((rating_b - rating_a) / 400))
    change = k_factor * (result - expected_a)
    return change


async def play_match(num_games=10, your_elo=2200, stockfish_elo=2400):
    """Play a match between your engine and Stockfish with specified Elo settings"""
    if not os.path.exists(STOCKFISH_PATH):
        print(f"Error: Stockfish executable not found at '{STOCKFISH_PATH}'")
        print("Please download Stockfish and update the STOCKFISH_PATH variable.")
        return

    # Initialize game statistics
    your_wins = 0
    stockfish_wins = 0
    draws = 0
    your_current_elo = your_elo

    engine = None
    try:
        # Start Stockfish engine
        print(f"Starting Stockfish engine from: {STOCKFISH_PATH}")
        engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
        print("Stockfish engine started successfully.")

        # Set Stockfish Elo rating
        engine.configure({"UCI_LimitStrength": True, "UCI_Elo": stockfish_elo})
        print(f"Stockfish Elo set to: {stockfish_elo}")
        print(f"Your starting Elo: {your_elo}")
        print(f"\n{'Game':<6}{'Result':<10}{'Elo Change':<12}{'New Elo':<10}")
        print("-" * 38)

        # Play the specified number of games
        for game_num in range(1, num_games + 1):
            board = chess.Board()

            # Alternate who plays white
            your_color = chess.WHITE if game_num % 2 == 1 else chess.BLACK

            # Play the game
            while not game_end(board):
                if board.turn == your_color:
                    # Your engine's move
                    best_move = find_best_move_iterative_deepening_tt_book_aw(board, 11, 7)
                else:
                    # Stockfish's move
                    limit = chess.engine.Limit(depth=5)
                    result = engine.play(board, limit)
                    best_move = result.move

                # Make the move
                board.push(best_move)

            # Game result
            outcome = board.outcome()
            if outcome is None:
                # Handle stalemate or insufficient material
                if board.is_stalemate() or board.is_insufficient_material():
                    result = "Draw"
                    draws += 1
                    result_value = 0.5
                else:
                    # This should not happen if game_end is implemented correctly
                    result = "Draw"  # Default to draw
                    draws += 1
                    result_value = 0.5
            elif outcome.winner == your_color:
                result = "Win"
                your_wins += 1
                result_value = 1.0
            elif outcome.winner is None:  # Draw
                result = "Draw"
                draws += 1
                result_value = 0.5
            else:  # Stockfish wins
                result = "Loss"
                stockfish_wins += 1
                result_value = 0.0

            # Update your Elo rating
            elo_change = calculate_elo_change(your_current_elo, stockfish_elo, result_value)
            your_current_elo += elo_change

            # Print simple result line
            print(f"{game_num:<6}{result:<10}{elo_change:+.2f}      {your_current_elo:.2f}")

            # Clear transposition table between games if you're using one
            if 'transposition_table' in globals():
                transposition_table.clear()

        # Final statistics
        print("\n=== Final Results ===")
        print(f"Games: {num_games} | Wins: {your_wins} | Draws: {draws} | Losses: {stockfish_wins}")
        print(f"Final Elo: {your_current_elo:.2f} ({your_current_elo - your_elo:+.2f})")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if engine:
            print("\nShutting down Stockfish engine.")
            engine.quit()
            print("Engine shut down.")
# Example usage:
# Assuming 'initial_board' is a chess.Board object
async def main():
    if not os.path.exists(STOCKFISH_PATH):
        print(f"Error: Stockfish executable not found at '{STOCKFISH_PATH}'")
        print("Please download Stockfish and update the STOCKFISH_PATH variable.")
        exit()

        # Play 50 games against Stockfish with Elo 2200, starting from 1200
    await play_match(num_games=10, your_elo=2200, stockfish_elo=2400)


if __name__ == "__main__":
    if 'load_opening_book' in globals():
        load_opening_book(OPENING_BOOK_PATH)  # Load the opening book if function exists
    if 'load_syzygy_tablebase' in globals():
        load_syzygy_tablebase(SYZYGY_PATH)
    asyncio.run(main())
