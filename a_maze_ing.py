"""Main script for the A-Maze-ing mandatory project."""

import sys
from dataclasses import dataclass

from mazegen import Coord, MazeGenerator


@dataclass
class MazeConfig:
    """Modello dati per la configurazione del labirinto."""

    width: int
    height: int
    entry: Coord
    exit: Coord
    output_file: str
    perfect: bool
    seed: int | None = None
    include_42: bool = True


class ConfigParser:
    """Gestisce la lettura e la validazione del file config.txt."""

    REQUIRED_KEYS = {
        "WIDTH",
        "HEIGHT",
        "ENTRY",
        "EXIT",
        "OUTPUT_FILE",
        "PERFECT",
    }

    def __init__(self, path: str) -> None:
        self.path = path

    def parse(self) -> MazeConfig:
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
        )

    def _read_file(self) -> dict[str, str]:
        raw: dict[str, str] = {}
        with open(self.path, "r", encoding="utf-8") as cfg:
            for line_num, line in enumerate(cfg, start=1):
                text = line.strip()
                if not text or text.startswith("#"):
                    continue
                if "=" not in text:
                    raise ValueError(
                        f"Invalid syntax on line {line_num}: missing '='"
                    )
                key, value = text.split("=", 1)
                raw[key.strip().upper()] = value.strip()
        return raw

    def _validate_keys(self, raw: dict[str, str]) -> None:
        missing = self.REQUIRED_KEYS - raw.keys()
        if missing:
            raise ValueError(
                f"Missing required config keys: {', '.join(sorted(missing))}"
            )

    def _parse_bool(self, value: str) -> bool:
        lower = value.strip().lower()
        if lower in {"true", "1", "yes", "y", "on"}:
            return True
        if lower in {"false", "0", "no", "n", "off"}:
            return False
        raise ValueError(f"Invalid boolean value: {value!r}")

    def _parse_coord(self, value: str, key: str) -> Coord:
        parts = [item.strip() for item in value.split(",")]
        if len(parts) != 2:
            raise ValueError(f"{key} must have format x,y")
        try:
            x, y = int(parts[0]), int(parts[1])
        except ValueError as exc:
            raise ValueError(f"{key} must be integers") from exc
        return Coord(x, y)


class MazeCLI:
    """Interfaccia a riga di comando per l'esplorazione del labirinto."""

    WALL_COLORS = [
        "",
        "\033[31m",
        "\033[32m",
        "\033[34m",
        "\033[36m",
        "\033[33m",
    ]

    def __init__(self, generator: MazeGenerator) -> None:
        self.generator = generator
        self.show_solution = False
        self.color_idx = 0

    def run(self) -> None:
        while True:
            print(
                "\n"
                + self.generator.render_ascii(
                    show_solution=self.show_solution,
                    wall_color=self.WALL_COLORS[self.color_idx],
                )
            )
            print(
                "\nCommands: [r]egenerate, [s]how/hide path, [c]olor, [q]uit"
            )
            try:
                cmd = input("> ").strip().lower()
                if cmd in {"q", "quit", "exit"}:
                    break
                self._handle_command(cmd)
            except (EOFError, KeyboardInterrupt):
                print("\nExiting.")
                break

    def _handle_command(self, cmd: str) -> None:
        if cmd in {"s", "show"}:
            self.show_solution = not self.show_solution
        elif cmd in {"c", "color", "colour"}:
            self.color_idx = (self.color_idx + 1) % len(self.WALL_COLORS)
        elif cmd in {"r", "regen", "regenerate"}:
            try:
                self.generator.regenerate()
                for warning in self.generator.warnings:
                    print(f"Warning: {warning}")
            except ValueError as exc:
                print(f"Error during regeneration: {exc}")


def main(argv: list[str]) -> int:
    """Program entry point."""
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
        )
        generator.generate()
        generator.dump_to_file(config.output_file)

        print(f"Maze written to: {config.output_file}")
        for warning in generator.warnings:
            print(f"Warning: {warning}")

        MazeCLI(generator).run()
        return 0
    except FileNotFoundError:
        print(f"Error: configuration file not found: {argv[1]}")
    except ValueError as exc:
        print(f"Error: {exc}")
    except OSError as exc:
        print(f"Error: file operation failed: {exc}")
    except Exception as exc:
        print(f"Unexpected error: {exc}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
