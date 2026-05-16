import json
from pathlib import Path
from typing import Dict, List, Optional

from .solver import Position


CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"
CACHE_FILE = CACHE_DIR / "knights_tour_start_paths.json"


def _start_key(board_size: int, start: Position) -> str:
    return f"{board_size}:{start[0]},{start[1]}"


def _load_cache() -> Dict[str, List[List[int]]]:
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
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"start_paths": entries}
    with CACHE_FILE.open("w", encoding="utf-8") as cache_handle:
        json.dump(payload, cache_handle, indent=2)


def get_cached_start_path(
    board_size: int, start: Position
) -> Optional[List[Position]]:
    entries = _load_cache()
    raw_path = entries.get(_start_key(board_size, start))
    if raw_path is None:
        return None
    return [tuple(step) for step in raw_path]


def get_cached_path_for_moves(
    board_size: int, moves: List[Position]
) -> Optional[List[Position]]:
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
    entries = _load_cache()
    entries[_start_key(board_size, start)] = [[row, col] for row, col in path]
    _save_cache(entries)
