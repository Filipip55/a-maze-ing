"""Interfaccia per mazegen e le classi al suo interno."""

from .exporter import MazeExporter
from .generator import CoreGenerator
from .models import ALL_WALLS, EAST, NORTH, SOUTH, WEST, Coord, MazeData
from .renderer import MazeRenderer
from .solver import MazeSolver

__all__ = ["MazeGenerator", "Coord"]


class MazeGenerator:
    """Classe principale che coordina generazione, solve, export e render."""

    def __init__(
        self,
        width: int,
        height: int,
        entry: tuple[int, int],
        exit_: tuple[int, int],
        seed: int | None = None,
        perfect: bool = True,
        include_42: bool = True,
        algorithm: str = "backtracker",
    ) -> None:
        """Inizializza il coordinatore del labirinto."""
        self.entry = Coord(*entry)
        self.exit = Coord(*exit_)
        self.seed = seed
        self.algorithm = algorithm
        self.generator = CoreGenerator(
            width,
            height,
            self.entry,
            self.exit,
            seed,
            perfect,
            include_42,
            algorithm,
        )
        self.data: MazeData | None = None
        self.warnings: list[str] = []

    def generate(self) -> None:
        """Avvia generazione del labirinto."""
        self.generator.seed = self.seed
        self.generator.algorithm = self.algorithm
        self.generator.rng.seed(self.seed)
        self.data = self.generator.generate()
        self.warnings = self.generator.warnings

    def regenerate(self, new_seed: int | None = None) -> None:
        """Rigenera il labirinto con un nuovo seed opzionale."""
        if new_seed is not None:
            self.seed = new_seed
        self.generator.rng.seed(self.seed)
        self.generate()

    def shortest_path(self) -> list[str]:
        """Ritorna il percorso più breve tra entrata e uscita del labirinto."""
        if not self.data:
            raise RuntimeError("Generate the maze before solving.")
        return MazeSolver(self.data).solve()

    def to_hex_rows(self) -> list[str]:
        """Ritorna righe del labirinto codificate in esadecimale."""
        if not self.data:
            raise RuntimeError("Generate the maze before exporting.")
        return MazeExporter(self.data).to_hex_rows()

    def dump_to_file(self, file_path: str) -> None:
        """Scrive il labirinto e i suoi dati in un file di testo."""
        if not self.data:
            raise RuntimeError("Generate the maze before exporting.")
        path = self.shortest_path()
        MazeExporter(self.data).dump_to_file(file_path, path)

    def render_ascii(
        self, show_solution: bool = False, wall_color: str = ""
    ) -> str:
        """Stampa il labirinto sulla CLI."""
        if not self.data:
            raise RuntimeError("Generate the maze before rendering.")
        path_coords = (
            MazeSolver(self.data).get_path_coords() if show_solution else []
        )
        return MazeRenderer(self.data).render(
            path_coords, show_solution, wall_color
        )

    def set_seed(self, seed: int) -> None:
        """Aggiorna il seed usato nelle prossime generazioni."""
        self.seed = seed

    def set_algorithm(self, algorithm: str) -> None:
        """Aggiorna l'algoritmo usato nelle prossime generazioni."""
        if algorithm not in CoreGenerator.SUPPORTED_ALGORITHMS:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        self.algorithm = algorithm

    def generation_frames(
        self, show_solution: bool, wall_color: str, max_frames: int = 60
    ) -> list[str]:
        """Costruisce frame ASCII per animare la generazione corrente."""
        if not self.data:
            raise RuntimeError("Generate the maze before rendering.")

        steps = self.generator.last_open_steps
        if not steps:
            return [self.render_ascii(show_solution, wall_color)]

        stride = max(1, len(steps) // max_frames)
        temp = MazeData(
            width=self.data.width,
            height=self.data.height,
            entry=self.data.entry,
            exit=self.data.exit,
            grid=[
                [ALL_WALLS for _ in range(self.data.width)]
                for _ in range(self.data.height)
            ],
            closed_cells=set(self.data.closed_cells),
        )
        for blocked in temp.closed_cells:
            temp.grid[blocked.y][blocked.x] = ALL_WALLS

        frames: list[str] = []
        for index, (current, nxt) in enumerate(steps, start=1):
            self._open_step_in_grid(temp, current, nxt)
            if index % stride == 0 or index == len(steps):
                path_coords = (
                    MazeSolver(self.data).get_path_coords()
                    if show_solution
                    else []
                )
                frames.append(
                    MazeRenderer(temp).render(
                        path_coords,
                        show_solution,
                        wall_color,
                    )
                )
        return frames

    def _open_step_in_grid(
        self, data: MazeData, current: Coord, nxt: Coord
    ) -> None:
        """Applica un singolo passo di apertura a una griglia temporanea."""
        dx = nxt.x - current.x
        dy = nxt.y - current.y
        if dx == 1:
            data.grid[current.y][current.x] &= ~EAST
            data.grid[nxt.y][nxt.x] &= ~WEST
        elif dx == -1:
            data.grid[current.y][current.x] &= ~WEST
            data.grid[nxt.y][nxt.x] &= ~EAST
        elif dy == 1:
            data.grid[current.y][current.x] &= ~SOUTH
            data.grid[nxt.y][nxt.x] &= ~NORTH
        elif dy == -1:
            data.grid[current.y][current.x] &= ~NORTH
            data.grid[nxt.y][nxt.x] &= ~SOUTH
