"""Logica pathfinding del labirinto."""

from collections import deque

from .models import DIRS, Coord, MazeData


class MazeSolver:
    """Trova il percorso più breve tra entrata e uscita di un labirinto."""

    def __init__(self, data: MazeData) -> None:
        self.data = data

    def solve(self) -> list[str]:
        """Ritorna il percorso più breve tra entrata e uscita tramite passi N/E/S/W."""
        if self.data.entry == self.data.exit:
            return []

        queue: deque[Coord] = deque([self.data.entry])
        prev: dict[Coord, tuple[Coord, str]] = {}
        seen: set[Coord] = {self.data.entry}

        while queue:
            current = queue.popleft()
            if current == self.data.exit:
                break
            for nxt, step in self._reachable_neighbors(current):
                if nxt in seen:
                    continue
                seen.add(nxt)
                prev[nxt] = (current, step)
                queue.append(nxt)

        if self.data.exit not in prev and self.data.exit != self.data.entry:
            raise ValueError("No valid path exists from entry to exit.")

        path: list[str] = []
        cursor = self.data.exit
        while cursor != self.data.entry:
            parent, step = prev[cursor]
            path.append(step)
            cursor = parent

        path.reverse()
        return path

    def get_path_coords(self) -> list[Coord]:
        """Ritorna il percorso più breve come una lista di Coord."""
        if self.data.entry == self.data.exit:
            return []

        queue: deque[Coord] = deque([self.data.entry])
        prev: dict[Coord, Coord] = {}
        seen: set[Coord] = {self.data.entry}

        while queue:
            current = queue.popleft()
            if current == self.data.exit:
                break
            for nxt, _ in self._reachable_neighbors(current):
                if nxt in seen:
                    continue
                seen.add(nxt)
                prev[nxt] = current
                queue.append(nxt)

        if self.data.exit not in prev and self.data.exit != self.data.entry:
            return []

        path: list[Coord] = []
        cursor = self.data.exit
        while cursor != self.data.entry:
            path.append(cursor)
            cursor = prev[cursor]
        path.append(self.data.entry)
        path.reverse()
        return path

    def _reachable_neighbors(self, current: Coord) -> list[tuple[Coord, str]]:
        out = []
        cell_walls = self.data.grid[current.y][current.x]
        for dx, dy, from_bit, _, step in DIRS:
            nx, ny = current.x + dx, current.y + dy
            nxt = Coord(nx, ny)
            if not self.data.inside(nx, ny) or nxt in self.data.closed_cells:
                continue
            if cell_walls & from_bit:
                continue
            out.append((nxt, step))
        return out
