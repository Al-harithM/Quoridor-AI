import copy
import random
import time
from collections import deque
from core.move_validator import MoveValidator


class QuoridorAI:
    def __init__(self, player_id, difficulty="medium"):
        self.player_id = player_id
        self.opponent_id = 2 if player_id == 1 else 1
        self.difficulty = difficulty
        self.tt = {}

    def get_best_move(self, game):
        start_time = time.time()

        sim_board = copy.deepcopy(game.board)
        my_walls = game.players[self.player_id].walls_remaining
        op_walls = game.players[self.opponent_id].walls_remaining

        self.my_recent_positions = set()
        for hist_board, _, _ in game.history[-4:]:
            self.my_recent_positions.add(hist_board.pawns[self.player_id])

        self.tt.clear()

        if self.difficulty == "easy":
            target_time = 1.0
            best_move = self._get_easy_move(sim_board, my_walls)

        elif self.difficulty == "medium":
            target_time = 2.0
            best_move = self._get_iterative_deepening_move(
                sim_board, my_walls, op_walls,
                time_limit=target_time, max_depth=2
            )

        elif self.difficulty == "hard":
            target_time = 4.0
            best_move = self._get_iterative_deepening_move(
                sim_board, my_walls, op_walls,
                time_limit=target_time, max_depth=5
            )

        elapsed = time.time() - start_time
        if elapsed < target_time:
            time.sleep(target_time - elapsed)

        return best_move


    def _get_easy_move(self, board, walls_remaining):
        moves = self.get_smart_moves(board, self.player_id, walls_remaining)
        if not moves:
            return None

        scored = []
        for move in moves:
            saved = self.apply_move(board, move, self.player_id)
            score = self.evaluate(board) + random.uniform(-12, 12)
            scored.append((score, move))
            self.undo_move(board, move, self.player_id, saved)

        scored.sort(key=lambda x: x[0], reverse=True)
        return random.choice(scored[:3])[1]

    def _get_iterative_deepening_move(self, board, my_walls, op_walls, time_limit, max_depth):
        start_time = time.time()
        best_move_overall = None
        best_score_overall = float('-inf')

        for current_depth in range(1, max_depth + 1):
            score, move = self.minimax(
                board, depth=current_depth, maximizing=True,
                alpha=float('-inf'), beta=float('inf'),
                my_walls=my_walls, op_walls=op_walls,
                start_time=start_time, time_limit=time_limit
            )

            elapsed = time.time() - start_time
            if elapsed > time_limit:
                break

            if move is not None:
                best_move_overall = move
                best_score_overall = score

        return best_move_overall


    def _get_state_hash(self, board, my_walls, op_walls, maximizing):
        return (
            board.pawns[1],
            board.pawns[2],
            my_walls,
            op_walls,
            frozenset(board.walls),
            maximizing
        )


    def minimax(self, board, depth, maximizing, alpha, beta,
                my_walls, op_walls, start_time, time_limit):

        # --- Time check ---
        if time.time() - start_time > time_limit:
            return self.evaluate(board), None

        # --- Transposition table ---
        state_key = self._get_state_hash(board, my_walls, op_walls, maximizing)
        if state_key in self.tt:
            stored_depth, stored_score, stored_move = self.tt[state_key]
            if stored_depth >= depth:
                return stored_score, stored_move

        # --- Terminal / leaf ---
        my_dist = board.get_shortest_path_distance(self.player_id)
        op_dist = board.get_shortest_path_distance(self.opponent_id)

        if my_dist == 0:
            return 100000 + depth * 10, None   # Win sooner = better
        if op_dist == 0:
            return -100000 - depth * 10, None  # Lose later = less bad

        if depth == 0:
            return self.evaluate(board), None

        current_player = self.player_id if maximizing else self.opponent_id
        walls_remaining = my_walls if maximizing else op_walls
        possible_moves = self.get_smart_moves(board, current_player, walls_remaining)

        if not possible_moves:
            return self.evaluate(board), None

        best_move = None

        if maximizing:
            max_eval = float('-inf')
            for move in possible_moves:
                saved = self.apply_move(board, move, current_player)
                new_my_walls = my_walls - 1 if move[0] == "wall" else my_walls

                eval_score, _ = self.minimax(
                    board, depth - 1, False, alpha, beta,
                    new_my_walls, op_walls, start_time, time_limit
                )
                self.undo_move(board, move, current_player, saved)

                if time.time() - start_time > time_limit:
                    return max_eval, best_move

                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move

                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break

            self.tt[state_key] = (depth, max_eval, best_move)
            return max_eval, best_move

        else:  # minimizing
            min_eval = float('inf')
            for move in possible_moves:
                saved = self.apply_move(board, move, current_player)
                new_op_walls = op_walls - 1 if move[0] == "wall" else op_walls

                eval_score, _ = self.minimax(
                    board, depth - 1, True, alpha, beta,
                    my_walls, new_op_walls, start_time, time_limit
                )
                self.undo_move(board, move, current_player, saved)

                if time.time() - start_time > time_limit:
                    return min_eval, best_move

                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move

                beta = min(beta, eval_score)
                if beta <= alpha:
                    break

            self.tt[state_key] = (depth, min_eval, best_move)
            return min_eval, best_move


    def evaluate(self, board):
        my_dist = board.get_shortest_path_distance(self.player_id)
        op_dist = board.get_shortest_path_distance(self.opponent_id)

        # --- Immediate win/loss ---
        if my_dist == 0:
            return 100000
        if op_dist == 0:
            return -100000
        if my_dist == float('inf'):
            return -99999
        if op_dist == float('inf'):
            return 99999

        score = 0

        #    op_dist - my_dist > 0  means we are closer = good
        path_lead = op_dist - my_dist
        score += path_lead * 80

        score -= my_dist * 20

        my_goal_row  = 0 if self.player_id  == 1 else 8
        op_goal_row  = 0 if self.opponent_id == 1 else 8
        my_row  = board.pawns[self.player_id][1]
        op_row  = board.pawns[self.opponent_id][1]

        my_row_dist = abs(my_row - my_goal_row)
        op_row_dist = abs(op_row - op_goal_row)

        if my_row_dist <= 3:
            score += (4 - my_row_dist) * 60   
        if op_row_dist <= 3:
            score -= (4 - op_row_dist) * 60   

        my_walls_remaining  = 0  
        total_walls_placed = len(board.walls)
        # Each player starts with 10 walls; 20 total
        # Rough estimate of AI walls used vs opponent walls used
        # (precise count passed through minimax; here we use a proxy)
        wall_advantage_proxy = 0  
        score += wall_advantage_proxy

       
        my_col = board.pawns[self.player_id][0]
        center_bonus = max(0, 3 - abs(my_col - 4)) * 5
        score += center_bonus

       
        if board.pawns[self.player_id] in self.my_recent_positions:
            score -= 300

        return score

    def get_smart_moves(self, board, player_id, walls_remaining):
        opponent_id = 2 if player_id == 1 else 1

        # --- Pawn moves, sorted by BFS distance to goal ---
        valid_pos = MoveValidator.get_valid_pawn_moves(board, player_id)
        target_row = 0 if player_id == 1 else 8

        pawn_moves = []
        for pos in valid_pos:
            dist_score = abs(pos[1] - target_row)
            pawn_moves.append((dist_score, ("move", pos)))
        pawn_moves.sort(key=lambda x: x[0])
        pawn_moves = [x[1] for x in pawn_moves]

        # --- Wall moves ---
        wall_moves = []

        my_dist = board.get_shortest_path_distance(player_id)
        op_dist = board.get_shortest_path_distance(opponent_id)

        should_block = (walls_remaining > 0) and (op_dist - my_dist < 5)

        if should_block:
            op_path = self.get_shortest_path(board, opponent_id)
            checked_walls = set()

            for i in range(min(len(op_path) - 1, 6)):
                curr     = op_path[i]
                next_step = op_path[i + 1]
                cx, cy = curr
                nx, ny = next_step

                if ny < cy:
                    candidates = [(cx, ny, "H"), (cx - 1, ny, "H")]
                elif ny > cy:
                    candidates = [(cx, cy, "H"), (cx - 1, cy, "H")]
                elif nx < cx:
                    candidates = [(nx, cy, "V"), (nx, cy - 1, "V")]
                elif nx > cx:
                    candidates = [(cx, cy, "V"), (cx, cy - 1, "V")]
                else:
                    candidates = []

                for wx, wy, wo in candidates:
                    if (wx, wy, wo) not in checked_walls:
                        checked_walls.add((wx, wy, wo))
                        if board.can_place_wall(wx, wy, wo):
                            # Score the wall: prefer walls that maximise
                            # the increase in the opponent's shortest path
                            wall_value = self._score_wall(board, wx, wy, wo, opponent_id)
                            if wall_value != -1:
                                wall_moves.append((wall_value, ("wall", (wx, wy, wo))))

            if op_dist < my_dist + 2:
                my_path = self.get_shortest_path(board, player_id)
                for i in range(min(len(my_path) - 1, 4)):
                    curr     = my_path[i]
                    next_step = my_path[i + 1]
                    cx, cy = curr
                    nx, ny = next_step

                    if ny != cy:  
                        flank_candidates = [(cx, cy, "V"), (cx - 1, cy, "V")]
                    else:          
                        flank_candidates = [(cx, cy, "H"), (cx, cy - 1, "H")]

                    for wx, wy, wo in flank_candidates:
                        if (wx, wy, wo) not in checked_walls:
                            checked_walls.add((wx, wy, wo))
                            if board.can_place_wall(wx, wy, wo):
                                wall_value = self._score_wall(board, wx, wy, wo, opponent_id)
                                if wall_value != -1:
                                    wall_moves.append((wall_value, ("wall", (wx, wy, wo))))

            wall_moves.sort(key=lambda x: x[0], reverse=True)

            max_walls = 6
            wall_moves = [x[1] for x in wall_moves[:max_walls]]

        if my_dist > op_dist:
            return wall_moves + pawn_moves
        else:
            return pawn_moves + wall_moves

    def _score_wall(self, board, wx, wy, wo, opponent_id):
        """
        Score a wall by how much it extends the opponent's shortest path.
        Higher is better (from our perspective).
        """
        before = board.get_shortest_path_distance(opponent_id)

        board.walls.append((wx, wy, wo))
        board.wall_owners[(wx, wy, wo)] = opponent_id
        if wo == "H":
            board.add_horizontal_wall(wx, wy)
        else:
            board.add_vertical_wall(wx, wy)

        after = board.get_shortest_path_distance(opponent_id)

        board.walls.pop()
        del board.wall_owners[(wx, wy, wo)]
        if wo == "H":
            board.block[(wx, wy)]["down"]         = False
            board.block[(wx + 1, wy)]["down"]     = False
            board.block[(wx, wy + 1)]["up"]       = False
            board.block[(wx + 1, wy + 1)]["up"]   = False
        else:
            board.block[(wx + 1, wy)]["left"]     = False
            board.block[(wx + 1, wy + 1)]["left"] = False
            board.block[(wx, wy)]["right"]        = False
            board.block[(wx, wy + 1)]["right"]    = False

        if after == float('inf'):
            return -1  
        return after - before   


    def get_shortest_path(self, board, player_id):
        start_pos  = board.pawns[player_id]
        target_row = 0 if player_id == 1 else 8

        queue   = deque([[start_pos]])
        visited = {start_pos}

        while queue:
            path = queue.popleft()
            cx, cy = path[-1]

            if cy == target_row:
                return path

            neighbors = []
            if cy + 1 < board.size and not board.block[(cx, cy)]["down"]:
                neighbors.append((cx, cy + 1))
            if cy - 1 >= 0 and not board.block[(cx, cy)]["up"]:
                neighbors.append((cx, cy - 1))
            if cx + 1 < board.size and not board.block[(cx, cy)]["right"]:
                neighbors.append((cx + 1, cy))
            if cx - 1 >= 0 and not board.block[(cx, cy)]["left"]:
                neighbors.append((cx - 1, cy))

            for nb in neighbors:
                if nb not in visited:
                    visited.add(nb)
                    queue.append(list(path) + [nb])

        return []

 
    def apply_move(self, board, move, player_id):
        if move[0] == "move":
            old_pos = board.pawns[player_id]
            board.pawns[player_id] = move[1]
            return old_pos
        else:
            wx, wy, wo = move[1]
            board.walls.append((wx, wy, wo))
            board.wall_owners[(wx, wy, wo)] = player_id
            if wo == "H":
                board.add_horizontal_wall(wx, wy)
            else:
                board.add_vertical_wall(wx, wy)
            return None

    def undo_move(self, board, move, player_id, saved_state):
        if move[0] == "move":
            board.pawns[player_id] = saved_state
        else:
            wx, wy, wo = move[1]
            board.walls.pop()
            del board.wall_owners[(wx, wy, wo)]
            if wo == "H":
                board.block[(wx, wy)]["down"]         = False
                board.block[(wx + 1, wy)]["down"]     = False
                board.block[(wx, wy + 1)]["up"]       = False
                board.block[(wx + 1, wy + 1)]["up"]   = False
            else:
                board.block[(wx + 1, wy)]["left"]     = False
                board.block[(wx + 1, wy + 1)]["left"] = False
                board.block[(wx, wy)]["right"]        = False
                board.block[(wx, wy + 1)]["right"]    = False