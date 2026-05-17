"""High-resolution ASCII rendering using box-drawing characters."""

from .models import EAST, NORTH, SOUTH, WEST, Coord, MazeData


class MazeRenderer:
    """Handles terminal visualization of the maze."""

    WALLS = {
        0: ' ', 1: '┃', 2: '━', 3: '┗', 4: '┃', 5: '┃', 6: '┏', 7: '┣',
        8: '━', 9: '┛', 10: '━', 11: '┻', 12: '┓', 13: '┫', 14: '┳', 15: '╋',
    }

    PATHS = {
        0: ' ', 1: '│', 2: '─', 3: '╰', 4: '│', 5: '│', 6: '╭', 7: '├',
        8: '─', 9: '╯', 10: '─', 11: '┴', 12: '╮', 13: '┤', 14: '┬', 15: '┼',
    }

    def __init__(self, data: MazeData) -> None:
        self.data = data
        self.w = data.width * 2 + 1
        self.h = data.height * 2 + 1
        self.canvas: list[list[str]] = []

    def render(
        self,
        path: list[Coord],
        show_solution: bool = False,
        color: str = "",
    ) -> str:
        """Render the complete maze as a string."""
        self.canvas = [[' ' for _ in range(self.w)] for _ in range(self.h)]
        self._draw_walls()
        self._draw_cells()
        if show_solution and path:
            self._draw_path(path)

        # Mappa per espandere i caratteri nelle colonne dispari (centri delle celle)
        stretch_map = {
            "━": "━━━",
            "█": "███",
            "▶": " ▶ ",
            "✖": " ✖ ",
            " ": "   ",
            "│": " │ ",
            "─": "───",
            "╰": " ╰─",
            "╭": " ╭─",
            "╮": "─╮ ",
            "╯": "─╯ ",
            "├": " ├─",
            "┤": "─┤ ",
            "┬": "─┬─",
            "┴": "─┴─",
            "┼": "─┼─",
        }

        reset = "\033[0m" if color else ""
        lines: list[str] = []

        for row in self.canvas:
            line_parts = []
            for x, char in enumerate(row):
                if x % 2 != 0:
                    # Usa la mappa per espandere, di default metti 3 spazi
                    line_parts.append(stretch_map.get(char, "   "))
                else:
                    # Le colonne pari (i muri verticali) rimangono di 1 carattere
                    line_parts.append(char)
            lines.append(f"{color}{''.join(line_parts)}{reset}")

        return "\n".join(lines)

    def _draw_walls(self) -> None:
        for y in range(self.data.height):
            for x in range(self.data.width):
                cell_walls = self.data.grid[y][x]
                cy, cx = y * 2 + 1, x * 2 + 1
                if cell_walls & NORTH:
                    self.canvas[cy - 1][cx] = '━'
                if cell_walls & SOUTH:
                    self.canvas[cy + 1][cx] = '━'
                if cell_walls & WEST:
                    self.canvas[cy][cx - 1] = '┃'
                if cell_walls & EAST:
                    self.canvas[cy][cx + 1] = '┃'

        for y in range(0, self.h, 2):
            for x in range(0, self.w, 2):
                mask = 0
                if y > 0 and self.canvas[y - 1][x] == '┃':
                    mask |= 1
                if x < self.w - 1 and self.canvas[y][x + 1] == '━':
                    mask |= 2
                if y < self.h - 1 and self.canvas[y + 1][x] == '┃':
                    mask |= 4
                if x > 0 and self.canvas[y][x - 1] == '━':
                    mask |= 8
                self.canvas[y][x] = self.WALLS[mask]

    def _draw_cells(self) -> None:
        for cell in self.data.closed_cells:
            self.canvas[cell.y * 2 + 1][cell.x * 2 + 1] = '█'

        ex, ey = self.data.entry.x * 2 + 1, self.data.entry.y * 2 + 1
        if self.canvas[ey][ex] == ' ':
            self.canvas[ey][ex] = '▶'

        xx, xy = self.data.exit.x * 2 + 1, self.data.exit.y * 2 + 1
        if self.canvas[xy][xx] == ' ':
            self.canvas[xy][xx] = '✖'

    def _draw_path(self, path: list[Coord]) -> None:
        for i, cell in enumerate(path):
            if cell == self.data.entry or cell == self.data.exit:
                continue

            mask = 0
            prev_c = path[i - 1] if i > 0 else cell
            next_c = path[i + 1] if i < len(path) - 1 else cell

            for adj in (prev_c, next_c):
                if adj.y < cell.y:
                    mask |= 1
                elif adj.x > cell.x:
                    mask |= 2
                elif adj.y > cell.y:
                    mask |= 4
                elif adj.x < cell.x:
                    mask |= 8

            self.canvas[cell.y * 2 + 1][cell.x * 2 + 1] = self.PATHS[mask]

            if next_c.y < cell.y:
                self.canvas[cell.y * 2][cell.x * 2 + 1] = '│'
            elif next_c.y > cell.y:
                self.canvas[cell.y * 2 + 2][cell.x * 2 + 1] = '│'
            elif next_c.x < cell.x:
                self.canvas[cell.y * 2 + 1][cell.x * 2] = '─'
            elif next_c.x > cell.x:
                self.canvas[cell.y * 2 + 1][cell.x * 2 + 2] = '─'
