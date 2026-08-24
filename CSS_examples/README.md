# CS Studio Examples

This directory contains the graphical user interfaces (GUIs) developed in **CS Studio** for the **SFRS detectors**.

The main objective is to provide operators and users with intuitive, clear, and reliable control panels to monitor and interact with the detector systems.

## Project Goal

To build functional GUIs that connect directly to **EPICS PVs**. These interfaces allow operators to:
- **Command:** Send live control parameters to the detector firmware.
- **Monitor:** Track live readbacks and status updates to verify if operations were successfully executed.

## Current Status of Detectors

The project covers three main detector types:

|    Detector    |    Connection Type    |    Status    |
|    **SCIFI**   |    Live System        |    Fully functional GUI layout tested with live firmware    |
|    **MUSIC**   |    Live System        |    Fully functional GUI layout tested with live firmware    |
|    **PLSCI**   |    Soft PVs Only      |    GUI created but currenty tested with soft PV values      |

## Next Step (Layout Automation)

- **Current Phase:** The initial GUIs were designed manually by dragging, dropping, and positioning element by pixel.
- **Next Step:** It is aimed to transition from manual positioning to automated GUI generation using a `layoutcreator.txt` file.

## Progress Tracking & Documentation

For a detailed daily breakdown of tasks, completed milestones, and future todos, please refer to the progress presentation:

`Documentation && Report/CSS works.pptx`

This presentation includes:
- Day-by-day logs of development task
- Successfully completed components
- Next-day action items and pending futures.