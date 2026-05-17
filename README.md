*This project has been created as part of the 42 curriculum by icoman, edingwiz.*

## Description
A-Maze-ing is a Python maze generator project.
It reads a configuration file, generates a valid maze, exports a hexadecimal file format, and displays an interactive ASCII view.
The implementation focuses on clarity, robust error handling, and reusable architecture.

## Instructions
### Requirements
- Python 3.10+

### Install
```bash
make install
```

### Run
```bash
python3 a_maze_ing.py config.txt
```
or
```bash
make run
```

### Debug
```bash
make debug
```

### Lint and type-check
```bash
make lint
```

### Clean generated caches/artifacts
```bash
make clean
```

## Configuration file format
The config file uses one `KEY=VALUE` per line. Lines starting with `#` are comments.

Mandatory keys:
- `WIDTH` (int): maze width in cells
- `HEIGHT` (int): maze height in cells
- `ENTRY` (x,y): entry cell coordinates
- `EXIT` (x,y): exit cell coordinates
- `OUTPUT_FILE` (string): output filename
- `PERFECT` (bool): enable perfect maze mode

Optional keys:
- `SEED` (int): deterministic random seed
- `INCLUDE_42` (bool): enable/disable visible `42` closed pattern

Example:
```txt
WIDTH=20
HEIGHT=12
ENTRY=0,0
EXIT=19,11
OUTPUT_FILE=maze.txt
PERFECT=True
SEED=42
INCLUDE_42=True
```

## Maze generation algorithm
The generator uses a depth-first recursive-backtracker strategy implemented iteratively with a stack.
This produces a spanning-tree structure over non-closed cells (perfect maze mode).

## Why this algorithm
- Simple to understand and implement for beginners.
- Naturally produces connected mazes.
- Works well with deterministic seeds for reproducibility.

## Reusable module
Reusable code lives in the `mazegen` package with one main class: `MazeGenerator`.

### Basic usage
```python
from mazegen import MazeGenerator

g = MazeGenerator(width=20, height=12, entry=(0, 0), exit_=(19, 11), seed=42)
g.generate()
print(g.to_hex_rows())
print(g.shortest_path())
```

### Custom parameters
You can pass custom `seed`, `perfect`, and `include_42` values.

### Accessible generated data
- Maze structure: `grid` (bit flags N/E/S/W per cell)
- Closed `42` cells: `closed_cells`
- Shortest valid solution: `shortest_path()`

## Visual representation
Terminal ASCII rendering is provided from the main script.
Interactive commands:
- regenerate maze
- show/hide shortest path
- rotate wall colors

## Team and project management
### Roles
- `icoman`: architecture, generation engine, output encoding
- `edingwiz`: parser, interactive display loop, validation checks

### Anticipated planning and evolution
Planned phases:
1. parser and infrastructure
2. generation and pathfinding
3. output/export and rendering
4. refactor and validation

The same structure was maintained with small iterative improvements.

### What worked well
- Keeping generation logic inside a reusable class.
- Strong validation at parser and generator boundaries.

### What could be improved
- More automatic test coverage for edge-case configurations.
- Additional rendering modes.

### Tools used
- Python standard library (`random`, `collections`, `dataclasses`, `typing`)
- `flake8` for style
- `mypy` for static typing
- `build` for wheel/sdist packaging

## Resources
- Python documentation: https://docs.python.org/3/
- PEP 257 docstrings: https://peps.python.org/pep-0257/
- mypy documentation: https://mypy.readthedocs.io/
- Recursive backtracker overview: https://en.wikipedia.org/wiki/Maze_generation_algorithm

### AI usage
AI was used to:
- structure implementation steps,
- validate interpretation of requirements,
- review naming/docstring consistency.
All generated proposals were manually checked and adapted.
