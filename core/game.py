import copy
from core.board import Board
from core.player import Player

class Game:
    def __init__(self):
        self.board = Board()
        self.players = {
            1: Player(1),
            2: Player(2)
        }
        self.current_player = 1
        self.history = []     # Past states
        self.redo_stack = []  # Future states (for Redo)

    def reset_game(self):
        self.board.reset()  # Clears board walls and pawn positions
        self.players[1].walls_remaining = 10
        self.players[2].walls_remaining = 10
        self.current_player = 1
        self.history = []     # Clear history
        self.redo_stack = []  # Clear redo stack

    def switch_turn(self):
        self.current_player = 2 if self.current_player == 1 else 1

    def save_state(self):
        # 1. Clear Redo Stack (New move kills the future)
        self.redo_stack = [] 
        
        # 2. Save current state to history
        snapshot = (
            copy.deepcopy(self.board), 
            copy.deepcopy(self.players), 
            self.current_player
        )
        self.history.append(snapshot)

    def undo(self):
        if not self.history:
            return False 

        # 1. Save CURRENT state to Redo Stack before we lose it
        current_state = (
            copy.deepcopy(self.board), 
            copy.deepcopy(self.players), 
            self.current_player
        )
        self.redo_stack.append(current_state)

        # 2. Restore the previous state
        previous_state = self.history.pop()
        self.board, self.players, self.current_player = previous_state
        return True

    def redo(self):
        if not self.redo_stack:
            return False

        # 1. Save CURRENT state to History (so we can Undo again later)
        current_state = (
            copy.deepcopy(self.board), 
            copy.deepcopy(self.players), 
            self.current_player
        )
        self.history.append(current_state)

        # 2. Restore the future state
        next_state = self.redo_stack.pop()
        self.board, self.players, self.current_player = next_state
        return True

    def place_wall(self, x, y, orientation):
        # 1. Geometric Validation
        if not self.board.can_place_wall(x, y, orientation):
            return "overlap"

        # 2. TEMPORARY PLACEMENT
        self.board.walls.append((x, y, orientation))
        self.board.wall_owners[(x, y, orientation)] = self.current_player
        if orientation == "H":
            self.board.add_horizontal_wall(x, y)
        else:
            self.board.add_vertical_wall(x, y)

        # 3. PATHFINDING CHECK
        if self.board.has_path(1) and self.board.has_path(2):
            return True  # Success!
        
        # 4. ROLLBACK (If path is blocked)
        self.board.walls.pop()
        del self.board.wall_owners[(x, y, orientation)]
        if orientation == "H":
            self._remove_horizontal_wall(x, y)
        else:
            self._remove_vertical_wall(x, y)
            
        return "path"

    def _remove_horizontal_wall(self, board_x, board_y):
        self.board.block[(board_x, board_y)]["down"] = False
        self.board.block[(board_x + 1, board_y)]["down"] = False
        self.board.block[(board_x, board_y + 1)]["up"] = False
        self.board.block[(board_x + 1, board_y + 1)]["up"] = False

    def _remove_vertical_wall(self, board_x, board_y):
        self.board.block[(board_x + 1, board_y)]["left"] = False
        self.board.block[(board_x + 1, board_y + 1)]["left"] = False
        self.board.block[(board_x, board_y)]["right"] = False
        self.board.block[(board_x, board_y + 1)]["right"] = False