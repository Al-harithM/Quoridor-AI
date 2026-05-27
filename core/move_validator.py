class MoveValidator:
    @staticmethod
    def get_valid_pawn_moves(board, player_id):
        valid_moves = []
        px, py = board.pawns[player_id]
        
        # Check area around player for valid moves (includes jumps)
        # We scan a 5x5 grid centered on player to catch all jumps
        for x in range(px - 2, px + 3):
            for y in range(py - 2, py + 3):
                if MoveValidator.is_valid_move(board, player_id, x, y):
                    valid_moves.append((x, y))
        return valid_moves

    @staticmethod
    def is_valid_move(board, player_id, gx, gy):
        if not board.is_inside((gx, gy)): return False
        
        px, py = board.pawns[player_id]
        if (gx, gy) == (px, py): return False

        opponent_id = 2 if player_id == 1 else 1
        ox, oy = board.pawns[opponent_id]
        if (gx, gy) == (ox, oy): return False

        dx = gx - px
        dy = gy - py
        dist = abs(dx) + abs(dy)

        # Helper for single step check
        def can_step(x1, y1, x2, y2):
            if x2 == x1: # Vertical
                if y2 > y1: return not board.block[(x1, y1)]["down"]
                if y2 < y1: return not board.block[(x1, y1)]["up"]
            elif y2 == y1: # Horizontal
                if x2 > x1: return not board.block[(x1, y1)]["right"]
                if x2 < x1: return not board.block[(x1, y1)]["left"]
            return False

        # 1 Step Move
        if dist == 1:
            return can_step(px, py, gx, gy)

        # 2 Step Jump (Straight)
        elif dist == 2 and (dx == 0 or dy == 0):
            mx, my = px + dx // 2, py + dy // 2
            if (mx, my) == (ox, oy): 
                return can_step(px, py, mx, my) and can_step(mx, my, gx, gy)

        # Diagonal Jump
        elif abs(dx) == 1 and abs(dy) == 1:
            if (ox, oy) == (gx, py): # Opponent Horizontal
                if can_step(px, py, ox, oy) and can_step(ox, oy, gx, gy):
                     # Check if straight jump was blocked
                     sx, sy = ox + (ox - px), oy
                     if not board.is_inside((sx, sy)) or not can_step(ox, oy, sx, sy):
                         return True
            elif (ox, oy) == (px, gy): # Opponent Vertical
                if can_step(px, py, ox, oy) and can_step(ox, oy, gx, gy):
                     # Check if straight jump was blocked
                     sx, sy = ox, oy + (oy - py)
                     if not board.is_inside((sx, sy)) or not can_step(ox, oy, sx, sy):
                         return True
        
        return False