"""Logica di generazione del labirinto tramite algoritmo di backtracking."""

import random
from collections import deque

from .models import (
    ALL_WALLS,
    DIRS,
    EAST,
    EXTRA_OPENINGS_DIVISOR,
    NORTH,
    SOUTH,
    WEST,
    Coord,
    MazeData,
)


class CoreGenerator:
    """Genera la struttura del labirinto."""

    DIGIT_PATTERNS: dict[int, list[str]] = {
        42: [
            "#.#.###",
            "#.#...#",
            "###.###",
            "..#.#..",
            "..#.###",
        ],
        27: [
            "###.###",
            "..#...#",
            "###..#.",
            "#....#.",
            "###..#.",
        ],
        21: [
            "###.##.",
            "..#..#.",
            "###..#.",
            "#....#.",
            "###.###",
        ],
    }

    SUPPORTED_ALGORITHMS = {"backtracker", "binary_tree"}

    def __init__(
        self,
        width: int,
        height: int,
        entry: Coord,
        exit_: Coord,
        seed: int | None,
        perfect: bool,
        include_42: bool,
        algorithm: str,
    ) -> None:
        """Inizializza il generatore con parametri e stato condiviso."""
        if algorithm not in self.SUPPORTED_ALGORITHMS:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        self.data = MazeData(
            width=width, height=height, entry=entry, exit=exit_
        )
        self.perfect = perfect
        self.include_42 = include_42
        self.algorithm = algorithm
        self.seed = seed
        self.rng = random.Random(seed)
        self.warnings: list[str] = []
        self.last_open_steps: list[tuple[Coord, Coord]] = []

    def generate(self) -> MazeData:
        """Genera la matrice del labirinto e crea corridoi validi."""
        self.data.grid = [
            [ALL_WALLS for _ in range(self.data.width)]
            for _ in range(self.data.height)
        ]
        self.data.closed_cells = set()
        self.warnings.clear()
        self.last_open_steps = []

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

        if self.algorithm == "backtracker":
            visited = self._generate_with_backtracker(start)
        elif self.algorithm == "binary_tree":
            visited = self._generate_with_binary_tree(open_cells)
        else:
            raise ValueError(f"Unsupported algorithm: {self.algorithm}")

        if len(visited) != len(open_cells):
            raise ValueError("Maze generation failed: cells are disconnected.")
        if not self._ensure_connected(open_cells):
            raise ValueError(
                "Maze generation failed: unable to connect cells."
            )
        if not self._is_generated_maze_connected(open_cells):
            raise ValueError("Maze generation failed: no path to all cells.")

        if not self.perfect:
            self._add_extra_openings()

        return self.data

    def _inject_42_pattern(self) -> None:
        """Inserisce un pattern numerico chiuso in base al seed."""
        pattern_seed = self.get_pattern_seed()
        pattern = self.DIGIT_PATTERNS.get(
            pattern_seed,
            self.DIGIT_PATTERNS[42],
        )
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

    def get_pattern_seed(self) -> int:
        """Ritorna il seed attivo usato per scegliere il pattern centrale."""
        if self.seed in self.DIGIT_PATTERNS:
            return self.seed
        return 42

    def _is_open_graph_connected(self, blocked: set[Coord]) -> bool:
        """Controlla che le celle non bloccate restino tutte raggiungibili."""
        open_cells = [
            Coord(x, y)
            for y in range(self.data.height)
            for x in range(self.data.width)
            if Coord(x, y) not in blocked
        ]
        if not open_cells:
            return False

        start = (
            self.data.entry
            if self.data.entry not in blocked
            else open_cells[0]
        )
        seen: set[Coord] = {start}
        q: deque[Coord] = deque([start])
        while q:
            current = q.popleft()
            for dx, dy, *_ in DIRS:
                nx, ny = current.x + dx, current.y + dy
                nxt = Coord(nx, ny)
                if (
                    not self.data.inside(nx, ny)
                    or nxt in blocked
                    or nxt in seen
                ):
                    continue
                seen.add(nxt)
                q.append(nxt)
        return len(seen) == len(open_cells)

    def _unvisited_neighbors(
        self, current: Coord, visited: set[Coord]
    ) -> list[tuple[int, int, int, int]]:
        """Trova i vicini non visitati senza creare aree aperte 3x3."""
        candidates = []
        for dx, dy, from_bit, to_bit, _ in DIRS:
            nx, ny = current.x + dx, current.y + dy
            nxt = Coord(nx, ny)
            if not self.data.inside(nx, ny):
                continue
            if nxt in self.data.closed_cells or nxt in visited:
                continue
            if not self._can_open_between(current, nxt, from_bit, to_bit):
                continue
            candidates.append((nx, ny, from_bit, to_bit))
        return candidates

    def _add_extra_openings(self) -> None:
        """Aggiunge aperture extra rispettando il vincolo anti-3x3."""
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
                if (
                    not self.data.inside(nx, ny)
                    or nxt in self.data.closed_cells
                ):
                    continue
                if self.data.grid[y][x] & from_bit:
                    options.append((nx, ny, from_bit, to_bit))
            if not options:
                continue
            nx, ny, from_bit, to_bit = self.rng.choice(options)
            current = Coord(x, y)
            nxt = Coord(nx, ny)
            if self._can_open_between(current, nxt, from_bit, to_bit):
                self._open_between(current, nxt, from_bit, to_bit)

    def _generate_with_backtracker(self, start: Coord) -> set[Coord]:
        """Genera il labirinto con DFS iterativa e backtracking."""
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
            self._open_between(current, nxt, from_bit, to_bit)
            visited.add(nxt)
            stack.append(nxt)
        return visited

    def _generate_with_binary_tree(
        self, open_cells: list[Coord]
    ) -> set[Coord]:
        """Genera il labirinto con algoritmo binary-tree."""
        visited: set[Coord] = set(open_cells)
        for y in range(self.data.height):
            for x in range(self.data.width):
                cell = Coord(x, y)
                if cell in self.data.closed_cells:
                    continue
                options: list[tuple[Coord, int, int]] = []
                north = Coord(x, y - 1)
                east = Coord(x + 1, y)
                if self.data.inside(north.x, north.y):
                    if north not in self.data.closed_cells:
                        options.append((north, NORTH, SOUTH))
                if self.data.inside(east.x, east.y):
                    if east not in self.data.closed_cells:
                        options.append((east, EAST, WEST))
                if not options:
                    continue
                nxt, from_bit, to_bit = self.rng.choice(options)
                if self._can_open_between(cell, nxt, from_bit, to_bit):
                    self._open_between(cell, nxt, from_bit, to_bit)
        return visited

    def _open_between(
        self, current: Coord, nxt: Coord, from_bit: int, to_bit: int
    ) -> None:
        """Apre il passaggio tra due celle adiacenti."""
        self.data.grid[current.y][current.x] &= ~from_bit
        self.data.grid[nxt.y][nxt.x] &= ~to_bit
        self.last_open_steps.append((current, nxt))

    def _can_open_between(
        self, current: Coord, nxt: Coord, from_bit: int, to_bit: int
    ) -> bool:
        """Valuta se aprire un muro viola il vincolo delle aree 3x3."""
        if not (self.data.grid[current.y][current.x] & from_bit):
            return True

        self.data.grid[current.y][current.x] &= ~from_bit
        self.data.grid[nxt.y][nxt.x] &= ~to_bit
        forbidden = self._contains_forbidden_3x3_near(current, nxt)
        self.data.grid[current.y][current.x] |= from_bit
        self.data.grid[nxt.y][nxt.x] |= to_bit
        return not forbidden

    def _contains_forbidden_3x3_near(
        self, first: Coord, second: Coord
    ) -> bool:
        """Controlla blocchi 3x3 vicini alle due celle appena modificate."""
        min_x = min(first.x, second.x) - 2
        min_y = min(first.y, second.y) - 2
        max_x = max(first.x, second.x)
        max_y = max(first.y, second.y)
        for top_y in range(min_y, max_y + 1):
            for top_x in range(min_x, max_x + 1):
                if self._is_open_3x3(top_x, top_y):
                    return True
        return False

    def _is_open_3x3(self, top_x: int, top_y: int) -> bool:
        """Verifica se un blocco 3x3 è completamente aperto."""
        if top_x < 0 or top_y < 0:
            return False
        if top_x + 2 >= self.data.width or top_y + 2 >= self.data.height:
            return False

        for y in range(top_y, top_y + 3):
            for x in range(top_x, top_x + 3):
                if Coord(x, y) in self.data.closed_cells:
                    return False
        for y in range(top_y, top_y + 3):
            for x in range(top_x, top_x + 2):
                if self.data.grid[y][x] & EAST:
                    return False
        for y in range(top_y, top_y + 2):
            for x in range(top_x, top_x + 3):
                if self.data.grid[y][x] & SOUTH:
                    return False
        return True

    def _is_generated_maze_connected(self, open_cells: list[Coord]) -> bool:
        """Verifica con BFS che tutte le celle aperte siano raggiungibili."""
        if not open_cells:
            return False
        start = self.data.entry
        seen: set[Coord] = {start}
        queue: deque[Coord] = deque([start])
        while queue:
            current = queue.popleft()
            cell_walls = self.data.grid[current.y][current.x]
            for dx, dy, from_bit, _, _ in DIRS:
                nxt = Coord(current.x + dx, current.y + dy)
                if not self.data.inside(nxt.x, nxt.y):
                    continue
                if nxt in self.data.closed_cells:
                    continue
                if cell_walls & from_bit or nxt in seen:
                    continue
                seen.add(nxt)
                queue.append(nxt)
        return len(seen) == len(open_cells)

    def _ensure_connected(self, open_cells: list[Coord]) -> bool:
        """Apre muri tra componenti diverse finché possibile."""
        while True:
            components = self._connected_components(open_cells)
            if len(components) <= 1:
                return True

            comp_map: dict[Coord, int] = {}
            for idx, component in enumerate(components):
                for cell in component:
                    comp_map[cell] = idx

            connected = False
            for cell in open_cells:
                for dx, dy, from_bit, to_bit, _ in DIRS:
                    nxt = Coord(cell.x + dx, cell.y + dy)
                    if nxt not in comp_map:
                        continue
                    if comp_map[cell] == comp_map[nxt]:
                        continue
                    if not (self.data.grid[cell.y][cell.x] & from_bit):
                        continue
                    if not self._can_open_between(cell, nxt, from_bit, to_bit):
                        continue
                    self._open_between(cell, nxt, from_bit, to_bit)
                    connected = True
                    break
                if connected:
                    break
            if not connected:
                return False

    def _connected_components(
        self, open_cells: list[Coord]
    ) -> list[set[Coord]]:
        """Ritorna le componenti connesse usando i muri correnti."""
        all_open = set(open_cells)
        seen: set[Coord] = set()
        components: list[set[Coord]] = []

        for start in open_cells:
            if start in seen:
                continue
            component: set[Coord] = set()
            queue: deque[Coord] = deque([start])
            seen.add(start)
            while queue:
                current = queue.popleft()
                component.add(current)
                cell_walls = self.data.grid[current.y][current.x]
                for dx, dy, from_bit, _, _ in DIRS:
                    nxt = Coord(current.x + dx, current.y + dy)
                    if nxt not in all_open or nxt in seen:
                        continue
                    if cell_walls & from_bit:
                        continue
                    seen.add(nxt)
                    queue.append(nxt)
            components.append(component)
        return components
