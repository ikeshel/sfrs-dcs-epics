from __future__ import annotations

import argparse
import copy
import xml.etree.ElementTree as ET
from pathlib import Path


TARGET_BOARDS = {
    "emdiBOARD1",
    "emdiBOARD2",
    "emdiBOARD3",
    "emdiBOARD4",
    "emdiBOARD5",
    "emdiBOARD6",
}

Y_OFFSET = 30


def get_text(widget: ET.Element, tag: str) -> str | None:
    element = widget.find(tag)

    if element is None:
        return None

    return element.text


def move_target_boards(
    source_file: Path,
    output_file: Path,
) -> None:
    tree = ET.parse(source_file)
    root = tree.getroot()

    modified_count = 0

    for widget in root.iter("widget"):
        name = get_text(widget, "name")

        if name not in TARGET_BOARDS:
            continue

        y_element = widget.find("y")

        if y_element is None or y_element.text is None:
            raise ValueError(
                f"Widget '{name}' does not contain a valid y property."
            )

        old_y = int(y_element.text)
        new_y = old_y + Y_OFFSET

        y_element.text = str(new_y)

        print(
            f"{name}: "
            f"y={old_y} -> y={new_y}"
        )

        modified_count += 1

    if modified_count != len(TARGET_BOARDS):
        raise ValueError(
            f"Expected to modify {len(TARGET_BOARDS)} boards, "
            f"but modified {modified_count}."
        )

    tree.write(
        output_file,
        encoding="UTF-8",
        xml_declaration=True,
    )

    print()
    print(f"Modified {modified_count} board widgets.")
    print(f"Saved test file: {output_file}")

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Create a test Phoebus .bob file with "
            "SCIFI top-row boards moved down."
        )
    )

    parser.add_argument(
        "source_file",
        type=Path,
        help="Path to the original BoardTemplate_SCIFI.bob",
    )

    parser.add_argument(
        "output_file",
        type=Path,
        help="Path for the generated test .bob file",
    )

    args = parser.parse_args()

    source_file: Path = args.source_file
    output_file: Path = args.output_file

    if not source_file.exists():
        raise FileNotFoundError(
            f"Source BOB file does not exist: {source_file}"
        )

    if source_file.resolve() == output_file.resolve():
        raise ValueError(
            "Output file must be different from the source file."
        )

    move_target_boards(
        source_file=source_file,
        output_file=output_file,
    )


if __name__ == "__main__":
    main()