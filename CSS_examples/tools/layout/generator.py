from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml


BOARD_PREFIX= "emdiBOARD"

def load_config(config_file: Path) -> dict:
    with config_file.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError("YAML configuration must contain a mapping.")

    return config

def calculate_board_positions(config: dict) -> dict[str, tuple[int, int]]:
    board_width = int(config["board"]["width"])
    board_height = int(config["board"]["height"])

    layout = config["layout"]

    positions: dict[str, tuple[int, int]] = {}

    # TOP
    top = layout["top"]

    for index, board_number in enumerate(top["boards"]):
        x = int(top["start_x"]) + index * (
            board_width + int(top["gap"])
        )
        y = int(top["y"])

        positions[f"{BOARD_PREFIX}{board_number}"] = (x, y)

    # LEFT
    left = layout["left"]

    for index, board_number in enumerate(left["boards"]):
        x = int(left["x"])
        y = int(left["start_y"]) + index * (
            board_height + int(left["gap"])
        )

        positions[f"{BOARD_PREFIX}{board_number}"] = (x, y)

    # BOTTOM
    bottom = layout["bottom"]

    for index, board_number in enumerate(bottom["boards"]):
        x = int(bottom["start_x"]) + index * (
            board_width + int(bottom["gap"])
        )
        y = int(bottom["y"])

        positions[f"{BOARD_PREFIX}{board_number}"] = (x, y)

    # RIGHT
    right = layout["right"]

    for index, board_number in enumerate(right["boards"]):
        x = int(right["x"])
        y = int(right["start_y"]) + index * (
            board_height + int(right["gap"])
        )

        positions[f"{BOARD_PREFIX}{board_number}"] = (x, y)

    return positions


def calculate_plsci_positions(
    config: dict,
    template_name: str,
) -> dict[str, tuple[int, int]]:
    board_width = int(config["board"]["width"])
    board_height = int(config["board"]["height"])

    template = config["templates"][template_name]
    layout = template["layout"]

    positions: dict[str, tuple[int, int]] = {}

    for group_name, group in layout.items():
        boards = group["boards"]

        if "start_x" in group:
            start_x = int(group["start_x"])
            y = int(group["y"])
            gap = int(group.get("gap", 0))

            for index, board_number in enumerate(boards):
                x = start_x + index * (board_width + gap)

                positions[f"{BOARD_PREFIX}{board_number}"] = (x, y)

        elif "start_y" in group:
            x = int(group["x"])
            start_y = int(group["start_y"])
            gap = int(group.get("gap", 0))

            for index, board_number in enumerate(boards):
                y = start_y + index * (board_height + gap)

                positions[f"{BOARD_PREFIX}{board_number}"] = (x, y)

        else:
            raise ValueError(
                f"PLSCI layout group '{group_name}' "
                "must contain either start_x or start_y."
            )

    return positions


def calculate_music_positions(
    config: dict,
    template_name: str,
) -> dict[str, tuple[int, int]]:
    field_cage_width = int(config["field_cage"]["width"])

    template = config["templates"][template_name]
    row = template["layout"]["row"]

    widgets = row["widgets"]
    start_x = int(row["start_x"])
    y = int(row["y"])
    gap = int(row["gap"])

    positions: dict[str, tuple[int, int]] = {}

    for index, widget_name in enumerate(widgets):
        x = start_x + index * (
            field_cage_width + gap
        )

        positions[widget_name] = (x, y)

    return positions


def update_board_template(
    source_file: Path,
    output_file: Path,
    config: dict,
    positions: dict[str, tuple[int, int]],
) -> None:
    tree = ET.parse(source_file)
    root = tree.getroot()

    board_width = int(config["board"]["width"])
    board_height = int(config["board"]["height"])

    expected_widgets = set(positions)
    modified_widgets: set[str] = set()

    for widget in root.iter("widget"):
        name_element = widget.find("name")

        if name_element is None or name_element.text is None:
            continue

        name = name_element.text

        if name not in expected_widgets:
            continue


        x_element = widget.find("x")
        y_element = widget.find("y")
        width_element = widget.find("width")
        height_element = widget.find("height")

        if (
            x_element is None
            or y_element is None
            or width_element is None
            or height_element is None
        ):
            raise ValueError(
                f"Widget '{name}' is missing position or size properties."
            )

        new_x, new_y = positions[name]

        old_x = x_element.text
        old_y = y_element.text

        x_element.text = str(new_x)
        y_element.text = str(new_y)
        width_element.text = str(board_width)
        height_element.text = str(board_height)

        modified_widgets.add(name)

        print(
            f"{name}: "
            f"({old_x}, {old_y}) -> ({new_x}, {new_y})"
        )

    missing_widgets = expected_widgets - modified_widgets

    if missing_widgets:
        missing = ", ".join(sorted(missing_widgets))

        raise ValueError(
            f"Some configured widgets were not found in the BOB file: {missing}"
        )

    tree.write(
        output_file,
        encoding="UTF-8",
        xml_declaration=True,
    )

    print()
    print(f"Updated {len(modified_widgets)} board widgets.")
    print(f"Generated file: {output_file}")


def update_plsci_template(
    source_file: Path,
    output_file: Path,
    config: dict,
    template_name: str,
    positions: dict[str, tuple[int, int]],
) -> None:
    tree = ET.parse(source_file)
    root = tree.getroot()

    board_width = int(config["board"]["width"])
    board_height = int(config["board"]["height"])

    template = config["templates"][template_name]
    picture_config = template["picture"]

    expected_widgets = set(positions)
    modified_widgets: set[str] = set()

    picture_updated = False

    for widget in root.iter("widget"):
        name_element = widget.find("name")

        if name_element is None or name_element.text is None:
            continue

        name = name_element.text

        if name in expected_widgets:
            x_element = widget.find("x")
            y_element = widget.find("y")
            width_element = widget.find("width")
            height_element = widget.find("height")

            # Phoebus may omit x/y when the value is 0.
            if x_element is None:
                x_element = ET.SubElement(widget, "x")

            if y_element is None:
                y_element = ET.SubElement(widget, "y")

            if width_element is None:
                width_element = ET.SubElement(widget, "width")

            if height_element is None:
                height_element = ET.SubElement(widget, "height")

            new_x, new_y = positions[name]

            old_x = x_element.text or "0"
            old_y = y_element.text or "0"

            x_element.text = str(new_x)
            y_element.text = str(new_y)
            width_element.text = str(board_width)
            height_element.text = str(board_height)

            modified_widgets.add(name)

            print(
                f"{name}: "
                f"({old_x}, {old_y}) -> ({new_x}, {new_y})"
            )

        if name == picture_config["widget"]:
            properties = {
                "x": int(picture_config["x"]),
                "y": int(picture_config["y"]),
                "width": int(picture_config["width"]),
                "height": int(picture_config["height"]),
            }

            for property_name, property_value in properties.items():
                element = widget.find(property_name)

                if element is None:
                    element = ET.SubElement(widget, property_name)

                element.text = str(property_value)

            picture_updated = True

            print(
                f"{name}: picture geometry -> "
                f"x={picture_config['x']}, "
                f"y={picture_config['y']}, "
                f"width={picture_config['width']}, "
                f"height={picture_config['height']}"
            )

    missing_widgets = expected_widgets - modified_widgets

    if missing_widgets:
        missing = ", ".join(sorted(missing_widgets))

        raise ValueError(
            f"Some configured PLSCI widgets were not found: {missing}"
        )

    if not picture_updated:
        raise ValueError(
            f"Picture widget '{picture_config['widget']}' was not found."
        )

    tree.write(
        output_file,
        encoding="UTF-8",
        xml_declaration=True,
    )

    print()
    print(
        f"Generated PLSCI template '{template_name}': "
        f"{output_file}"
    )


def update_music_template(
    source_file: Path,
    output_file: Path,
    config: dict,
    template_name: str,
    positions: dict[str, tuple[int, int]],
) -> None:
    tree = ET.parse(source_file)
    root = tree.getroot()

    field_cage_width = int(
        config["field_cage"]["width"]
    )
    field_cage_height = int(
        config["field_cage"]["height"]
    )

    expected_widgets = set(positions)
    modified_widgets: set[str] = set()

    for widget in root.iter("widget"):
        name_element = widget.find("name")

        if name_element is None or name_element.text is None:
            continue

        name = name_element.text

        if name not in expected_widgets:
            continue

        x_element = widget.find("x")
        y_element = widget.find("y")
        width_element = widget.find("width")
        height_element = widget.find("height")

        # Phoebus may omut properties whose value is 0.
        if x_element is None:
            x_element = ET.SubElement(widget, "x")

        if y_element is None:
            y_element = ET.SubElement(widget, "y")

        if width_element is None:
            width_element = ET.SubElement(widget, "width")

        if height_element is None:
            height_element = ET.SubElement(widget, "height")

        new_x, new_y = positions[name]

        old_x = x_element.text or "0"
        old_y = y_element.text or "0"

        x_element.text = str(new_x)
        y_element.text = str(new_y)
        width_element.text = str(field_cage_width)
        height_element.text = str(field_cage_height)

        modified_widgets.add(name)

        print(
            f"{name}: "
            f"({old_x}, {old_y}) -> "
            f"({new_x}, {new_y})"
        )

    missing_widgets = expected_widgets - modified_widgets

    if missing_widgets:
        missing = ", ".join(sorted(missing_widgets))

        raise ValueError(
            f"Some configured MUSIC widgets "
            f"were not found: {missing}"
        )

    tree.write(
        output_file,
        encoding="UTF-8",
        xml_declaration=True,
    )

    print()
    print(
        f"Generated MUSIC template "
        f"'{template_name}': {output_file}"
    )


def generate_plsci_templates(
    config_file: Path,
    six_source: Path,
    six_output: Path,
    eight_source: Path,
    eight_output: Path,
) -> None:
    config = load_config(config_file)

    print("\nPLSCI 6-board template\n")

    six_positions = calculate_plsci_positions(
        config=config,
        template_name="six_board",
    )

    for name, (x, y) in six_positions.items():
        print(f"{name}: x={x}, y={y}")
    
    print()

    update_plsci_template(
        source_file=six_source,
        output_file=six_output,
        config=config,
        template_name="six_board",
        positions=six_positions,
    )

    print("\nPLSCI 8-board template\n")

    eight_positions = calculate_plsci_positions(
        config=config,
        template_name="eight_board",
    )

    for name, (x, y) in eight_positions.items():
        print(f"{name}: x={x}, y={y}")

    print()

    update_plsci_template(
        source_file=eight_source,
        output_file=eight_output,
        config=config,
        template_name="eight_board",
        positions=eight_positions,
    )


def generate_music_templates(
    config_file: Path,
    two_source: Path,
    two_output: Path,
    three_source: Path,
    three_output: Path,
) -> None:
    config = load_config(config_file)

    print("\nMUSIC 2-FC template\n")

    two_positions = calculate_music_positions(
        config=config,
        template_name="two_fc",
    )

    for name, (x, y) in two_positions.items():
        print(f"{name}: x={x}, y={y}")

    print()

    update_music_template(
        source_file=two_source,
        output_file=two_output,
        config=config,
        template_name="two_fc",
        positions=two_positions,
    )

    print("\nMUSIC 3-FC template\n")

    three_positions = calculate_music_positions(
        config=config,
        template_name="three_fc",
    )

    for name, (x, y) in three_positions.items():
        print(f"{name}: x={x}, y={y}")

    print()

    update_music_template(
        source_file=three_source,
        output_file=three_output,
        config=config,
        template_name="three_fc",
        positions=three_positions,
    )


def update_main_bob(
    source_file: Path,
    output_file: Path,
    config_file: Path,
) -> None:
    config = load_config(config_file)

    tree = ET.parse(source_file)
    root = tree.getroot()

    screen_config = config["screen"]
    tabs_config = config["tabs"]

    # Update display size
    width_element = root.find("width")
    height_element = root.find("height")

    if width_element is None or height_element is None:
        raise ValueError("Main.bob is missing display width or height.")

    width_element.text = str(screen_config["width"])
    height_element.text = str(screen_config["height"])

    # Find navtabs widget
    navtabs_widget = None

    for widget in root.iter("widget"):
        widget_type = (widget.get("type") or "").strip()

        name_element = widget.find("name")

        name = (
            (name_element.text or "").strip()
            if name_element is not None
            else ""
        )

        target_name = str(tabs_config["widget"]).strip()

        if (
            widget_type == "navtabs"
            and name == target_name
        ):
            navtabs_widget = widget
            break

    if navtabs_widget is None:
        raise ValueError(
            f"Navtabs widget '{tabs_config['widget']}' was not found."
        )

    # Update navtabs geometry
    geometry = {
        "width": int(tabs_config["width"]),
        "height": int(tabs_config["height"]),
        "tab_width": int(tabs_config["tab_width"]),
    }

    for property_name, value in geometry.items():
        element = navtabs_widget.find(property_name)

        if element is None:
            element = ET.SubElement(
                navtabs_widget,
                property_name,
            )

        element.text = str(value)

    tabs_element = navtabs_widget.find("tabs")

    if tabs_element is None:
        raise ValueError(
            f"Navtabs widget '{tabs_config['widget']}' "
            "does not contain <tabs>."
        )

    configured_tabs = tabs_config["items"]

    existing_tabs: dict[str, ET.Element] = {}

    for tab in tabs_element.findall("tab"):
        name_element = tab.find("name")

        if (
            name_element is not None
            and name_element.text is not None
        ):
            existing_tabs[name_element.text] = tab

    for tab_config in configured_tabs:
        tab_name = tab_config["name"]
        tab_file = tab_config["file"]

        if tab_name not in existing_tabs:
            raise ValueError(
                f"Configured tab '{tab_name}' "
                "was not found in Main.bob."
            )

        tab = existing_tabs[tab_name]

        file_element = tab.find("file")

        if file_element is None:
            file_element = ET.SubElement(
                tab,
                "file",
            )

        old_file = file_element.text or ""
        file_element.text = str(tab_file)

        print(
            f"{tab_name}: "
            f"{old_file} -> {tab_file}"
        )

    tree.write(
        output_file,
        encoding="UTF-8",
        xml_declaration=True,
    )

    print()
    print(f"Generated Main.bob file: {output_file}.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate CS Studio layouts from the master YAML configuration."
        )
    )

    parser.add_argument(
        "config_file",
        type=Path,
        help="Path to the master layout.yaml file",
    )

    args = parser.parse_args()

    config_file: Path = args.config_file

    if not config_file.exists():
        raise FileNotFoundError(
            f"Master configuration file does not exist: {config_file}"
        )

    generate_all(config_file)


def get_generated_path(source_file: Path) -> Path:
    return source_file.with_name(
        f"{source_file.stem}_GENERATED{source_file.suffix}"
    )



def generate_all(master_config_file: Path) -> None:
    master_config = load_config(master_config_file)

    # Layout/layout.yaml -> project root
    layout_dir = master_config_file.parent
    project_root = layout_dir.parent

    print("\n==========================")
    print("CS Studio Layout Generation")
    print("==========================\n")

    # -----------------------------------
    # SCIFI
    # -----------------------------------

    print("Generating SCIFI ...\n")

    scifi_config_file = layout_dir / master_config["detectors"]["scifi"]["config"]
    scifi_config = load_config(scifi_config_file)

    scifi_source = project_root / scifi_config["source"]["board_template"]
    scifi_output = get_generated_path(scifi_source)

    scifi_positions = calculate_board_positions(scifi_config)

    update_board_template(
        source_file=scifi_source,
        output_file=scifi_output,
        config=scifi_config,
        positions=scifi_positions,
    )

    # -----------------------------------
    # PLSCI
    # -----------------------------------

    print("\nGenerating PLSCI...\n")

    plsci_config_file = layout_dir / master_config["detectors"]["plsci"]["config"]
    plsci_config = load_config(plsci_config_file)

    six_source = (
        project_root
        / plsci_config["templates"]["six_board"]["source"]
    )

    eight_source = (
        project_root
        / plsci_config["templates"]["eight_board"]["source"]
    )

    generate_plsci_templates(
        config_file=plsci_config_file,
        six_source=six_source,
        six_output=get_generated_path(six_source),
        eight_source=eight_source,
        eight_output=get_generated_path(eight_source),
    )

    # -----------------------------------
    # MUSIC
    # -----------------------------------

    print("\nGenerating MUSIC...\n")

    music_config_file = layout_dir / master_config["detectors"]["music"]["config"]
    music_config = load_config(music_config_file)

    two_source = (
        project_root
        / music_config["templates"]["two_fc"]["source"]
    )

    three_source = (
        project_root
        / music_config["templates"]["three_fc"]["source"]
    )

    generate_music_templates(
        config_file=music_config_file,
        two_source=two_source,
        two_output=get_generated_path(two_source),
        three_source=three_source,
        three_output=get_generated_path(three_source),
    )

    # -----------------------------------
    # MAIN
    # -----------------------------------

    print("\nGenerating Main...\n")

    main_config_file = layout_dir / master_config["main"]["config"]
    main_config = load_config(main_config_file)

    main_source = project_root / main_config["source"]
    main_output = get_generated_path(main_source)

    update_main_bob(
        source_file=main_source,
        output_file=main_output,
        config_file=main_config_file,
    )

    # -----------------------------------
    # COMPLETE
    # -----------------------------------

    print("\n========================================")
    print("Layout generation completed successfully.")
    print("========================================\n")

    print("\nGenerated files:")

    print(f"    SCIFI : {scifi_output}")
    print(f"    PLSCI : {get_generated_path(six_source)}")
    print(f"    PLSCI : {get_generated_path(eight_source)}")
    print(f"    MUSIC : {get_generated_path(two_source)}")
    print(f"    MUSIC : {get_generated_path(three_source)}")
    print(f"    MAIN : {main_output}")


if __name__ == "__main__":
    main()