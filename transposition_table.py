class TranspositionTable:
    def __init__(self, size=1000000):  # Adjust size as needed
        self.table = {}
        self.size = size
        self.hits = 0
        self.collisions = 0

    def store(self, board, depth, evaluation, move=None, node_type=None):
        hash_value = board.zobrist_hash()
        if hash_value in self.table:
            self.collisions += 1
        self.table[hash_value] = {
            'evaluation': evaluation,
            'depth': depth,
            'move': move,
            'node_type': node_type
        }
        # Optional: Implement a mechanism to handle table overflow if needed
        if len(self.table) > self.size:
            # Simple replacement strategy (e.g., replace oldest entry or entry with lower depth)
            self.table.pop(next(iter(self.table)))

    def lookup(self, board, depth, alpha, beta):
        hash_value = board.zobrist_hash()
        if hash_value in self.table:
            entry = self.table[hash_value]
            if entry['depth'] >= depth:
                self.hits += 1
                eval = entry['evaluation']
                node_type = entry.get('node_type')

                if node_type == 'exact':
                    return eval, entry.get('move')
                elif node_type == 'alpha':
                    if eval <= alpha:
                        return alpha, entry.get('move')
                elif node_type == 'beta':
                    if eval >= beta:
                        return beta, entry.get('move')
            return None, entry.get('move')  # Return stored move for move ordering
        return None, None

    def get_stored_move(self, board):
        hash_value = board.zobrist_hash()
        if hash_value in self.table:
            return self.table[hash_value].get('move')
        return None

    def clear(self):
        self.table.clear()
        self.hits = 0
        self.collisions = 0