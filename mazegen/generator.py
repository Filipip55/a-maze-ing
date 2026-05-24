"""Core generation logic using a recursive backtracker algorithm."""

import random
from collections import deque

from .models import ALL_WALLS, DIRS, EXTRA_OPENINGS_DIVISOR, Coord, MazeData


class CoreGenerator:
    """Handles the structural generation of the maze."""

    def __init__(
        self,
        width: int,
        height: int,
        entry: Coord,
        exit_: Coord,
        seed: int | None,
        perfect: bool,
        include_42: bool,
    ) -> None:
        self.data = MazeData(
            width=width, height=height, entry=entry, exit=exit_
        )
        self.perfect = perfect
        self.include_42 = include_42
        self.rng = random.Random(seed)
        self.warnings: list[str] = []

    def generate(self) -> MazeData:
        """Build the maze grid and return the state data."""
        self.data.grid = [
            [ALL_WALLS for _ in range(self.data.width)]
            for _ in range(self.data.height)
        ]
        self.data.closed_cells = set()
        self.warnings.clear()

        if self.include_42:
            self._inject_42_pattern()

        open_cells = [
            Coord(x, y)
            for y in range(self.data.height)
            for x in range(self.data.width)
            if Coord(x, y) not in self.data.closed_cells
        ]

        if not open_cells:
            raise ValueError("Maze has no open cells left after pattern.")

        start = self.data.entry
        if start in self.data.closed_cells:
            raise ValueError("Entry cell cannot be in closed '42' pattern.")

        visited: set[Coord] = {start}
        stack: list[Coord] = [start]

        while stack:
            current = stack[-1]
            neighbors = self._unvisited_neighbors(current, visited)
            if not neighbors:
                stack.pop()
                continue

            nx, ny, from_bit, to_bit = self.rng.choice(neighbors)
            nxt = Coord(nx, ny)
            self.data.grid[current.y][current.x] &= ~from_bit
            self.data.grid[nxt.y][nxt.x] &= ~to_bit
            visited.add(nxt)
            stack.append(nxt)

        if len(visited) != len(open_cells):
            raise ValueError("Maze generation failed: cells are disconnected.")

        if not self.perfect:
            self._add_extra_openings()

        return self.data

    def _inject_42_pattern(self) -> None:
        pattern = [
            "#.#.###",
            "#.#...#",
            "###.###",
            "..#.#..",
            "..#.###",
        ]
        p_height = len(pattern)
        p_width = len(pattern[0])

        if self.data.width < p_width + 2 or self.data.height < p_height + 2:
            self.warnings.append("Maze too small for '42'. Pattern omitted.")
            return

        ox = (self.data.width - p_width) // 2
        oy = (self.data.height - p_height) // 2
        proposed: set[Coord] = set()
        for py, row in enumerate(pattern):
            for px, ch in enumerate(row):
                if ch == "#":
                    proposed.add(Coord(ox + px, oy + py))

        if self.data.entry in proposed or self.data.exit in proposed:
            self.warnings.append("'42' pattern overlaps entry/exit.")
            return

        if not self._is_open_graph_connected(proposed):
            self.warnings.append("Unable to keep maze connected with '42'.")
            return

        self.data.closed_cells = proposed
        for cell in proposed:
            self.data.grid[cell.y][cell.x] = ALL_WALLS

    def _is_open_graph_connected(self, blocked: set[Coord]) -> bool:
        open_cells = [
            Coord(x, y)
            for y in range(self.data.height)
            for x in range(self.data.width)
            if Coord(x, y) not in blocked
        ]
        if not open_cells:
            return False

        start = self.data.entry if self.data.entry not in blocked else open_cells[0]
        seen: set[Coord] = {start}
        q: deque[Coord] = deque([start])
        while q:
            current = q.popleft()
            for dx, dy, *_ in DIRS:
                nx, ny = current.x + dx, current.y + dy
                nxt = Coord(nx, ny)
                if not self.data.inside(nx, ny) or nxt in blocked or nxt in seen:
                    continue
                seen.add(nxt)
                q.append(nxt)
        return len(seen) == len(open_cells)

    def _unvisited_neighbors(
        self, current: Coord, visited: set[Coord]
    ) -> list[tuple[int, int, int, int]]:
        candidates = []
        for dx, dy, from_bit, to_bit, _ in DIRS:
            nx, ny = current.x + dx, current.y + dy
            nxt = Coord(nx, ny)
            if not self.data.inside(nx, ny):
                continue
            if nxt in self.data.closed_cells or nxt in visited:
                continue
            candidates.append((nx, ny, from_bit, to_bit))
        return candidates

    def _add_extra_openings(self) -> None:
        cell_count = max(1, self.data.width * self.data.height)
        for _ in range(cell_count // EXTRA_OPENINGS_DIVISOR):
            x = self.rng.randrange(self.data.width)
            y = self.rng.randrange(self.data.height)
            cell = Coord(x, y)
            if cell in self.data.closed_cells:
                continue
            options = []
            for dx, dy, from_bit, to_bit, _ in DIRS:
                nx, ny = x + dx, y + dy
                nxt = Coord(nx, ny)
                if not self.data.inside(nx, ny) or nxt in self.data.closed_cells:
                    continue
                if self.data.grid[y][x] & from_bit:
                    options.append((nx, ny, from_bit, to_bit))
            if not options:
                continue
            nx, ny, from_bit, to_bit = self.rng.choice(options)
            self.data.grid[y][x] &= ~from_bit
            self.data.grid[ny][nx] &= ~to_bit
