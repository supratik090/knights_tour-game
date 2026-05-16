# Knight's Tour

A desktop Knight's Tour game built with Python and Tkinter.

The game lets you:
- Choose a board size from `5x5` to `10x10`
- Start from any square
- See valid next knight moves highlighted on the board
- Use `Suggest`, `Analyze`, `Auto Finish`, `Replay`, `Undo`, and `Redo`
- See whether the current path is still finishable using the badge beside the title

## Controls

- Click any square to place the first move.
- After that, click only highlighted squares to continue the knight path.
- `⟲` Undo the previous move.
- `⟳` Redo the most recently undone move.
- `Suggest` Highlight the next move that still keeps a full tour possible.
- `Analyze` Check whether the current position can still finish the tour.
- `Auto Finish` Automatically play the remaining solution if one is found.
- `Replay` Replay the current move history from the beginning.
- `New Game` Clear the board and start over.

## Solvability

- The badge near the title shows the current state:
- `Ready` means no move has been played yet.
- `Finishable` means the current path can still complete a full tour.
- `Blocked` means the current path cannot complete a full tour.

## Run The Game

From the project folder:

```bash
python3 app.py
```

## Precompute Cache

The project supports a local cache for full-tour start paths so large boards can load faster.

To generate the cache:

```bash
python3 precompute_start_cache.py
```

What this does:
- Precomputes start-position tour paths for board sizes `5x5` through `10x10`
- Writes cache data into `.cache/knights_tour_start_paths.json`
- Skips duplicate start positions using symmetry
- Skips impossible odd-board starts using parity rules

The cache file is local-only and does not need to be committed.

## Project Files

- `app.py` small launcher entry point
- `knights_tour/ui.py` Tkinter user interface
- `knights_tour/game.py` game state and rules
- `knights_tour/solver.py` solver and heuristics
- `knights_tour/cache.py` local cache helpers
- `precompute_start_cache.py` cache generation script

## Notes

- `requirements.txt` is comment-only because this project uses Python standard library modules.
- Very large boards may still take time if the cache is missing and the solver needs to compute a path live.
