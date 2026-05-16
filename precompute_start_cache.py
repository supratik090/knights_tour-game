from knights_tour.cache import CACHE_FILE, cache_start_path, get_cached_start_path
from knights_tour.solver import (
    find_solution_path,
    find_start_tour_fast,
    symmetry_orbit,
    start_position_can_have_full_tour,
    transform_path,
)


def main() -> None:
    print(f"Writing cache to: {CACHE_FILE}")

    for board_size in (5, 6, 7, 8, 9, 10):
        total_starts = board_size * board_size
        completed = 0
        covered_starts = set()
        print(f"\nPrecomputing {board_size}x{board_size} start positions...")

        for row in range(board_size):
            for col in range(board_size):
                start = (row, col)
                if start in covered_starts:
                    completed += 1
                    print(
                        f"  [{completed}/{total_starts}] start {start} covered by symmetry"
                    )
                    continue

                orbit = symmetry_orbit(start, board_size)
                if not start_position_can_have_full_tour(board_size, start):
                    covered_starts.update(orbit)
                    completed += 1
                    print(
                        f"  [{completed}/{total_starts}] start {start} is impossible by parity on {board_size}x{board_size}"
                    )
                    continue

                cached_transforms = {
                    orbit_start: get_cached_start_path(board_size, orbit_start)
                    for orbit_start in orbit
                }
                if any(path is not None for path in cached_transforms.values()):
                    covered_starts.update(orbit)
                    completed += 1
                    print(
                        f"  [{completed}/{total_starts}] start {start} already cached through symmetry"
                    )
                    continue

                cached = get_cached_start_path(board_size, start)
                if cached is not None:
                    covered_starts.update(orbit)
                    completed += 1
                    print(
                        f"  [{completed}/{total_starts}] start {start} already cached"
                    )
                    continue

                solution = find_start_tour_fast(board_size, start)
                if solution is None:
                    solution = find_solution_path(board_size, start, {start})
                completed += 1
                if solution is None:
                    print(
                        f"  [{completed}/{total_starts}] start {start} has no cached solution"
                    )
                    continue

                for transform_id in range(8):
                    transformed_start = orbit[transform_id] if transform_id < len(orbit) else None
                    transformed_path = transform_path(solution, board_size, transform_id)
                    transformed_origin = transform_path([start], board_size, transform_id)[0]
                    cache_start_path(board_size, transformed_origin, transformed_path)
                    covered_starts.add(transformed_origin)
                print(
                    f"  [{completed}/{total_starts}] cached symmetry orbit for start {start} with {len(solution)} remaining moves"
                )

    print("\nCache generation complete.")


if __name__ == "__main__":
    main()
