"""Gestisce formattazione ed esportazione dei dati del labirinto."""

from .models import MazeData


class MazeExporter:
    """Esporta mazedata su un file."""

    def __init__(self, data: MazeData) -> None:
        """Salva i dati da convertire/esportare."""
        self.data = data

    def to_hex_rows(self) -> list[str]:
        """Converte le righe in stringhe di cifre esadecimali."""
        rows: list[str] = []
        for y in range(self.data.height):
            chars = [
                format(self.data.grid[y][x], "X")
                for x in range(self.data.width)
            ]
            rows.append("".join(chars))
        return rows

    def dump_to_file(self, file_path: str, path_steps: list[str]) -> None:
        """Scrive file output con labirinto, entry/exit e percorso."""
        steps_str = "".join(path_steps)
        with open(file_path, "w", encoding="utf-8") as out:
            for row in self.to_hex_rows():
                out.write(f"{row}\n")
            out.write("\n")
            out.write(f"{self.data.entry.x},{self.data.entry.y}\n")
            out.write(f"{self.data.exit.x},{self.data.exit.y}\n")
            out.write(f"{steps_str}\n")
