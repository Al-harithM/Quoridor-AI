class Player:
    def __init__(self, player_id):
        self.id = player_id
        self.walls_remaining = 10

    def use_wall(self):
        if self.walls_remaining > 0:
            self.walls_remaining -= 1
