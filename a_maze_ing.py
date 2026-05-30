"""Script principale del progetto."""

import sys
import time
from dataclasses import dataclass

from mazegen import Coord, MazeGenerator
from mazegen.generator import CoreGenerator


@dataclass
class MazeConfig:
    """Dati estratti dal file di configurazione."""

    width: int
    height: int
    entry: Coord
    exit: Coord
    output_file: str
    perfect: bool
    seed: int | None = None
    include_42: bool = True
    algorithm: str = "backtracker"


class ConfigParser:
    """Gestisce lettura, validazione e parsing del file di configurazione."""

    REQUIRED_KEYS = {
        "WIDTH",
        "HEIGHT",
        "ENTRY",
        "EXIT",
        "OUTPUT_FILE",
        "PERFECT",
    }

    def __init__(self, path: str) -> None:
        """Salva il percorso del file di configurazione."""
        self.path = path

    def parse(self) -> MazeConfig:
        """Interpreta il file di configurazione e restituisce MazeConfig."""
        raw = self._read_file()
        self._validate_keys(raw)

        width = int(raw["WIDTH"])
        height = int(raw["HEIGHT"])
        if width <= 0 or height <= 0:
            raise ValueError("WIDTH and HEIGHT must be strictly positive")

        return MazeConfig(
            width=width,
            height=height,
            entry=self._parse_coord(raw["ENTRY"], "ENTRY"),
            exit=self._parse_coord(raw["EXIT"], "EXIT"),
            output_file=raw["OUTPUT_FILE"],
            perfect=self._parse_bool(raw["PERFECT"]),
            seed=int(raw["SEED"]) if "SEED" in raw else None,
            include_42=self._parse_bool(raw.get("INCLUDE_42", "True")),
            algorithm=self._parse_algorithm(
                raw.get("ALGORITHM", "backtracker")
            ),
        )

    def _read_file(self) -> dict[str, str]:
        """Legge il file e restituisce una mappa KEY=VALUE."""
        raw: dict[str, str] = {}
        with open(self.path, "r", encoding="utf-8") as cfg:
            for line_num, line in enumerate(cfg, start=1):
                text = line.strip()
                if not text or text.startswith("#"):
                    continue
                if "=" not in text:
                    raise ValueError(f"Invalid syntax on line {line_num}")
                key, value = text.split("=", 1)
                raw[key.strip().upper()] = value.strip()
        return raw

    def _validate_keys(self, raw: dict[str, str]) -> None:
        """Valida che tutte le chiavi obbligatorie siano presenti."""
        missing = self.REQUIRED_KEYS - raw.keys()
        if missing:
            raise ValueError(f"Missing keys: {', '.join(sorted(missing))}")

    def _parse_bool(self, value: str) -> bool:
        """Converte una stringa in valore booleano."""
        lower = value.strip().lower()
        if lower in {"true", "1", "yes", "y", "on"}:
            return True
        if lower in {"false", "0", "no", "n", "off"}:
            return False
        raise ValueError(f"Invalid boolean value: {value!r}")

    def _parse_coord(self, value: str, key: str) -> Coord:
        """Converte una coordinata x,y in oggetto Coord."""
        parts = [item.strip() for item in value.split(",")]
        if len(parts) != 2:
            raise ValueError(f"{key} must have format x,y")
        try:
            x, y = int(parts[0]), int(parts[1])
        except ValueError as exc:
            raise ValueError(f"{key} must be integers") from exc
        return Coord(x, y)

    def _parse_algorithm(self, value: str) -> str:
        """Valida il nome dell'algoritmo di generazione."""
        algorithm = value.strip().lower()
        if algorithm not in CoreGenerator.SUPPORTED_ALGORITHMS:
            allowed = ", ".join(sorted(CoreGenerator.SUPPORTED_ALGORITHMS))
            raise ValueError(
                f"ALGORITHM must be one of: {allowed}"
            )
        return algorithm


class MazeCLI:
    """Interfaccia CLI con menu e animazioni di generazione."""

    INPUT_ERROR_DELAY = 0.8
    WARNING_DELAY = 1.2
    UNKNOWN_COMMAND_DELAY = 0.6
    FRAME_DELAY = 0.04

    def __init__(self, generator: MazeGenerator, output_file: str) -> None:
        """Inizializza lo stato della CLI."""
        self.generator = generator
        self.output_file = output_file
        self.show_solution = False
        self.wall_color = ""
        self.started = False

    def run(self) -> None:
        """Avvia il loop principale dei comandi utente."""
        while True:
            self._print_screen()
            try:
                cmd = input("> ").strip().lower()
                if cmd in {"q", "quit", "exit"}:
                    break
                self._handle_command(cmd)
            except (EOFError, KeyboardInterrupt):
                print("\nExiting.")
                break

    def _print_screen(self) -> None:
        """Stampa schermata corrente con menu comandi."""
        print("\033[H\033[J", end="")
        if self.started:
            maze = self.generator.render_ascii(
                self.show_solution,
                self.wall_color,
            )
            print(f"{maze}\n")
        else:
            print("=== A-Maze-ing ===")
            print("Premi [1] Start per avviare l'animazione iniziale.\n")

        print(
            "Menu: [1]start [2]regenerate [3]toggle path "
            "[4]seed [5]algorithm [6]rgb color [q]quit"
        )
        print(
            f"Seed={self.generator.seed} "
            f"Algorithm={self.generator.algorithm} "
            f"Path={'ON' if self.show_solution else 'OFF'}"
        )

    def _handle_command(self, cmd: str) -> None:
        """Instrada il comando al relativo handler."""
        if cmd in {"1", "start"}:
            self.started = True
            self._animate_generation()
            return
        if cmd in {"2", "r", "regen", "regenerate"}:
            self._regenerate()
            return
        if cmd in {"3", "s", "show"}:
            self.show_solution = not self.show_solution
            return
        if cmd in {"4", "seed"}:
            self._change_seed()
            return
        if cmd in {"5", "algo", "algorithm"}:
            self._change_algorithm()
            return
        if cmd in {"6", "color", "colour"}:
            self._change_color()
            return
        print("Unknown command.")
        time.sleep(self.UNKNOWN_COMMAND_DELAY)

    def _regenerate(self) -> None:
        """Rigenera il labirinto corrente e aggiorna l'output file."""
        try:
            self.generator.generate()
            self.generator.dump_to_file(self.output_file)
            self.started = True
            self._animate_generation()
            for warning in self.generator.warnings:
                print(f"Warning: {warning}")
                time.sleep(self.WARNING_DELAY)
        except ValueError as exc:
            print(f"Error during regeneration: {exc}")
            time.sleep(self.WARNING_DELAY)

    def _change_seed(self) -> None:
        """Permette all'utente di scegliere un nuovo seed intero."""
        value = input("New seed (integer): ").strip()
        try:
            seed = int(value)
        except ValueError:
            print("Invalid seed.")
            time.sleep(self.INPUT_ERROR_DELAY)
            return
        self.generator.set_seed(seed)
        self._regenerate()

    def _change_algorithm(self) -> None:
        """Permette all'utente di cambiare algoritmo di generazione."""
        options = sorted(CoreGenerator.SUPPORTED_ALGORITHMS)
        print(f"Available algorithms: {', '.join(options)}")
        choice = input("Algorithm: ").strip().lower()
        try:
            self.generator.set_algorithm(choice)
        except ValueError as exc:
            print(exc)
            time.sleep(self.INPUT_ERROR_DELAY)
            return
        self._regenerate()

    def _change_color(self) -> None:
        """Imposta il colore muri con codici RGB o resetta al default."""
        value = input("RGB (es. 120,40,240) oppure empty per default: ")
        value = value.strip()
        if not value:
            self.wall_color = ""
            return
        parts = [part.strip() for part in value.split(",")]
        if len(parts) != 3:
            print("RGB format must be r,g,b.")
            time.sleep(self.INPUT_ERROR_DELAY)
            return
        try:
            r, g, b = (int(part) for part in parts)
        except ValueError:
            print("RGB values must be integers.")
            time.sleep(self.INPUT_ERROR_DELAY)
            return
        invalid = [
            channel for channel in (r, g, b) if channel < 0 or channel > 255
        ]
        if invalid:
            bad_values = ", ".join(str(channel) for channel in invalid)
            print(f"RGB values out of range [0,255]: {bad_values}.")
            time.sleep(self.INPUT_ERROR_DELAY)
            return
        self.wall_color = f"\033[38;2;{r};{g};{b}m"

    def _animate_generation(self) -> None:
        """Riproduce l'animazione della generazione del labirinto."""
        frames = self.generator.generation_frames(
            self.show_solution,
            self.wall_color,
        )
        for frame in frames:
            print("\033[H\033[J", end="")
            print(frame)
            time.sleep(self.FRAME_DELAY)


def main(argv: list[str]) -> int:
    """Punto di avvio del programma."""
    if len(argv) != 2:
        print("Usage: python3 a_maze_ing.py config.txt")
        return 1

    try:
        config = ConfigParser(argv[1]).parse()
        generator = MazeGenerator(
            width=config.width,
            height=config.height,
            entry=(config.entry.x, config.entry.y),
            exit_=(config.exit.x, config.exit.y),
            seed=config.seed,
            perfect=config.perfect,
            include_42=config.include_42,
            algorithm=config.algorithm,
        )
        generator.generate()
        generator.dump_to_file(config.output_file)

        print(f"Maze written to: {config.output_file}")
        for warning in generator.warnings:
            print(f"Warning: {warning}")

        MazeCLI(generator, config.output_file).run()
        return 0
    except Exception as exc:
        print(f"Error: {exc}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
