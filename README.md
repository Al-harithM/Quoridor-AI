🧱 Quoridor AI Engine & GUI

A complete Python implementation of the classic abstract strategy game Quoridor, featuring a custom-built, highly optimized artificial intelligence engine and a sleek, multithreaded Tkinter graphical interface.

📋 Table of Contents

About the Project

Game Rules

Features

The AI Engine (Under the Hood)

Architecture & Technologies

Installation & Execution

Project Structure

🎯 About the Project

This project transforms a standard Quoridor board game into a modern digital experience. It features a responsive, context-aware GUI that allows players to click seamlessly between cells (to move) and gaps (to place walls).

The centerpiece of the project is the custom AI Engine, which utilizes advanced game-tree search algorithms, time-bound iterative deepening, and dynamic memory caching to deliver a deeply challenging opponent that runs in a background thread to maintain flawless UI performance.

📜 Game Rules

Quoridor is a game of maze-building and racing.

Objective: Be the first player to reach any square on the opposite side of the board from where you started.

Movement: On your turn, you may either move your pawn OR place a wall. Pawns move one square orthogonally (up, down, left, right). If you are adjacent to your opponent, you can jump over them.

Wall Placement: You start with 10 walls. Walls block movement and must span exactly two squares.

The Golden Rule: You CANNOT completely box in a player; there must always be at least one valid, open path to their goal.

✨ Features

Three Difficulty Levels: Easy (Randomized Greedy), Medium (Depth-limited search), and Hard (Time-bound deep search).

Context-Aware Input: No clunky mode-switching buttons. Hover over a tile to preview a move, or hover between tiles to preview wall placements.

Visual Inventory: Real-time tracking of remaining walls color-coded to each player.

Undo/Redo System: Full state-saving allows you to step backward and forward through the game history.

Multithreaded Processing: The Tkinter UI remains completely responsive with animated loading indicators while the AI performs millions of calculations in the background.

🧠 The AI Engine (Under the Hood)

The AI opponent (QuoridorAI) is designed to mimic advanced human strategy, utilizing several core algorithms to calculate its moves efficiently.

Core Algorithms
Minimax with Alpha-Beta Pruning: The backbone of the decision-making process. The AI simulates thousands of possible future board states, assuming the opponent will play perfectly, and trims mathematical branches that are proven to be suboptimal, drastically reducing calculation time.

Iterative Deepening: Instead of searching to a fixed depth, the Hard mode AI utilizes a time limit (e.g., 2.5 seconds). It searches Depth 1, then Depth 2, then Depth 3, going as deep as possible until the clock runs out. This ensures it doesn't waste time in the early game and can search incredibly deep in the endgame.

Transposition Tables (State Caching): Quoridor has a massive branching factor. To prevent recalculating the exact same board state reached via a different move order, the AI creates a deterministic hash of the board and stores the result in memory, retrieving it in O(1) time.

Breadth-First Search (BFS): Used continuously to validate that walls do not break "The Golden Rule" and to calculate the shortest mathematical path to the target rows for both players.

Strategic Heuristics (Evaluation Function)
When the AI reaches the end of its search depth, it scores the board using a custom heuristic function:

Path Lead & Absolute Distance: The AI prioritizes maintaining a shorter mathematical path to the goal than the opponent, while heavily penalizing itself for moving backward.

Endgame Urgency: As pawns enter the final 3 rows, the AI aggressively shifts its weighting to prioritize racing over wall-building.

Anti-Oscillation (Horizon Effect Prevention): The AI tracks a 4-ply history of its own positions. If it detects it is stepping back onto a previously visited square (looping), it applies a massive point penalty, forcing it to commit to a forward path.

Flanking & Self-Help Walls: The move generator doesn't just look at blocking the opponent; it proactively analyzes parallel threats and places "flanking" walls to protect its own optimal corridor.

Smart Move Ordering: To maximize Alpha-Beta cutoffs, wall placements are pre-scored and sorted by how much they disrupt the opponent's path, ensuring the AI searches the most devastating moves first.

🛠️ Architecture & Technologies

Language: Python 3.x

GUI Framework: Tkinter (Standard GUI library)

Concurrency: threading (Daemon threads for AI non-blocking execution)

Data Structures: collections.deque (Queue optimization), frozenset (State hashing)
