import json
from pathlib import Path
from typing import Dict, List, Optional

from .solver import Position


CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"
CACHE_FILE = CACHE_DIR / "knights_tour_start_paths.json"


def _start_key(board_size: int, start: Position) -> str:
    """Build the stable dictionary key used for one starting square."""
    return f"{board_size}:{start[0]},{start[1]}"


def _load_cache() -> Dict[str, List[List[int]]]:
    """
    Load the start-position cache from disk.

    The cache is optional and local-only. If the file is missing or malformed,
    we return an empty dictionary so the rest of the app can fall back to live
    solving without crashing.
    """
    if not CACHE_FILE.exists():
        return {}

    try:
        with CACHE_FILE.open("r", encoding="utf-8") as cache_handle:
            payload = json.load(cache_handle)
    except (OSError, ValueError):
        return {}

    entries = payload.get("start_paths", {})
    return entries if isinstance(entries, dict) else {}


def _save_cache(entries: Dict[str, List[List[int]]]) -> None:
    """Persist the in-memory cache map to the local JSON cache file."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"start_paths": entries}
    with CACHE_FILE.open("w", encoding="utf-8") as cache_handle:
        json.dump(payload, cache_handle, indent=2)


def get_cached_start_path(
    board_size: int, start: Position
) -> Optional[List[Position]]:
    """
    Return the cached full remaining path for a fresh starting square.

    The stored path does not include the starting square itself. It contains
    only the remaining moves needed to complete the tour from that start.
    """
    entries = _load_cache()
    raw_path = entries.get(_start_key(board_size, start))
    if raw_path is None:
        return None
    return [tuple(step) for step in raw_path]


def get_cached_path_for_moves(
    board_size: int, moves: List[Position]
) -> Optional[List[Position]]:
    """
    Reuse a cached starting-line solution if the player's moves match its prefix.

    This is the bridge between cache data and live play:
    - look up the cached path for the original starting square
    - reconstruct the full tour for that start
    - verify that the player's current move history still follows that tour
    - if it does, return only the remaining suffix
    - if not, return None so the caller can fall back to live solving
    """
    if not moves:
        return None

    cached_remaining = get_cached_start_path(board_size, moves[0])
    if cached_remaining is None:
        return None

    full_tour = [moves[0]] + cached_remaining
    if full_tour[: len(moves)] != moves:
        return None

    return full_tour[len(moves) :]


def cache_start_path(board_size: int, start: Position, path: List[Position]) -> None:
    """Store a solved start-position path into the local cache."""
    entries = _load_cache()
    entries[_start_key(board_size, start)] = [[row, col] for row, col in path]
    _save_cache(entries)
