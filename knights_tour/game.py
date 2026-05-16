from dataclasses import dataclass, field
from typing import List, Optional, Set, Tuple

from .cache import cache_start_path, get_cached_path_for_moves
from .solver import (
    Position,
    board_has_any_full_tour,
    find_start_tour_fast,
    find_solution_path,
    start_position_can_have_full_tour,
    valid_moves_from,
)


@dataclass
class GameState:
    board_size: int = 5
    moves: List[Position] = field(default_factory=list)
    redo_stack: List[Position] = field(default_factory=list)
    visited: Set[Position] = field(default_factory=set)
    last_analysis_path: List[Position] = field(default_factory=list)
    suggested_move: Optional[Position] = None
    solvable: Optional[bool] = None

    def reset(self, board_size: Optional[int] = None) -> None:
        if board_size is not None:
            self.board_size = board_size
        self.moves = []
        self.redo_stack = []
        self.visited = set()
        self.last_analysis_path = []
        self.suggested_move = None
        self.solvable = None

    @property
    def total_tiles(self) -> int:
        return self.board_size ** 2

    @property
    def current_move(self) -> Optional[Position]:
        return self.moves[-1] if self.moves else None

    @property
    def start_move(self) -> Optional[Position]:
        return self.moves[0] if self.moves else None

    def is_complete(self) -> bool:
        return len(self.moves) == self.total_tiles

    def valid_moves(self) -> List[Position]:
        if not self.current_move:
            return []
        return valid_moves_from(self.current_move, self.board_size, self.visited)

    def can_move_to(self, move: Position) -> bool:
        if not self.moves:
            return True
        return move in set(self.valid_moves())

    def apply_move(self, move: Position, clear_redo: bool = True) -> None:
        if clear_redo:
            self.redo_stack.clear()
        self.moves.append(move)
        self.visited.add(move)
        self.last_analysis_path = []
        self.suggested_move = None
        self.solvable = None

    def undo(self) -> Optional[Position]:
        if not self.moves:
            return None
        last_move = self.moves.pop()
        self.visited.remove(last_move)
        self.redo_stack.append(last_move)
        self.last_analysis_path = []
        self.suggested_move = None
        self.solvable = None
        return last_move

    def redo(self) -> Optional[Position]:
        if not self.redo_stack:
            return None

        next_move = self.redo_stack[-1]
        if self.moves and next_move not in set(self.valid_moves()):
            self.redo_stack.clear()
            return None

        self.redo_stack.pop()
        self.moves.append(next_move)
        self.visited.add(next_move)
        self.last_analysis_path = []
        self.suggested_move = None
        self.solvable = None
        return next_move

    def undo_many(self, steps: int) -> int:
        undone = 0
        while undone < steps and self.moves:
            last_move = self.moves.pop()
            self.visited.remove(last_move)
            self.redo_stack.append(last_move)
            undone += 1

        if undone:
            self.last_analysis_path = []
            self.suggested_move = None
            self.solvable = None
        return undone

    def set_replay_snapshot(self, moves: List[Position]) -> None:
        self.moves = list(moves)
        self.visited = set(self.moves)
        self.redo_stack = []
        self.last_analysis_path = []
        self.suggested_move = None
        self.solvable = None

    def assess_solvability(self) -> Optional[bool]:
        if not self.current_move:
            self.solvable = None
            self.last_analysis_path = []
            return None

        if self.is_complete():
            self.solvable = True
            self.last_analysis_path = []
            return True

        if not board_has_any_full_tour(self.board_size):
            self.solvable = False
            self.last_analysis_path = []
            return False

        if len(self.moves) == 1:
            if not start_position_can_have_full_tour(self.board_size, self.moves[0]):
                self.solvable = False
                self.last_analysis_path = []
                return False

        cached_path = get_cached_path_for_moves(self.board_size, self.moves)
        if cached_path is not None:
            self.last_analysis_path = cached_path
            self.solvable = True
            return True

        if len(self.moves) == 1:
            fast_solution = find_start_tour_fast(self.board_size, self.moves[0])
            if fast_solution is not None:
                self.last_analysis_path = fast_solution
                self.solvable = True
                cache_start_path(self.board_size, self.moves[0], fast_solution)
                return True

        solution = find_solution_path(self.board_size, self.current_move, self.visited)
        self.last_analysis_path = solution or []
        self.solvable = solution is not None
        if solution and len(self.moves) == 1:
            cache_start_path(self.board_size, self.moves[0], solution)
        return self.solvable

    def analyze(self) -> Optional[List[Position]]:
        solvable = self.assess_solvability()
        if solvable is None:
            return None

        self.suggested_move = self.last_analysis_path[0] if self.last_analysis_path else None
        return list(self.last_analysis_path)

    def suggest(self) -> Optional[Position]:
        if self.solvable is None:
            self.assess_solvability()
        solution = self.last_analysis_path
        self.suggested_move = solution[0] if solution else None
        return self.suggested_move

    def format_position(self, move: Position) -> str:
        row, col = move
        return f"({row + 1}, {col + 1})"

    def format_move_list(self, moves: List[Position]) -> str:
        return "\n".join(
            f"{index + 1}. {self.format_position(move)}"
            for index, move in enumerate(moves)
        )
