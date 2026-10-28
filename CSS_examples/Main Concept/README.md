# CS Studio Examples

This directory contains the graphical user interfaces (GUIs) developed in **CS Studio** for the **SFRS detectors (SCIFI, PLSCI, MUSIC)**.

The main objective is to provide operators and users with intuitive, clear, and reliable control panels to monitor and interact with the detector systems.

## Project Goal

To build functional GUIs that connect directly to **EPICS PVs**. These interfaces allow operators to:

- **Command:** Send live control parameters to the detector firmware.
- **Monitor:** Track live readbacks and status updates to verify whether operations were successfully executed.

## Current Status of Detectors

| Detector | Connection Type | Status |
| --- | --- | --- |
| **SCIFI** | Live System | Fully functional GUI layout tested with live firmware |
| **MUSIC** | Live System | Fully functional GUI layout tested with live firmware |
| **PLSCI** | Soft PVs Only | GUI created but currently tested with soft PV values |

## Layout Automation

The detector GUIs were originally positioned manually in CS Studio by dragging widgets and adjusting their pixel coordinates.

To simplify future layout changes, a **YAML-based layout generation system** is now available.

Instead of manually repositioning multiple widgets inside CS Studio, the relevant layout parameters can be changed in configuration files and the corresponding `.bob` templates can be regenerated automatically.

### Structure

The layout configuration is stored under:

```text
layout/
├── layout.yaml
├── main.yaml
└── detectors/
    ├── scifi.yaml
    ├── plsci.yaml
    └── music.yaml
```

The Python tools are stored under:

```text
tools/
└── layout/
    ├── parser.py
    ├── modifier.py
    └── generator.py
```

### How It Works

`layout.yaml` is the main entry point of the layout system.

It references the individual detector configuration files and the Main GUI configuration.

For example:

```text
layout.yaml
    │
    ├── scifi.yaml
    ├── plsci.yaml
    ├── music.yaml
    └── main.yaml
```

The detector YAML files contain layout parameters such as:

- Board or Field Cage dimensions
- Starting positions
- Horizontal or vertical gaps
- Picture dimensions and positions
- Widget ordering
- Template-specific layout parameters

The generator reads these values, calculates the required widget coordinates, updates the corresponding CS Studio XML structure, and creates new `.bob` files.

### Running the Layout Generator

Run the generator from the project root directory:

```powershell
python tools/layout/generator.py layout/layout.yaml
```

The command processes all configured layouts in one run.

Generated files use the `_GENERATED.bob` suffix, for example:

```text
BoardTemplate_SCIFI_GENERATED.bob
BoardTemplate_6_PLSCI_GENERATED.bob
BoardTemplate_8_PLSCI_GENERATED.bob

MUSIC_TWOFC_TEMPLATE_GENERATED.bob
MUSIC_THREEFC_TEMPLATE_GENERATED.bob

Main_GENERATED.bob
```

The original `.bob` files are therefore not overwritten automatically.

### Example Layout Change

If the distance between the upper SCIFI boards should be increased, it is not necessary to reposition every board manually in CS Studio.

The corresponding value in:

```text
layout/detectors/scifi.yaml
```

can be changed, for example:

```yaml
top:
  gap: 15
```

to:

```yaml
top:
  gap: 25
```

Then run:

```powershell
python tools/layout/generator.py layout/layout.yaml
```

The new board coordinates are calculated automatically and written to the generated template.

The same principle is used for PLSCI, MUSIC, and the Main GUI layout.

### Current Scope and Limitations

The current automation focuses on **layout geometry of the existing templates**.

It can currently modify and regenerate layout properties such as:

- Widget positions
- Widget dimensions
- Spacing between repeated widgets
- Detector template geometry
- MUSIC Field Cage placement
- PLSCI board placement
- SCIFI board placement
- Main GUI tab geometry and configured detector file references

The system does **not currently redesign or generate the smallest detector widgets themselves**.

For example, it does not automatically modify the internal content of:

```text
boardcard_SCIFI.bob
boardcard_PLSCI.bob
MUSIC_ONEBOX_TEMPLATE.bob
```

Therefore, changes to internal widget content such as:

- EPICS PV names
- Labels
- Buttons
- LEDs
- Rules
- Actions
- Internal card styling
- Internal card widget positions

must still be edited separately if required.

The current system should therefore be understood as a **configuration-driven template layout generator**, not as a complete generator for every CS Studio widget.

### Python Dependency

The generator uses YAML configuration files and requires **PyYAML**.

To verify that it is installed:

```powershell
python -c "import yaml; print(yaml.__version__)"
```

If it is not installed:

```powershell
python -m pip install PyYAML
```

## Progress Tracking & Documentation

For a detailed daily breakdown of tasks, completed milestones, and future todos, please refer to the progress presentation:

```text
Documentation && Report/CSS works.pptx
```

This presentation includes:

- Day-by-day development logs
- Successfully completed components
- Next-day action items
- Pending features and future improvements