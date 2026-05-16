import random
from typing import List, Optional, Set, Tuple


Position = Tuple[int, int]


def board_has_any_full_tour(size: int) -> bool:
    """Return whether this board size can support any complete tour at all."""
    # For the square sizes this app supports, 4x4 has no full knight's tour.
    # 5x5, 6x6, and 7x7 do have tours.
    return size != 4


def start_position_can_have_full_tour(size: int, start: Position) -> bool:
    """
    Fast mathematical filter for impossible starting squares.

    On odd-sized boards, one board color appears one extra time. Because a
    knight alternates color every move, a full tour on an odd board must start
    on that majority color. This lets us reject impossible starts instantly.
    """
    if not board_has_any_full_tour(size):
        return False

    # On odd-sized boards, the knight alternates square color and a full tour
    # has even length, so start and end land on the same color. Since odd
    # boards have one extra square of the (0, 0) color, a full tour can only
    # start on that majority color.
    if size % 2 == 1 and (start[0] + start[1]) % 2 == 1:
        return False

    return True


def valid_moves_from(position: Position, size: int, visited: Set[Position]) -> List[Position]:
    """Return all legal unvisited knight moves from a given square."""
    row, col = position
    candidates = [
        (row + 2, col + 1),
        (row + 2, col - 1),
        (row - 2, col + 1),
        (row - 2, col - 1),
        (row + 1, col + 2),
        (row + 1, col - 2),
        (row - 1, col + 2),
        (row - 1, col - 2),
    ]

    valid_moves = []
    for next_row, next_col in candidates:
        if 0 <= next_row < size and 0 <= next_col < size:
            if (next_row, next_col) not in visited:
                valid_moves.append((next_row, next_col))
    return valid_moves


def transform_position(position: Position, size: int, transform_id: int) -> Position:
    """Apply one of the 8 square-board symmetry transforms to a position."""
    row, col = position
    last = size - 1

    transforms = {
        0: (row, col),
        1: (col, last - row),
        2: (last - row, last - col),
        3: (last - col, row),
        4: (row, last - col),
        5: (last - row, col),
        6: (col, row),
        7: (last - col, last - row),
    }
    return transforms[transform_id]


def transform_path(path: List[Position], size: int, transform_id: int) -> List[Position]:
    """Apply the same symmetry transform to every step in a path."""
    return [transform_position(step, size, transform_id) for step in path]


def symmetry_orbit(position: Position, size: int) -> List[Position]:
    """Return every position equivalent under board rotation/reflection."""
    orbit = {
        transform_position(position, size, transform_id)
        for transform_id in range(8)
    }
    return sorted(orbit)


def ordered_moves(position: Position, size: int, visited: Set[Position]) -> List[Position]:
    """
    Rank candidate moves so the search explores promising branches first.

    The score is Warnsdorff-style:
    - fewer onward moves first
    - then lower total onward branching
    - then a slight edge preference to consume constrained squares earlier
    """
    def move_score(move: Position) -> Tuple[int, int, int]:
        next_seen = visited | {move}
        onward = valid_moves_from(move, size, next_seen)
        onward_degrees = sum(
            len(valid_moves_from(candidate, size, next_seen | {candidate}))
            for candidate in onward
        )
        edge_bias = min(move[0], move[1], size - 1 - move[0], size - 1 - move[1])
        return (len(onward), onward_degrees, edge_bias)

    return sorted(valid_moves_from(position, size, visited), key=move_score)


def find_start_tour_fast(
    board_size: int, start: Position, max_attempts: int = 64
) -> Optional[List[Position]]:
    """
    Quickly try to build a full tour from an empty board using greedy heuristics.

    This is intentionally not a complete proof search. It is used for two
    practical cases:
    - speeding up the first move on a fresh board
    - generating cache entries in the precompute script

    The method performs repeated greedy attempts with deterministic random tie
    breaking so different attempts explore slightly different routes. If one
    attempt reaches all remaining squares, we return the path; otherwise we
    return None and let the exact solver handle the hard case if needed.
    """
    if not start_position_can_have_full_tour(board_size, start):
        return None

    total_tiles = board_size ** 2

    def greedy_attempt(seed: int) -> Optional[List[Position]]:
        rng = random.Random(seed)
        visited = {start}
        current = start
        path: List[Position] = []

        for _ in range(total_tiles - 1):
            candidates = valid_moves_from(current, board_size, visited)
            if not candidates:
                return None

            def score(move: Position) -> Tuple[int, int, float]:
                next_seen = visited | {move}
                onward = valid_moves_from(move, board_size, next_seen)
                onward_degrees = sum(
                    len(valid_moves_from(candidate, board_size, next_seen | {candidate}))
                    for candidate in onward
                )
                return (len(onward), onward_degrees, rng.random())

            next_move = min(candidates, key=score)
            visited.add(next_move)
            path.append(next_move)
            current = next_move

        return path

    base_seed = board_size * 100 + start[0] * 10 + start[1]
    for attempt in range(max_attempts):
        solution = greedy_attempt(base_seed + attempt)
        if solution is not None:
            return solution

    return None


def find_solution_path(
    board_size: int, current: Position, visited: Set[Position]
) -> Optional[List[Position]]:
    """
    Try to finish a full Knight's Tour from the current board state.

    Human-readable overview:
    - We start from the knight's current square and the set of squares that
      have already been visited by earlier moves.
    - The goal is to find at least one sequence of legal knight moves that
      visits every remaining square exactly once.
    - If such a sequence exists, we return the remaining path as a list of
      board positions.
    - If every possible continuation fails, we return None.

    How the search works:
    - First we reject impossible cases quickly, such as unsupported board
      sizes or starting positions that cannot have a full tour by parity.
    - Then we use depth-first search with backtracking:
      1. Generate all legal next knight moves.
      2. Try one move.
      3. Recurse from that new position.
      4. If that branch gets stuck, undo that trial move and try the next one.
    - The search stops as soon as one full tour is found.

    Why it is reasonably fast:
    - Candidate moves are ordered with a Warnsdorff-style heuristic.
    - We prefer moves that lead to the fewest onward options first, because
      those constrained squares are most likely to become dead ends later.
    - This does not change correctness; it only improves the order in which
      the search explores branches.
    """
    if not board_has_any_full_tour(board_size):
        return None

    if len(visited) == 1 and current in visited:
        if not start_position_can_have_full_tour(board_size, current):
            return None

    total_tiles = board_size ** 2
    if len(visited) == total_tiles:
        return []

    seen = set(visited)
    path: List[Position] = []

    def search(position: Position) -> bool:
        if len(seen) == total_tiles:
            return True

        for next_move in ordered_moves(position, board_size, seen):
            seen.add(next_move)
            path.append(next_move)
            if search(next_move):
                return True
            path.pop()
            seen.remove(next_move)

        return False

    if search(current):
        return path
    return None
