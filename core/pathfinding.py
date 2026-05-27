from collections import deque

def bfs(board, start, goal_row):
    # Skeleton BFS
    queue = deque([start])
    visited = set([start])

    while queue:
        x, y = queue.popleft()
        
        if y == goal_row:
            return True
        
        # TODO: add movement rules respecting walls

    return False
