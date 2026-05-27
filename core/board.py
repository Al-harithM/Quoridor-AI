from collections import deque

class Board:
    def __init__(self, size=9):
        self.size = size
        self.reset()

    def reset(self):
        self.pawns = {
            1: (4, 8),
            2: (4, 0)
        }
        self.walls = []
        self.wall_owners = {}
        self.block = {
            (x, y): {"up": False, "down": False, "left": False, "right": False}
            for x in range(self.size)
            for y in range(self.size)
        }

    def is_inside(self, pos):
        x, y = pos
        return 0 <= x < self.size and 0 <= y < self.size

    def add_wall(self, x, y, orientation):
        self.walls.append((x, y, orientation))
        
    def wall_exists(self, x, y, orientation):
        return (x, y, orientation) in self.walls

    def add_horizontal_wall(self, x, y):
        self.block[(x, y)]["down"] = True
        self.block[(x + 1, y)]["down"] = True
        self.block[(x, y + 1)]["up"] = True
        self.block[(x + 1, y + 1)]["up"] = True

    def add_vertical_wall(self, x, y):
        self.block[(x+1, y)]["left"] = True
        self.block[(x+1, y+1)]["left"] = True
        self.block[(x, y)]["right"] = True
        self.block[(x, y+1)]["right"] = True

    def can_place_wall(self, x, y, orientation):
        if not (0 <= x < self.size - 1 and 0 <= y < self.size - 1):
            return False

        # Check overlapping with existing walls
        if orientation == "H":
            if (x, y, "V") in self.walls: return False
            if (x, y, "H") in self.walls: return False
            if (x - 1, y, "H") in self.walls: return False
            if (x + 1, y, "H") in self.walls: return False
        elif orientation == "V":
            if (x, y, "H") in self.walls: return False
            if (x, y, "V") in self.walls: return False
            if (x, y - 1, "V") in self.walls: return False
            if (x, y + 1, "V") in self.walls: return False

        return True

    def has_path(self, player_id):
        # Wrapper for backward compatibility, checks if distance is not infinity
        return self.get_shortest_path_distance(player_id) != float('inf')

    def get_shortest_path_distance(self, player_id):
        """BFS that returns the integer distance to the goal row."""
        start_pos = self.pawns[player_id]
        target_row = 0 if player_id == 1 else 8

        queue = deque([(start_pos, 0)])
        visited = {start_pos}

        while queue:
            (cx, cy), dist = queue.popleft()

            if cy == target_row:
                return dist

            # Check neighbors respecting walls
            # 1. DOWN
            if cy + 1 < self.size and not self.block[(cx, cy)]["down"]:
                if (cx, cy + 1) not in visited:
                    visited.add((cx, cy + 1))
                    queue.append(((cx, cy + 1), dist + 1))
            # 2. UP
            if cy - 1 >= 0 and not self.block[(cx, cy)]["up"]:
                if (cx, cy - 1) not in visited:
                    visited.add((cx, cy - 1))
                    queue.append(((cx, cy - 1), dist + 1))
            # 3. RIGHT
            if cx + 1 < self.size and not self.block[(cx, cy)]["right"]:
                if (cx + 1, cy) not in visited:
                    visited.add((cx + 1, cy))
                    queue.append(((cx + 1, cy), dist + 1))
            # 4. LEFT
            if cx - 1 >= 0 and not self.block[(cx, cy)]["left"]:
                if (cx - 1, cy) not in visited:
                    visited.add((cx - 1, cy))
                    queue.append(((cx - 1, cy), dist + 1))

        return float('inf')