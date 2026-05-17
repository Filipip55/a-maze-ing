"""Facade for the Maze Generation package."""

from .exporter import MazeExporter
from .generator import CoreGenerator
from .models import Coord, MazeData
from .renderer import MazeRenderer
from .solver import MazeSolver

__all__ = ["MazeGenerator", "Coord"]


class MazeGenerator:
    """Facade orchestrating generation, solving, exporting, and rendering."""

    def __init__(
        self,
        width: int,
        height: int,
        entry: tuple[int, int],
        exit_: tuple[int, int],
        seed: int | None = None,
        perfect: bool = True,
        include_42: bool = True,
    ) -> None:
        self.entry = Coord(*entry)
        self.exit = Coord(*exit_)
        self.seed = seed
        self.generator = CoreGenerator(
            width, height, self.entry, self.exit, seed, perfect, include_42
        )
        self.data: MazeData | None = None
        self.warnings: list[str] = []

    def generate(self) -> None:
        """Trigger the maze generation."""
        self.data = self.generator.generate()
        self.warnings = self.generator.warnings

    def regenerate(self, new_seed: int | None = None) -> None:
        """Regenerate with an optional new seed."""
        if new_seed is not None:
            self.seed = new_seed
            self.generator.rng.seed(new_seed)
        self.generate()

    def shortest_path(self) -> list[str]:
        """Get the solution path."""
        if not self.data:
            raise RuntimeError("Generate the maze before solving.")
        return MazeSolver(self.data).solve()

    def to_hex_rows(self) -> list[str]:
        """Get the hex encoded rows."""
        if not self.data:
            raise RuntimeError("Generate the maze before exporting.")
        return MazeExporter(self.data).to_hex_rows()

    def dump_to_file(self, file_path: str) -> None:
        """Write the maze and solution to a file."""
        if not self.data:
            raise RuntimeError("Generate the maze before exporting.")
        path = self.shortest_path()
        MazeExporter(self.data).dump_to_file(file_path, path)

    def render_ascii(
        self, show_solution: bool = False, wall_color: str = ""
    ) -> str:
        """Render the maze using standard ASCII characters."""
        if not self.data:
            raise RuntimeError("Generate the maze before rendering.")
        path_coords = (
            MazeSolver(self.data).get_path_coords() if show_solution else []
        )
        return MazeRenderer(self.data).render(
            path_coords, show_solution, wall_color
        )
