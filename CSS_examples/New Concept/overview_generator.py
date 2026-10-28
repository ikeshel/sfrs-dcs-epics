from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import yaml


# Project root: the directory containing this script.
PROJECT_ROOT = Path(__file__).resolve().parent

CONFIG_FILE = PROJECT_ROOT / "layout" / "overview.yaml"
OUTPUT_FILE = PROJECT_ROOT / "OVERVIEW" / "Overview_GENERATED.bob"


def load_config():
    """Load and validate the Overview YAML configuration."""
    if not CONFIG_FILE.is_file():
        raise FileNotFoundError(f"Configuration file not found: {CONFIG_FILE}")

    with CONFIG_FILE.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict):
        raise ValueError("overview.yaml must contain a YAML mapping.")
    
    for key in ("source", "cards", "card"):
        if key not in config:
            raise ValueError(f"Missing required configuration key: {key}")
    
    if "overview" not in config["source"]:
        raise ValueError("Missing source.overview in overview.yaml.")
    
    return config


def resolve_project_path(relative_path):
    """Resolve a project-relative path."""
    return PROJECT_ROOT / Path(relative_path)


def find_widgets(root):
    """Index all named widgets by name."""
    widgets = {}

    for widget in root.iter("widget"):
        name_element = widget.find("name")
        if name_element is None or not name_element.text:
            continue
        
        name = name_element.text.strip()

        if name in widgets:
            raise ValueError(f"Duplicate widget name in Overview.bob: {name}")
        
        widgets[name] = widget
    
    return widgets


def set_child_text(element, tag, value):
    """Set a child element's text, creating the element if necessary."""
    child = element.find(tag)

    if child is None:
        child = ET.SubElement(element, tag)
    
    child.text = str(value)


def update_macros(widget, card):
    """Update only the macros declared for this card."""
    macros = widget.find("macros")

    if macros is None:
        macros = ET.SubElement(widget, "macros")
    
    macro_values = { "CHAMBER": card["chamber"]}

    if card["type"] == "SCIFI":
        macro_values["ID"] = card["id"]
    
    for macro_name, macro_value in macro_values.items():
        set_child_text(macros, macro_name, macro_value)


def update_card(widget, card, default_width, default_height):
    """Update one existing embedded card without rebuilding its contents."""
    set_child_text(widget, "file", card["file"])
    set_child_text(widget, "x", card["x"])
    set_child_text(widget, "y", card["y"])
    set_child_text(widget, "width", card.get("width", default_width))
    set_child_text(widget, "height", card.get("height", default_height))

    update_macros(widget, card)


def validate_cards(cards):
    """Check card configuration before modifying the XML tree."""
    names = set()

    for index, card in enumerate(cards, start=1):
        if not isinstance(card, dict):
            raise ValueError(f"Card entry #{index} must be a mapping.")
        
        for key in ("name", "type", "file", "chamber", "x", "y"):
            if key not in card:
                raise ValueError(f"Card entry #{index} is missing '{key}'.")
        
        if card["name"] in names:
            raise ValueError(f"Duplicate card name in YAML: {card['name']}")
        
        names.add(card["name"])

        if card["type"] not in {"SCIFI", "PLSCI", "MUSIC"}:
            raise ValueError(
                f"Unsupported card type '{card['type']}' "
                f"for widget {card['name']}."
            )
        
        if card["type"] == "SCIFI" and "id" not in card:
            raise ValueError(f"SCIFI card {card['name']} is missing 'id'.")


def indent_xml(element, level=0):
    """Pretty-print XML using indentation, compatible with older Python versions."""
    indentation = "\n" + level * "  "

    if len(element):
        if not element.text or not element.text.strip():
            element.text = indentation + "  "
        
        for child in element:
            indent_xml(child, level + 1)
        
        if not element[-1].tail or not element[-1].tail.strip():
            element[-1].tail = indentation
    
    if level and (not element.tail or not element.tail.strip()):
        element.tail = indentation


def generate():
    config = load_config()
    validate_cards(config["cards"])

    source_file = resolve_project_path(config["source"]["overview"])

    if not source_file.is_file():
        raise FileNotFoundError(f"Overview source file not found: {source_file}")
    
    # Parse and validate everything before writing the output.
    tree = ET.parse(source_file)
    root = tree.getroot()
    widgets = find_widgets(root)

    missing_widgets = [
        card["name"]
        for card in config["cards"]
        if card["name"] not in widgets
    ]

    if missing_widgets:
        raise ValueError(
            "These card widgets were not found in Overview.bob: "
            + ", ".join(missing_widgets)
        )
    
    width = config["card"]["width"]
    height = config["card"]["height"]

    # Update the existing card widgets only.
    for card in config["cards"]:
        update_card(
            widgets[card["name"]],
            card,
            width,
            height,
        )
    
    # Preserve the configured background image widget and file.
    background = config.get("background", {})
    background_name = background.get("widget")

    if background_name:
        if background_name not in widgets:
            raise ValueError(
                f"Background widget '{background_name}' was not found."
            )
        
        if background.get("file"):
            set_child_text(
                widgets[background_name],
                "file",
                background["file"],
            )
    
    # Preserve the website button and its action, updating the URL if configured.
    website = config.get("website", {})
    button_name = website.get("button_widget")

    if button_name:
        if button_name not in widgets:
            raise ValueError(
                f"Website button '{button_name}' was not found."
            )
        
        button = widgets[button_name]
        action_url = button.find(".//action/url")

        if action_url is None:
            raise ValueError(
                f"No action URL found in website button '{button_name}'."
            )

        if website.get("url"):
            action_url.text = website["url"]
    
    # Keep the source file unchanged and write to a separate output file.
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    indent_xml(root)

    tree.write(
        OUTPUT_FILE,
        encoding="UTF-8",
        xml_declaration = True,
    )

    print(f"Overview generated successfully: {OUTPUT_FILE}")
    print(f"Updated cards: {len(config['cards'])}")


if __name__ == "__main__":
    try:
        generate()
    except (OSError, ET.ParseError, ValueError, KeyError, TypeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)