import tkinter as tk
from tkinter import messagebox
import threading
from utils.constants import *
from core.game import Game
from core.ai_agent import QuoridorAI
from core.move_validator import MoveValidator

class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command, width=100, height=35, radius=15, bg_color="#3B82F6", hover_color="#2563EB", text_color="white", **kwargs):
        super().__init__(parent, width=width, height=height, bg=parent["bg"], highlightthickness=0, **kwargs)
        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color
        
        points = [
            radius, 0, width-radius, 0, width, 0, width, radius, 
            width, height-radius, width, height, width-radius, height, radius, height, 
            0, height, 0, height-radius, 0, radius, 0, 0
        ]
        self.rect = self.create_polygon(points, fill=bg_color, smooth=True)
        self.create_text(width/2, height/2, text=text, fill=text_color, font=("Arial", 10, "bold"))
        
        self.bind("<Button-1>", lambda e: self.command())
        self.bind("<Enter>", lambda e: self.itemconfig(self.rect, fill=self.hover_color))
        self.bind("<Leave>", lambda e: self.itemconfig(self.rect, fill=self.bg_color))

class QuoridorGUI:
    def __init__(self):
        self.game = Game()
        self.window = tk.Tk()
        self.window.title("Quoridor Game")
        self.window.config(bg="#F4F6F9")

        # Game State
        self.is_ai_mode = False 
        self.is_game_over = False
        self.is_ai_thinking = False
        self.mode = "move"
        self.wall_orientation = None
        
        # AI Setup
        self.ai = QuoridorAI(player_id=2, difficulty="medium")
        self.ai_timer = None

        self.board_width = BOARD_SIZE * CELL_SIZE
        self.offset_x = 20 
        self.offset_y = 50 

        # --- Main Split Layout ---
        self.main_container = tk.Frame(self.window, bg="#F4F6F9")
        self.main_container.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # LEFT COLUMN: Canvas for the Board
        canvas_width = self.board_width + 40 
        canvas_height = self.board_width + 100 # Increased height for wall inventories
        self.canvas = tk.Canvas(
            self.main_container,
            width=canvas_width,
            height=canvas_height,
            bg="#F4F6F9",
            highlightthickness=0
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        # RIGHT COLUMN: UI Dashboard Panel
        self.ui_frame = tk.Frame(self.main_container, bg="#F4F6F9")
        self.ui_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=20, pady=20)

        self.badge_label = tk.Label(self.ui_frame, text="Mode: Player vs Player", font=("Arial", 10, "bold"), bg="#D1FAE5", fg="#065F46", padx=15, pady=5)
        self.badge_label.pack(pady=(0, 30))

        self.turn_label = tk.Label(self.ui_frame, text="", font=("Arial", 14, "bold"), bg="#F4F6F9", width=22)
        
        self.turn_label.pack(pady=10)
        
        self.button_frame = tk.Frame(self.ui_frame, bg="#F4F6F9")
        self.button_frame.pack(pady=20)
        self.create_buttons()

        # Bindings
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Motion>", self.on_hover)
        self.canvas.bind("<Configure>", self.on_resize)
        
        # Initial Draw
        self.draw_board()
        self.update_turn_indicator()
        
        
    def run(self):
        self.window.mainloop()

    # ---------------------------------------------------
    # GAME CONTROL & RESET
    # ---------------------------------------------------
    def start_new_game(self, ai_mode, difficulty="medium"):
        self.is_ai_mode = ai_mode
        
        # Update badge colors dynamically
        if ai_mode:
            self.ai = QuoridorAI(player_id=2, difficulty=difficulty)
            self.badge_label.config(text=f"Mode: Player vs AI ({difficulty.capitalize()})", bg="#DBEAFE", fg="#1E40AF")
            self.window.title(f"Quoridor Game (vs AI - {difficulty.capitalize()})")
        else:
            self.badge_label.config(text="Mode: Player vs Player", bg="#D1FAE5", fg="#065F46")
            self.window.title("Quoridor Game (vs Player)")
            
        self.reset_ui()

    def reset_ui(self):
        # 1. Stop AI Timer
        if self.ai_timer:
            self.window.after_cancel(self.ai_timer)
            self.ai_timer = None

        # 2. Reset Logic
        self.game.reset_game()
        self.is_game_over = False
        
        # 3. Reset View
        self.canvas.delete("all")
        self.draw_board()
        self.update_turn_indicator()
        print("Game has been reset.")

    def check_win(self, y):
        current = self.game.current_player
        winner = None

        if current == 1 and y == 0:
            winner = 1
        elif current == 2 and y == BOARD_SIZE - 1:
            winner = 2

        if winner:
            self.is_game_over = True
            self.canvas.delete("ghost")
            messagebox.showinfo("Game Over", f"Congratulations! Player {winner} Wins!")
            self.reset_ui()
            return True
        return False


    def get_intent(self, x, y):
        """Calculates if the user is pointing at a cell (Move) or a gap (Wall)"""
        adj_x = x - self.offset_x
        adj_y = y - self.offset_y

        # Out of bounds check
        if adj_x < 0 or adj_y < 0 or adj_x >= self.board_width or adj_y >= self.board_width:
            return None, None

        gx = int(adj_x // CELL_SIZE)
        gy = int(adj_y // CELL_SIZE)
        rx = adj_x % CELL_SIZE
        ry = adj_y % CELL_SIZE
        
        margin = CELL_GAP
        in_x_gap = rx < margin or rx > CELL_SIZE - margin
        in_y_gap = ry < margin or ry > CELL_SIZE - margin

        # If hovering over the 4-way corner intersection, ignore to prevent accidental misclicks
        if in_x_gap and in_y_gap: 
            return None, None

        # Vertical Walls (clicked in a vertical gap)
        if rx > CELL_SIZE - margin: return "V", (gx, gy)
        if rx < margin: return "V", (gx - 1, gy)
        
        # Horizontal Walls (clicked in a horizontal gap)
        if ry > CELL_SIZE - margin: return "H", (gx, gy)
        if ry < margin: return "H", (gx, gy - 1)
        
        # Clicked the body of the cell
        return "move", (gx, gy)
    
    def on_click(self, event):
        if self.is_game_over: return
        if self.is_ai_mode and self.game.current_player == 2: return 

        intent, pos = self.get_intent(event.x, event.y)
        if not intent: return
        
        gx, gy = pos

        if intent == "move":
            self.try_move_pawn(gx, gy)
        elif intent in ["H", "V"]:
            # Prevent attempting to place walls outside the placement grid
            if 0 <= gx < BOARD_SIZE - 1 and 0 <= gy < BOARD_SIZE - 1:
                self.try_place_wall(gx, gy, intent)

        self.draw_board()
        self.update_turn_indicator()
        
        if self.is_ai_mode and self.game.current_player == 2 and not self.is_game_over:
            self.run_ai_turn()

    def on_hover(self, event):
        if self.is_game_over: return

        if self.is_ai_mode and self.game.current_player == 2:
            self.canvas.delete("ghost") 
            return
        
        self.canvas.delete("ghost")
        
        intent, pos = self.get_intent(event.x, event.y)
        if not intent: return
        
        gx, gy = pos

        if intent in ["H", "V"]:
            if not (0 <= gx < BOARD_SIZE - 1 and 0 <= gy < BOARD_SIZE - 1): return
            
            if self.game.board.can_place_wall(gx, gy, intent):
                color = "#90EE90" # Green
            else:
                color = "#FFCCCB" # Red
            self._draw_wall_graphic(gx, gy, intent, color, tag="ghost")

        elif intent == "move":
            if MoveValidator.is_valid_move(self.game.board, self.game.current_player, gx, gy):
                color = "#ADD8E6" if self.game.current_player == 1 else "#F08080"
                self._draw_pawn((gx, gy), color, tag="ghost")


    def try_move_pawn(self, gx, gy):
        if MoveValidator.is_valid_move(self.game.board, self.game.current_player, gx, gy):
            self.game.save_state()
            
            self.game.board.pawns[self.game.current_player] = (gx, gy)
            self.canvas.delete("ghost")
            self.draw_board() 
            
            if self.check_win(gy): return

            self.game.switch_turn()
            self.update_turn_indicator()

    def try_place_wall(self, gx, gy, orientation):
        player = self.game.players[self.game.current_player]

        if player.walls_remaining == 0:
            messagebox.showwarning("Warning", "No walls left!")
            return

        self.game.save_state()
        result = self.game.place_wall(gx, gy, orientation)

        if result == True:
            player.use_wall()
            self.game.switch_turn()
        else:
            self.game.history.pop() 
            if result == "overlap":
                messagebox.showerror("Invalid Move", "Wall already exists or overlaps!")
            elif result == "path":
                messagebox.showerror("Invalid Move", "Invalid Wall: Blocks path!")

    def undo_move(self):
        if self.is_ai_mode:
            if len(self.game.history) >= 2:
                self.game.undo()
                self.game.undo()
                self.draw_board()
                self.update_turn_indicator()
        else:
            if self.game.undo():
                self.draw_board()
                self.update_turn_indicator()

    def redo_move(self):
        if self.is_ai_mode:
            if len(self.game.redo_stack) >= 2:
                self.game.redo()
                self.game.redo()
                self.draw_board()
                self.update_turn_indicator()
        else:
            if self.game.redo():
                self.draw_board()
                self.update_turn_indicator()


    def run_ai_turn(self):
        if self.is_game_over: return
        
        self.game.save_state()
        
        # Start the loading animation
        self.is_ai_thinking = True
        self._animate_loading(step=0)
        
        # Spawn the background thread
        threading.Thread(target=self._ai_worker, daemon=True).start()

    def _animate_loading(self, step):
        """Recursively updates the label with animated dots until the AI finishes."""
        if not self.is_ai_thinking:
            return # Stop animating when the flag is flipped
        
        # Cycle through 0, 1, 2, 3 dots
        dots = "." * (step % 4)
        self.turn_label.config(text=f"Turn: AI is thinking{dots}", fg="#1E40AF")
        
        # Schedule the next frame of the animation in 400ms
        self.window.after(400, lambda: self._animate_loading(step + 1))

    def _ai_worker(self):
        """Runs in the background, preventing GUI freezes."""
        best_move = self.ai.get_best_move(self.game)
        
        if best_move:
            move_type, data = best_move
            self.window.after(0, lambda: self._apply_ai_move(move_type, data))
        else:
            print("Warning: AI returned None. It might be trapped.")
            # Safely stop the animation even on failure
            self.window.after(0, self._stop_ai_animation)

    def _stop_ai_animation(self):
        """Helper to stop animation if AI fails."""
        self.is_ai_thinking = False
        self.update_turn_indicator()

    def _apply_ai_move(self, move_type, data):
        """Runs on the main Tkinter thread to safely update the board."""
        if self.is_game_over: return

        # AI finished, turn off the animation flag
        self.is_ai_thinking = False 

        if move_type == "move":
            gx, gy = data
            self.game.board.pawns[2] = (gx, gy)
            
            self.draw_board()
            self.window.update_idletasks() 
            
            if self.check_win(gy): return

        elif move_type == "wall":
            wx, wy, orientation = data
            success = self.game.place_wall(wx, wy, orientation)
            if success == True:
                self.game.players[2].use_wall()
            else:
                print(f"AI attempted invalid wall at {wx}, {wy}. Wall not deducted.")

        self.game.switch_turn()
        self.draw_board()
        self.update_turn_indicator()

    # ---------------------------------------------------
    # RENDERING
    # ---------------------------------------------------
    def show_rules(self):
        """Displays a clean, custom popup window with the game rules."""
        rules_window = tk.Toplevel(self.window)
        rules_window.title("How to Play Quoridor")
        # rules_window.geometry("450x400")
        rules_window.config(bg="#F4F6F9")
        
        # Make the popup modal (locks the main window until the popup is closed)
        rules_window.transient(self.window)
        rules_window.grab_set()

        title = tk.Label(rules_window, text="Quoridor Rules", font=("Arial", 16, "bold"), bg="#F4F6F9", fg="#1E293B")
        title.pack(pady=(20, 10))

        rules_text = (
            "\U0001f3af Objective:\n"
            "Be the first player to reach any square on the opposite side of the board.\n\n"
            "\U0001f6b6 Movement:\n"
            "- On each turn, a player must either move their pawn or place a wall. \n"
            "- Pawns move one square orthogonally (up, down, left, right). \n"
            "- Players cannot move through walls or opponent pawns. \n"
            "- If a player's pawn is adjacent to an opponent's pawn, the player can jump over "
            "the opponent's pawn (if there's no wall blocking). \n"
            "- If a jump is blocked by a wall, the player can move diagonally around the "
            "opponent's pawn.\n\n"
            # "On your turn, you may either move your pawn OR place a wall. "
            # "Pawns move one square orthogonally (up, down, left, right). "
            # "If you are adjacent to your opponent, you can jump over them!\n\n"
            "\U0001f9f1 Wall Placement:\n"
            "Click in the gaps between squares to place a wall. You have 10 walls. "
            "Walls block movement and must span exactly two squares. "
            "Rule: You CANNOT completely box in a player; there must always be at least one open path to their goal."
        )

        # Message widget automatically handles text wrapping
        msg = tk.Message(rules_window, text=rules_text, font=("Arial", 11), bg="#F4F6F9", fg="#334155", width=400, justify="left")
        msg.pack(padx=20, pady=5)

        # A sleek button to close the popup
        close_btn = tk.Button(
            rules_window, text="Got it!", command=rules_window.destroy, 
            font=("Arial", 10, "bold"), bg="#3B82F6", fg="white", 
            activebackground="#2563EB", activeforeground="white", relief="flat", padx=20, pady=8
        )
        close_btn.pack(pady=20)
        
    def create_buttons(self):
        btn_width = 140
        
        menu_btn = tk.Menubutton(
            self.button_frame, text="New Game ▾", font=("Arial", 10, "bold"), 
            bg="#E2E8F0", fg="#1E293B", activebackground="#CBD5E1", relief="flat", padx=10, pady=5
        )
        menu_btn.pack(pady=10) 
        
        self.game_menu = tk.Menu(menu_btn, tearoff=0)
        menu_btn.config(menu=self.game_menu)
        self.game_menu.add_command(label="Player vs Player", command=lambda: self.start_new_game(ai_mode=False))
        self.game_menu.add_separator()
        self.game_menu.add_command(label="vs AI (Easy)", command=lambda: self.start_new_game(ai_mode=True, difficulty="easy"))
        self.game_menu.add_command(label="vs AI (Medium)", command=lambda: self.start_new_game(ai_mode=True, difficulty="medium"))
        self.game_menu.add_command(label="vs AI (Hard)", command=lambda: self.start_new_game(ai_mode=True, difficulty="hard"))

        RoundedButton(self.button_frame, text="Undo", command=self.undo_move, bg_color="#64748B", hover_color="#475569", width=btn_width).pack(pady=5)
        RoundedButton(self.button_frame, text="Redo", command=self.redo_move, bg_color="#64748B", hover_color="#475569", width=btn_width).pack(pady=5) 

        RoundedButton(self.button_frame, text="How to Play", command=self.show_rules, bg_color="#10B981", hover_color="#059669", width=btn_width).pack(pady=(300, 5))   


    def draw_board(self):
        self.canvas.delete("all")
        margin = CELL_GAP
        
        # 1. Draw the main board background
        self.canvas.create_rectangle(
            self.offset_x, self.offset_y, 
            self.offset_x + self.board_width, self.offset_y + self.board_width, 
            fill="#FFFFFF", outline="#DEE2E6", width=2
        )
        
        inner = CELL_SIZE - 2 * margin
        
        # 2. Draw the individual grid tiles
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                x1 = self.offset_x + i * CELL_SIZE + margin
                y1 = self.offset_y + j * CELL_SIZE + margin
                x2 = x1 + inner
                y2 = y1 + inner
                
                # Determine tile color
                if j == 8: 
                    tile_color = "#FEE2E2"  # Light Red (Bottom Row)
                elif j == 0: 
                    tile_color = "#DBEAFE"  # Light Blue (Top Row)
                else:
                    tile_color = "#FDFDFD"  # Standard White

                # Draw ONE tile using the determined color
                self.canvas.create_rectangle(x1, y1, x2, y2, outline="#E9ECEF", fill=tile_color)

        # 3. Draw placed walls
        for (x, y, orientation) in self.game.board.walls:
            owner = self.game.board.wall_owners.get((x, y, orientation), 1)
            
            wall_color = "#3B82F6" if owner == 1 else "#EF4444"
            
            self._draw_wall_graphic(x, y, orientation, wall_color)

        # 4. Draw player pawns
        for player, pos in self.game.board.pawns.items():
            color = "#3B82F6" if player == 1 else "#EF4444"
            self._draw_pawn(pos, color)

        # 5. Draw the top and bottom wall inventory
        self._draw_visual_inventory()

        
    def _draw_pawn(self, pos, color, tag=None): 
        x, y = pos
        margin = CELL_GAP * 1.2
        
        # Apply offset to center point
        cx = self.offset_x + x * CELL_SIZE + (CELL_SIZE / 2)
        cy = self.offset_y + y * CELL_SIZE + (CELL_SIZE / 2)
        radius = (CELL_SIZE - margin * 2) / 2
        
        self.canvas.create_oval(
            cx - radius + 2, cy - radius + 2, 
            cx + radius + 2, cy + radius + 2, 
            fill="#CBD5E1", outline="", tags=tag
        )
        
        self.canvas.create_oval(
            cx - radius, cy - radius, 
            cx + radius, cy + radius, 
            fill=color, outline="#1E293B", width=2, tags=tag
        )
        
        inner_r = radius * 0.55
        self.canvas.create_oval(
            cx - inner_r, cy - inner_r, 
            cx + inner_r, cy + inner_r, 
            fill="", outline="white", width=2, tags=tag
        )

    def _draw_wall_graphic(self, x, y, orientation, color, tag=None):
        margin = CELL_GAP
        wall_thickness = CELL_GAP
        
        if orientation == "H":
            y_center = self.offset_y + (y + 1) * CELL_SIZE
            x_start = self.offset_x + x * CELL_SIZE + margin
            x_end = self.offset_x + (x + 2) * CELL_SIZE - margin
            self.canvas.create_rectangle(
                x_start, y_center - wall_thickness // 2,
                x_end, y_center + wall_thickness // 2,
                fill=color, outline="", tags=tag
            )
        else:
            x_center = self.offset_x + (x + 1) * CELL_SIZE
            y_start = self.offset_y + y * CELL_SIZE + margin
            y_end = self.offset_y + (y + 2) * CELL_SIZE - margin
            self.canvas.create_rectangle(
                x_center - wall_thickness // 2, y_start,
                x_center + wall_thickness // 2, y_end,
                fill=color, outline="", tags=tag
            )

    def update_turn_indicator(self):
        player = self.game.current_player
        color = "blue" if player == 1 else "red"
        self.turn_label.config(text=f"Turn: Player {player}", fg=color)

    
    def _draw_visual_inventory(self):
        p2_walls = self.game.players[2].walls_remaining
        p2_start = self.offset_x + (self.board_width - (p2_walls * 35)) // 2
        for i in range(p2_walls):
            x = p2_start + i * 35
            y = self.offset_y - 25
            self.canvas.create_rectangle(x, y, x + 25, y + 8, fill="#EF4444", outline="#7F1D1D")

        p1_walls = self.game.players[1].walls_remaining
        p1_start = self.offset_x + (self.board_width - (p1_walls * 35)) // 2
        for i in range(p1_walls):
            x = p1_start + i * 35
            y = self.offset_y + self.board_width + 17
            self.canvas.create_rectangle(x, y, x + 25, y + 8, fill="#3B82F6", outline="#1E3A8A")    
    
    def on_resize(self, event):
        canvas_width = event.width
        canvas_height = event.height
        
        self.offset_x = max(20, (canvas_width - self.board_width) // 2)
        self.offset_y = max(50, (canvas_height - self.board_width) // 2) 
        
        self.draw_board()