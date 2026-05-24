"""CLI rendering for the maze."""

from .models import EAST, NORTH, SOUTH, WEST, Coord, MazeData


class MazeRenderer:
    """Handles visualization of the maze using background colors."""

    def __init__(self, data: MazeData) -> None:
        self.data = data
        self.w = data.width * 2 + 1
        self.h = data.height * 2 + 1
        self.canvas: list[list[str]] = [
            ["W" for _ in range(self.w)] for _ in range(self.h)
        ]

    def render(
        self,
        path: list[Coord],
        show_solution: bool = False,
        color: str = "",
    ) -> str:
        """Render the complete maze as an ANSI string."""
        self._carve_paths()
        self._draw_cells()
        if show_solution and path:
            self._draw_path(path)

        reset = "\033[0m"
        if color:
            wall_fmt = f"{color}\033[7m  {reset}"
            block_42_color = color
            entry_color = color
            exit_color = color
            path_color = color
        else:
            wall_fmt = f"\033[34m\033[7m  {reset}"
            block_42_color = "\033[36m"
            entry_color = "\033[93m"
            exit_color = "\033[91m"
            path_color = "\033[93m"

        lines: list[str] = []

        for row in self.canvas:
            line_parts = []
            for cell in row:
                if cell == "W":
                    line_parts.append(wall_fmt)
                elif cell == " ":
                    line_parts.append("  ")
                elif cell == "4":
                    line_parts.append(f"{block_42_color}░░{reset}")
                elif cell == "S":
                    line_parts.append(f"{entry_color}╰➤{reset}")
                elif cell == "E":
                    line_parts.append(f"{exit_color}➜]{reset}")
                elif cell == ".":
                    line_parts.append(f"{path_color}••{reset}")
            lines.append("".join(line_parts))

        return "\n".join(lines)

    def _carve_paths(self) -> None:
        """Remove walls where paths exist."""
        for y in range(self.data.height):
            for x in range(self.data.width):
                cy, cx = y * 2 + 1, x * 2 + 1
                cell_coord = Coord(x, y)

                if cell_coord not in self.data.closed_cells:
                    self.canvas[cy][cx] = " "

                cell_walls = self.data.grid[y][x]
                if not (cell_walls & NORTH):
                    self.canvas[cy - 1][cx] = " "
                if not (cell_walls & SOUTH):
                    self.canvas[cy + 1][cx] = " "
                if not (cell_walls & WEST):
                    self.canvas[cy][cx - 1] = " "
                if not (cell_walls & EAST):
                    self.canvas[cy][cx + 1] = " "

    def _draw_cells(self) -> None:
        """Draw the 42 pattern, entry, and exit markers."""
        for cell in self.data.closed_cells:
            self.canvas[cell.y * 2 + 1][cell.x * 2 + 1] = "4"

        ex, ey = self.data.entry.x * 2 + 1, self.data.entry.y * 2 + 1
        self.canvas[ey][ex] = "S"

        xx, xy = self.data.exit.x * 2 + 1, self.data.exit.y * 2 + 1
        self.canvas[xy][xx] = "E"

    def _draw_path(self, path: list[Coord]) -> None:
        """Draw the solution path."""
        for i, cell in enumerate(path):
            cy, cx = cell.y * 2 + 1, cell.x * 2 + 1

            if cell not in (self.data.entry, self.data.exit):
                self.canvas[cy][cx] = "."

            if i > 0:
                prev = path[i - 1]
                py, px = prev.y * 2 + 1, prev.x * 2 + 1
                my, mx = (cy + py) // 2, (cx + px) // 2
                if self.canvas[my][mx] == " ":
                    self.canvas[my][mx] = "."
