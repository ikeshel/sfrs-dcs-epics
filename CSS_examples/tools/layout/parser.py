from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path


BOARD_PREFIX = "emdiBOARD"

def get_text(widget: ET.Element, tag: str) -> str  | None:
    element = widget.find(tag)

    if element is None:
        return None

    return element.text


def parse_board_widgets(bob_file: Path) -> list[dict[str, str | int]]:
    tree = ET.parse(bob_file)
    root = tree.getroot()

    boards: list[dict[str, str | int]] = []

    for widget in root.iter("widget"):
        name = get_text(widget, "name")

        if name is None:
            continue

        if not name.startswith(BOARD_PREFIX):
            continue

        x = get_text(widget, "x")
        y = get_text(widget, "y")
        width = get_text(widget, "width")
        height = get_text(widget, "height")

        if None in (x, y, width, height):
            raise ValueError(
                f"Widget '{name}' is missing x, y, width, or height."
            )
    
        boards.append(
            {
                "name": name,
                "x": int(x),
                "y": int(y),
                "width": int(width),
                "height": int(height),
            }
        )

    boards.sort(
        key=lambda board: int(str(board["name"]).replace(BOARD_PREFIX, ""))
    )

    return boards


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Read SCIFI board positions from a Phoebus .bob file."
    )

    parser.add_argument(
        "bob_file",
        type=Path,
        help="Path to BoardTemplate_SCIFI.bob",
    )

    args = parser.parse_args()

    bob_file: Path = args.bob_file

    if not bob_file.exists():
        raise FileNotFoundError(
            f"BOB file does not exist: {bob_file}"
        )

    boards = parse_board_widgets(bob_file)

    print(f"\nFile: {bob_file}")
    print(f"Found {len(boards)} board widgets. \n")

    for board in boards:
        print(
            f"{board['name']}: "
            f"x={board['x']}, "
            f"y={board['y']}, "
            f"width={board['width']}, "
            f"height={board['height']}"
        )


if __name__ == "__main__":
    main()