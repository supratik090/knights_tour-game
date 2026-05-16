import tkinter as tk
from tkinter import ttk
from typing import List, Optional, Tuple

from .constants import (
    ANALYZE_ACTIVE_BG,
    ANALYZE_BG,
    APP_BG,
    BADGE_RING,
    BADGE_TEXT_DARK,
    BOARD_SURFACE_BG,
    BOARD_OPTIONS,
    CONTROL_ACTIVE_BG,
    CONTROL_BG,
    CURRENT_TILE,
    DARK_TILE,
    HIGHLIGHT_TILE,
    LIGHT_TILE,
    MUTED_FG,
    PANEL_BG,
    START_TILE,
    STATE_READY_AMBER_BG,
    STATE_BLOCKED_BG,
    STATE_FINISHABLE_BG,
    SUGGEST_ACTIVE_BG,
    SUGGEST_BG,
    TEXT_FG,
    TITLE_FG,
    VISITED_TILE,
)
from .game import GameState
from .solver import Position, board_has_any_full_tour


class KnightsTourApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Knight's Tour")
        self.root.configure(bg=APP_BG)
        self.root.resizable(False, False)

        self.game = GameState(board_size=5)
        self.board_size_var = tk.StringVar(value=str(self.game.board_size))
        self.status_var = tk.StringVar(
            value="Choose a board size, then click any square to start."
        )

        self.buttons: List[List[tk.Label]] = []
        self.replay_after_id: Optional[str] = None
        self.replay_index = 0
        self.replay_moves: List[Position] = []
        self.replay_running = False
        self.auto_after_id: Optional[str] = None
        self.auto_moves: List[Position] = []
        self.auto_index = 0
        self.auto_running = False

        self._build_layout()
        self.create_board()

    def _build_layout(self) -> None:
        outer = tk.Frame(self.root, bg=APP_BG, padx=18, pady=18)
        outer.pack()

        header = tk.Frame(outer, bg=APP_BG)
        header.pack(fill="x", pady=(0, 12))

        title_group = tk.Frame(header, bg=APP_BG)
        title_group.pack(side="left", anchor="w")

        title = tk.Label(
            title_group,
            text="Knight's Tour",
            font=("Avenir Next", 28, "bold"),
            fg=TITLE_FG,
            bg=APP_BG,
        )
        title.pack(side="left")

        self.state_badge = tk.Canvas(
            title_group,
            bd=0,
            highlightthickness=0,
            width=130,
            height=42,
            bg=APP_BG,
        )
        self.state_badge.pack(side="left", padx=(14, 0))
        self.state_badge_bg = self.state_badge.create_oval(
            2, 2, 128, 40, fill=STATE_READY_AMBER_BG, outline=""
        )
        self.state_badge_dot = self.state_badge.create_oval(
            12, 11, 28, 27, fill=BADGE_RING, outline=""
        )
        self.state_badge_text = self.state_badge.create_text(
            76,
            21,
            text="Ready",
            fill=BADGE_TEXT_DARK,
            font=("Avenir Next", 10, "bold"),
        )

        board_picker = tk.Frame(header, bg=APP_BG)
        board_picker.pack(side="right", anchor="ne")

        size_label = tk.Label(
            board_picker,
            text="Board:",
            font=("Avenir Next", 11, "bold"),
            fg=TEXT_FG,
            bg=APP_BG,
        )
        size_label.grid(row=0, column=0, padx=(0, 8))

        combo_style = ttk.Style()
        combo_style.theme_use(combo_style.theme_use())
        combo_style.configure(
            "KnightTour.TCombobox",
            fieldbackground=PANEL_BG,
            background=PANEL_BG,
            foreground=TITLE_FG,
            arrowcolor=TITLE_FG,
            borderwidth=0,
            relief="flat",
        )
        combo_style.map(
            "KnightTour.TCombobox",
            fieldbackground=[("readonly", PANEL_BG)],
            background=[("readonly", PANEL_BG)],
            foreground=[("readonly", TITLE_FG)],
        )
        size_menu = ttk.Combobox(
            board_picker,
            textvariable=self.board_size_var,
            values=[str(option) for option in BOARD_OPTIONS],
            width=8,
            font=("Avenir Next", 11),
            state="readonly",
            style="KnightTour.TCombobox",
        )
        size_menu.bind("<<ComboboxSelected>>", lambda _event: self.on_board_size_change())
        size_menu.grid(row=0, column=1, sticky="e")

        subtitle = tk.Label(
            outer,
            text="Start anywhere and try to complete a full knight's tour.",
            font=("Avenir Next", 12),
            fg=MUTED_FG,
            bg=APP_BG,
        )
        subtitle.pack(anchor="w", pady=(0, 12))

        content = tk.Frame(outer, bg=APP_BG)
        content.pack()

        toolbar = tk.Frame(content, bg=PANEL_BG, padx=10, pady=10)
        toolbar.grid(row=0, column=0, sticky="ns", padx=(0, 14))

        button_specs = [
            ("\u27f2", self.undo_move),
            ("\u27f3", self.redo_move),
            ("Suggest", self.suggest_next_move),
            ("Analyze", self.analyze_position),
            ("Auto Finish", self.auto_finish),
            ("Replay", self.start_replay),
            ("New Game", self.restart_game),
        ]

        for index, (label, command) in enumerate(button_specs):
            is_analyze = label in {"Analyze", "Auto Finish"}
            is_suggest = label == "Suggest"
            button = tk.Button(
                toolbar,
                text=label,
                command=command,
                width=12 if len(label) > 2 else 4,
                font=("Avenir Next", 14, "bold") if len(label) <= 2 else ("Avenir Next", 10, "bold"),
                bg=SUGGEST_BG if is_suggest else ANALYZE_BG if is_analyze else CONTROL_BG,
                fg="#1f2937",
                activebackground=(
                    SUGGEST_ACTIVE_BG
                    if is_suggest
                    else ANALYZE_ACTIVE_BG
                    if is_analyze
                    else CONTROL_ACTIVE_BG
                ),
                activeforeground="#111827",
                relief="flat",
                bd=0,
                padx=10,
                pady=8,
            )
            button.grid(row=index, column=0, pady=5, sticky="ew")
            self._bind_hover(
                button,
                SUGGEST_ACTIVE_BG if is_suggest else ANALYZE_ACTIVE_BG if is_analyze else CONTROL_ACTIVE_BG,
                SUGGEST_BG if is_suggest else ANALYZE_BG if is_analyze else CONTROL_BG,
            )

        self.board_frame = tk.Frame(
            content,
            bg=BOARD_SURFACE_BG,
            padx=14,
            pady=14,
            highlightbackground="#2f5366",
            highlightthickness=2,
        )
        self.board_frame.grid(row=0, column=1, sticky="nsew")

        status_card = tk.Frame(
            outer,
            bg=PANEL_BG,
            padx=14,
            pady=12,
            highlightbackground="#2b4c5d",
            highlightthickness=1,
        )
        status_card.pack(fill="x", pady=(12, 0))

        self.status_label = tk.Label(
            status_card,
            textvariable=self.status_var,
            font=("Avenir Next", 11),
            fg=TITLE_FG,
            bg=PANEL_BG,
            wraplength=780,
            justify="left",
            anchor="w",
        )
        self.status_label.pack(fill="x")

    def on_board_size_change(self) -> None:
        self.restart_game()

    def create_board(self) -> None:
        for widget in self.board_frame.winfo_children():
            widget.destroy()

        self.buttons = []
        size = int(self.board_size_var.get())
        cell_width, cell_height, cell_font = self._board_cell_style(size)

        for row in range(size):
            button_row = []
            for col in range(size):
                button = tk.Label(
                    self.board_frame,
                    width=cell_width,
                    height=cell_height,
                    font=("Avenir Next", cell_font, "bold"),
                    relief="solid",
                    bd=2,
                    cursor="hand2",
                    justify="center",
                )
                button.bind(
                    "<Button-1>",
                    lambda event, r=row, c=col: self.handle_square_click(r, c),
                )
                button.grid(row=row, column=col, padx=1, pady=1)
                button_row.append(button)
            self.buttons.append(button_row)

        self.game.reset(board_size=size)
        self.set_status("Choose a board size, then click any square to start.")
        self.update_state_button()
        self.refresh_board()

    def restart_game(self) -> None:
        self.cancel_animations(update_status=False)
        self.create_board()

    def handle_square_click(self, row: int, col: int) -> None:
        if self.replay_running or self.auto_running:
            self.set_status(
                "Animation is running. Start a new game or change the board size to stop it."
            )
            return

        move = (row, col)
        if not self.game.can_move_to(move):
            self.set_status("Pick one of the highlighted knight moves.")
            return

        self.game.apply_move(move, clear_redo=True)
        self.update_game_state()

    def update_game_state(self) -> None:
        self.game.assess_solvability()
        self.update_state_button()
        self.refresh_board()

        if self.game.is_complete():
            self.set_status(
                f"Excellent work. You completed the {self.game.board_size}x{self.game.board_size} Knight's Tour."
            )
            return

        if not self.game.moves:
            if not board_has_any_full_tour(self.game.board_size):
                self.set_status(
                    "A full Knight's Tour is not possible on a 4x4 board. You can still explore moves, or switch to 5x5 or larger for a completable game."
                )
            else:
                self.set_status("Choose a board size, then click any square to start.")
            return

        valid_moves = self.game.valid_moves()
        current = self.game.current_move
        if valid_moves and current:
            if self.game.solvable is False:
                if not board_has_any_full_tour(self.game.board_size):
                    self.set_status(
                        f"Move {len(self.game.moves)}/{self.game.total_tiles}. "
                        f"Knight is at {self.game.format_position(current)}. "
                        "A full Knight's Tour does not exist on 4x4."
                    )
                else:
                    self.set_status(
                        f"Move {len(self.game.moves)}/{self.game.total_tiles}. "
                        f"Knight is at {self.game.format_position(current)}. "
                        "This path is blocked from completing the full tour."
                    )
                return
            self.set_status(
                f"Move {len(self.game.moves)}/{self.game.total_tiles}. "
                f"Knight is at {self.game.format_position(current)}. "
                "Choose one of the highlighted squares."
            )
            return

        if current:
            if not board_has_any_full_tour(self.game.board_size):
                self.set_status(
                    f"No more valid knight moves from {self.game.format_position(current)}. "
                    "A full Knight's Tour is impossible on 4x4, so try 5x5 or larger for a solvable board."
                )
            else:
                self.set_status(
                    f"No more valid knight moves from {self.game.format_position(current)}. "
                    "Use undo, replay, or start a new game."
                )

    def undo_move(self) -> None:
        if self.replay_running or self.auto_running:
            self.set_status(
                "Start a new game or wait for the animation to finish before undoing moves."
            )
            return

        if self.game.undo() is None:
            self.set_status("There are no moves to undo.")
            return

        self.update_game_state()

    def redo_move(self) -> None:
        if self.replay_running or self.auto_running:
            self.set_status(
                "Start a new game or wait for the animation to finish before redoing moves."
            )
            return

        if not self.game.redo_stack:
            self.set_status("There are no moves to redo.")
            return

        if self.game.redo() is None:
            self.set_status("Redo is no longer valid after the current move path changed.")
            return

        self.update_game_state()

    def suggest_next_move(self) -> None:
        if self.replay_running or self.auto_running:
            self.set_status(
                "Wait for the current animation to finish, or start a new game before asking for a suggestion."
            )
            return

        if not self.game.moves:
            self.set_status("Choose a starting square first, then ask for a suggestion.")
            return

        self.set_status("Finding the best next move that still allows a full tour...")
        self.root.update_idletasks()

        suggestion = self.game.suggest()
        self.refresh_board()
        self.update_state_button()

        if suggestion:
            self.set_status(
                f"Suggested next move: {self.game.format_position(suggestion)}. "
                "This move keeps a full tour possible."
            )
            return

        self.set_status("No suggested next move can finish the tour from this board state.")

    def analyze_position(self) -> None:
        if self.replay_running or self.auto_running:
            self.set_status(
                "Wait for the current animation to finish, or start a new game before analyzing."
            )
            return

        self.set_status("Analyzing board. Looking for a full tour from the current position...")
        self.root.update_idletasks()

        solution = self.game.analyze()
        self.refresh_board()
        self.update_state_button()

        if solution is None:
            self.set_status("Choose a starting square first, then analyze the board.")
            return

        if solution:
            preview = ", ".join(
                self.game.format_position(move) for move in solution[:6]
            )
            if len(solution) > 6:
                preview += ", ..."
            self.set_status(
                f"Tour found. {len(solution)} move(s) remain. Suggested path starts: {preview}"
            )
            return

        self.set_status("No full tour was found from the current board state.")

    def auto_finish(self) -> None:
        if self.replay_running or self.auto_running:
            self.set_status(
                "Wait for the current animation to finish, or start a new game before auto finishing."
            )
            return

        if not self.game.moves:
            self.set_status("Choose a starting square first, then use Analyze or Auto Finish.")
            return

        solution = self.game.last_analysis_path or self.game.analyze()
        self.refresh_board()
        self.update_state_button()

        if not solution:
            self.set_status("Auto Finish could not find a full tour from this position.")
            return

        self.auto_moves = list(solution)
        self.auto_index = 0
        self.auto_running = True
        self.set_status("Auto Finish is playing the remaining solution.")
        self.run_auto_step()

    def start_replay(self) -> None:
        if self.replay_running or self.auto_running:
            self.set_status("Another animation is already running.")
            return

        if not self.game.moves:
            self.set_status("Make at least one move before replaying.")
            return

        self.replay_moves = list(self.game.moves)
        self.replay_index = 0
        self.replay_running = True
        self.game.reset(board_size=int(self.board_size_var.get()))
        self.update_state_button()
        self.refresh_board()
        self.set_status("Replaying your tour. Use New Game or change the board size to stop it.")
        self.run_replay_step()

    def run_replay_step(self) -> None:
        if not self.replay_running:
            return

        self.replay_after_id = None
        if self.replay_index >= len(self.replay_moves):
            self.replay_running = False
            self.game.assess_solvability()
            self.update_state_button()
            self.refresh_board()
            self.set_status("Replay finished. You can continue playing, undo, or start a new game.")
            return

        move = self.replay_moves[self.replay_index]
        self.game.apply_move(move, clear_redo=False)
        self.replay_index += 1
        self.game.assess_solvability()
        self.update_state_button()
        self.refresh_board()
        self.replay_after_id = self.root.after(550, self.run_replay_step)

    def run_auto_step(self) -> None:
        if not self.auto_running:
            return

        self.auto_after_id = None
        if self.auto_index >= len(self.auto_moves):
            self.auto_running = False
            self.game.last_analysis_path = []
            self.game.suggested_move = None
            self.game.assess_solvability()
            self.update_state_button()
            self.set_status("Auto Finish completed the tour.")
            return

        move = self.auto_moves[self.auto_index]
        self.game.apply_move(move, clear_redo=False)
        self.auto_index += 1
        if self.auto_index < len(self.auto_moves):
            self.game.suggested_move = self.auto_moves[self.auto_index]
        self.game.assess_solvability()
        self.update_game_state()

        if self.auto_running:
            self.auto_after_id = self.root.after(350, self.run_auto_step)

    def cancel_animations(self, update_status: bool = True) -> None:
        if self.replay_after_id is not None:
            self.root.after_cancel(self.replay_after_id)
            self.replay_after_id = None

        if self.replay_running:
            self.replay_running = False
            self.game.set_replay_snapshot(self.replay_moves[: self.replay_index])
            self.game.assess_solvability()
            self.update_state_button()
            self.refresh_board()
            if update_status:
                self.set_status("Replay canceled. Your progress has been restored.")

        if self.auto_after_id is not None:
            self.root.after_cancel(self.auto_after_id)
            self.auto_after_id = None

        if self.auto_running:
            self.auto_running = False
            self.game.suggested_move = None
            self.game.assess_solvability()
            self.update_state_button()
            self.refresh_board()
            if update_status:
                self.set_status("Auto Finish stopped.")

    def refresh_board(self) -> None:
        valid_moves = set(self.game.valid_moves())
        current_move = self.game.current_move
        start_move = self.game.start_move

        for row in range(self.game.board_size):
            for col in range(self.game.board_size):
                button = self.buttons[row][col]
                position = (row, col)
                base_color = LIGHT_TILE if (row + col) % 2 == 0 else DARK_TILE
                text = ""
                fg = "#111827"

                if position == current_move:
                    bg = CURRENT_TILE
                    fg = "#ffffff"
                    text = str(self.game.moves.index(position) + 1)
                elif position == start_move:
                    bg = START_TILE
                    text = str(self.game.moves.index(position) + 1)
                elif position in valid_moves:
                    bg = HIGHLIGHT_TILE
                    if position == self.game.suggested_move:
                        text = "Hint"
                elif position in self.game.visited:
                    bg = VISITED_TILE
                    text = str(self.game.moves.index(position) + 1)
                else:
                    bg = base_color

                button.configure(bg=bg, fg=fg, text=text)

    def set_status(self, message: str) -> None:
        self.status_var.set(message)

    def update_state_button(self) -> None:
        if not self.game.moves:
            label = "Ready"
            bg = STATE_READY_AMBER_BG
        elif self.game.solvable is False:
            label = "Blocked"
            bg = STATE_BLOCKED_BG
        else:
            label = "Finishable"
            bg = STATE_FINISHABLE_BG

        self.state_badge.itemconfigure(self.state_badge_bg, fill=bg)
        self.state_badge.itemconfigure(self.state_badge_text, text=label)

    def _bind_hover(self, button: tk.Button, hover_bg: str, normal_bg: str) -> None:
        button.bind("<Enter>", lambda _event: button.configure(bg=hover_bg))
        button.bind("<Leave>", lambda _event: button.configure(bg=normal_bg))

    def _board_cell_style(self, size: int) -> Tuple[int, int, int]:
        if size <= 7:
            return (8, 4, 16)
        if size == 8:
            return (6, 3, 14)
        if size == 9:
            return (5, 3, 12)
        return (4, 2, 11)


def main() -> None:
    root = tk.Tk()
    KnightsTourApp(root)
    root.mainloop()
