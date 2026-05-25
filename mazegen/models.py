"""Strutture dati e costanti necessarie per il funzionamento di mazegen."""

from dataclasses import dataclass, field
from typing import Final

NORTH: Final[int] = 1
EAST: Final[int] = 2
SOUTH: Final[int] = 4
WEST: Final[int] = 8
ALL_WALLS: Final[int] = NORTH | EAST | SOUTH | WEST
EXTRA_OPENINGS_DIVISOR: Final[int] = 6

DIRS: Final[list[tuple[int, int, int, int, str]]] = [
    (0, -1, NORTH, SOUTH, "N"),
    (1, 0, EAST, WEST, "E"),
    (0, 1, SOUTH, NORTH, "S"),
    (-1, 0, WEST, EAST, "W"),
]


@dataclass(frozen=True)
class Coord:
    """Coordinate delle celle all'interno della matrice del labirinto."""

    x: int
    y: int


@dataclass
class MazeData:
    """Stato del labirinto, è condiviso tra le varie classi."""

    width: int
    height: int
    entry: Coord
    exit: Coord
    grid: list[list[int]] = field(default_factory=list)
    closed_cells: set[Coord] = field(default_factory=set)

    def inside(self, x: int, y: int) -> bool:
        """Check per assicurarsi che le coordinate non siano out of bounds."""
        return 0 <= x < self.width and 0 <= y < self.height
