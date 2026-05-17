"""Standard ASCII rendering for the maze."""

from .models import EAST, NORTH, SOUTH, WEST, Coord, MazeData


class MazeRenderer:
    """Handles terminal visualization of the maze."""

    def __init__(self, data: MazeData) -> None:
        self.data = data
        self.w = data.width * 2 + 1
        self.h = data.height * 2 + 1
        self.canvas: list[list[str]] = [
            [' ' for _ in range(self.w)] for _ in range(self.h)
        ]

    def render(
        self, path: list[Coord], show_solution: bool = False, color: str = ""
    ) -> str:
        """Render the complete maze as an ASCII string with aspect ratio fixed."""
        self._draw_walls()
        self._draw_cells()
        if show_solution and path:
            self._draw_path(path)

        reset = "\033[0m" if color else ""
        lines: list[str] = []

        # Aspect ratio correction mapping for odd columns
        expand_map = {
            '-': '---',
            '#': '###',
            'S': ' S ',
            'E': ' E ',
            '.': ' . ',
            ' ': '   ',
        }

        for row in self.canvas:
            line_parts = []
            for x, char in enumerate(row):
                if x % 2 != 0:
                    expanded = expand_map.get(char, "   ")
                    if char == '-':
                        line_parts.append(f"{color}{expanded}{reset}")
                    else:
                        line_parts.append(expanded)
                else:
                    if char in ('+', '|'):
                        line_parts.append(f"{color}{char}{reset}")
                    else:
                        line_parts.append(char)
            lines.append("".join(line_parts))

        return "\n".join(lines)

    def _draw_walls(self) -> None:
        """Draw the grid lines representing the walls."""
        for y in range(self.data.height):
            for x in range(self.data.width):
                cell_walls = self.data.grid[y][x]
                cy, cx = y * 2 + 1, x * 2 + 1

                self.canvas[cy - 1][cx - 1] = '+'
                self.canvas[cy - 1][cx + 1] = '+'
                self.canvas[cy + 1][cx - 1] = '+'
                self.canvas[cy + 1][cx + 1] = '+'

                if cell_walls & NORTH:
                    self.canvas[cy - 1][cx] = '-'
                if cell_walls & SOUTH:
                    self.canvas[cy + 1][cx] = '-'
                if cell_walls & WEST:
                    self.canvas[cy][cx - 1] = '|'
                if cell_walls & EAST:
                    self.canvas[cy][cx + 1] = '|'

    def _draw_cells(self) -> None:
        """Draw the 42 pattern, entry, and exit."""
        for cell in self.data.closed_cells:
            self.canvas[cell.y * 2 + 1][cell.x * 2 + 1] = '#'

        ex, ey = self.data.entry.x * 2 + 1, self.data.entry.y * 2 + 1
        self.canvas[ey][ex] = 'S'

        xx, xy = self.data.exit.x * 2 + 1, self.data.exit.y * 2 + 1
        self.canvas[xy][xx] = 'E'

    def _draw_path(self, path: list[Coord]) -> None:
        """Draw the solution path with an . """
        for i, cell in enumerate(path):
            if cell in (self.data.entry, self.data.exit):
                continue
            cy, cx = cell.y * 2 + 1, cell.x * 2 + 1
            self.canvas[cy][cx] = '.'

            if i > 0:
                prev = path[i - 1]
                py, px = prev.y * 2 + 1, prev.x * 2 + 1
                my, mx = (cy + py) // 2, (cx + px) // 2
                if self.canvas[my][mx] == ' ':
                    self.canvas[my][mx] = '.'
