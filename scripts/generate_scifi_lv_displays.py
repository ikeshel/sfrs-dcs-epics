#!/usr/bin/env python3
"""Generate Phoebus LV panels for the SCIFI detectors and FPF2 PowerPi."""

import csv
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "CSStudio" / "SCIFI_LV"
# Use the Phoebus Jackie CA provider for discovery of the PowerPi IOC.
FPF2_POWERPI_CA = "jackie://SFRS:FPF2:POWERPI01:"
FPF2_ENABLE_CA = f"{FPF2_POWERPI_CA}ENABLE:CH"
FPF2_POWERPI_DISPLAY = "FPF2_POWERPI01.bob"
# PowerPi channel distribution assigns one front-panel channel per board group.
FPF2_ENABLE_CHANNELS = {1: range(4), 2: range(4, 8)}
BOARD_GROUPS = ("1–6", "7–8", "9–14", "15–16")

# Match BoardTemplate_SCIFI.bob: top 1–6, left 8/7, bottom 14–9, right 15/16.
# LV readback channel numbers are zero-based; board numbers are one-based.
CHANNEL_POSITIONS = {
    **{channel: (275 + channel * 215, 91) for channel in range(6)},
    6: (147, 624),
    7: (147, 351),
    **{channel: (1350 - (channel - 8) * 215, 884) for channel in range(8, 14)},
    14: (1472, 351),
    15: (1472, 624),
}
INK = (31, 49, 67)
MUTED = (91, 108, 125)
BACKGROUND = (240, 244, 248)
WHITE = (255, 255, 255)
BORDER = (211, 221, 231)
GREEN = (28, 116, 78)
RED = (164, 49, 53)
POWERPI_ON = (133, 222, 151)
POWERPI_PENDING = (245, 204, 80)
POWERPI_OFF = (179, 58, 69)
POWERPI_VOLTAGE_ON = (225, 47, 60)
POWERPI_VOLTAGE_OFF = (94, 105, 116)
POWERPI_ROW_HEIGHT = 128
POWERPI_CONTROL_Y = 58
POWERPI_TOGGLE_WIDTH = 153
POWERPI_TOGGLE_HEIGHT = 57
POWERPI_TEMP_WIDTH = 116
POWERPI_COLUMN_GAP = 12
POWERPI_ROW_WIDTH = 32 + 5 * (POWERPI_TOGGLE_WIDTH + POWERPI_COLUMN_GAP) + POWERPI_TEMP_WIDTH
POWERPI_ROW_REFRESH_PV = "sys://time"
POWERPI_TRIPS_PV = f"{FPF2_POWERPI_CA}TEMPERATURE:TRIPS"
POWERPI_LIMITS_PV = f"{FPF2_POWERPI_CA}TEMPERATURE:LIMITS"
POWERPI_THERMAL_HEIGHT = 68
THERMAL_SENSORS = tuple(f"PT1000 ROW{row}" for row in range(4)) + ("BME280",)
THERMAL_READBACKS = tuple(f"{sensor} temperature" for sensor in THERMAL_SENSORS[:4]) + ("Temperature",)
THERMAL_INPUTS = tuple(f"{FPF2_POWERPI_CA}PT1000:ROW{row}:TEMPERATURE" for row in range(4)) + (
    f"{FPF2_POWERPI_CA}BME280:TEMPERATURE",
)
# A disconnected trip PV still permits OFF commands in the row widget.
ROW_TRIPS_PV = f"=highestSeverity(`{POWERPI_TRIPS_PV}`) >= 3 ? -1 : `{POWERPI_TRIPS_PV}`"

THERMAL_VALUES = """\
from org.csstudio.display.builder.runtime.script import ValueUtil
from org.epics.vtype import Alarm, VNumber
from org.phoebus.pv import PV

def verified(value):
    return not PV.isDisconnected(value) and Alarm.alarmOf(value).getSeverity().ordinal() < 3

def trip_mask(value):
    return ValueUtil.getLong(value) if isinstance(value, VNumber) and verified(value) else None
"""

POWERPI_BUTTON_COLOR = f"""\
from org.csstudio.display.builder.runtime.script import ValueUtil
from org.epics.vtype import Alarm, AlarmSeverity, VNumber
from org.phoebus.pv import PV
from org.phoebus.ui.color import WidgetColor

readback = pvs[0].read()
confirmed = (not PV.isDisconnected(readback) and isinstance(readback, VNumber)
             and Alarm.alarmOf(readback).getSeverity() == AlarmSeverity.NONE
             and ValueUtil.getDouble(readback) == 1.0)
rgb = {POWERPI_ON!r} if confirmed else {POWERPI_PENDING!r}
widget.propOnColor().setValue(WidgetColor(*rgb))
"""

# Recheck the latest channel values once per second as well as on every monitor update.
ROW_STATE = THERMAL_VALUES + f"""\

def channel_pvs(pvs):
    return [pv for pv in pvs if pv.getName().startswith({FPF2_ENABLE_CA!r})]

def thermal_clear(pvs):
    trips = next((pv for pv in pvs if pv.getName() == {ROW_TRIPS_PV!r}), None)
    return trips is not None and trip_mask(trips.read()) == 0

def writable_channels(channels):
    return [pv for pv in channels if not PV.isDisconnected(pv.read()) and not pv.isReadonly()]

def row_action(inputs):
    channels = channel_pvs(inputs)
    writable = writable_channels(channels)
    if not thermal_clear(inputs):
        return writable, 0
    if len(writable) != 4:
        return [], 0
    target = 0 if all(ValueUtil.getInt(pv.read()) == 1 for pv in channels) else 1
    return channels, target
"""

ROW_STATUS = ROW_STATE + """\

channels, target = row_action(pvs)
widget.propText().setValue(('ALL ON' if target else 'ALL OFF') if channels else 'UNAVAILABLE')
widget.propEnabled().setValue(bool(channels))
"""

ROW_TOGGLE = ROW_STATE + """\
from java.lang import Exception as JavaException
from org.csstudio.display.builder.runtime.script import ScriptUtil

channels, target = row_action(ScriptUtil.getPVs(widget))
if channels:
    failed = []
    for pv in channels:
        try:
            pv.write(target)
        except JavaException:
            failed.append(pv.getName())
    if failed:
        ScriptUtil.showErrorDialog(widget, 'Could not write: ' + ', '.join(failed))
else:
    ScriptUtil.showErrorDialog(widget, 'Row controls are unavailable. Check the channel PV connections.')
"""

THERMAL_MONITOR = THERMAL_VALUES + r"""

import math
from org.csstudio.display.builder.runtime.script import ScriptUtil
from org.epics.vtype import VNumberArray
from org.phoebus.ui.color import WidgetColor

def finite(number):
    return not math.isnan(number) and not math.isinf(number)

def limits_vector(value, count):
    if PV.isDisconnected(value) or not isinstance(value, VNumberArray):
        return None
    data = value.getData()
    if data.size() != count:
        return None
    limits = [data.getDouble(i) for i in range(count)]
    return limits if all(finite(item) for item in limits) else None

def temperature_color(value, limit, tripped):
    if tripped:
        return WidgetColor(255, 199, 204)
    if limit is None or not isinstance(value, VNumber) or not verified(value):
        return WidgetColor(240, 244, 248)
    temperature = ValueUtil.getDouble(value)
    if not finite(temperature):
        return WidgetColor(240, 244, 248)
    if temperature >= limit:
        return WidgetColor(255, 199, 204)
    if temperature >= limit * 0.8:
        return WidgetColor(255, 237, 174)
    return WidgetColor(225, 245, 231)

def update_thermal(widget, pvs, sensor_names, displayed_sensors, buttons):
    mask = trip_mask(pvs[0].read())
    if mask is None:
        status = 'Thermal trip status unavailable - ON commands blocked'
        banner = WidgetColor(255, 237, 174)
    elif mask:
        tripped = [name for i, name in enumerate(sensor_names) if mask & (1 << i)]
        if mask & ~((1 << len(sensor_names)) - 1):
            tripped.append('other trip bits')
        status = 'Thermal shutdown - ' + ', '.join(tripped)
        banner = WidgetColor(255, 199, 204)
    else:
        status = 'No active thermal trips'
        banner = WidgetColor(225, 245, 231)
    widget.propText().setValue(status)
    widget.propBackgroundColor().setValue(banner)

    limits_value = pvs[1].read()
    limits = limits_vector(limits_value, len(sensor_names))
    confirmed = limits is not None and verified(limits_value)
    limits_status = ScriptUtil.findWidgetByName(widget, 'Thermal limits status')
    limits_status.propText().setValue('' if confirmed else
                                    'Thermal limits unavailable' if limits is None else 'Thermal limits unverified')
    for (index, readback_name), pv in zip(displayed_sensors, pvs[2:]):
        sensor = ScriptUtil.findWidgetByName(widget, readback_name)
        limit_label = ScriptUtil.findWidgetByName(widget, sensor_names[index] + ' limit')
        if limits is None:
            limit_label.propText().setValue('Limit unavailable')
        else:
            limit_label.propText().setValue(u'Limit %.1f \u00b0C%s' %
                                            (limits[index], '' if confirmed else ' ?'))
        tripped = mask is not None and (mask & (1 << index)) != 0
        limit = limits[index] if confirmed else None
        sensor.propBackgroundColor().setValue(temperature_color(pv.read(), limit, tripped))

    for name, pv in zip(buttons, pvs[len(displayed_sensors) + 2:]):
        value = pv.read()
        on = not PV.isDisconnected(value) and ValueUtil.getInt(value) == 1
        ScriptUtil.findWidgetByName(widget, name).propEnabled().setValue(mask == 0 or on)
"""


def prop(parent, name, value):
    element = ET.SubElement(parent, name)
    element.text = str(value).lower() if isinstance(value, bool) else str(value)
    return element


def color(parent, name, rgb):
    ET.SubElement(ET.SubElement(parent, name), "color",
                  dict(zip(("red", "green", "blue"), map(str, rgb))))


def font(parent, size=14, bold=False):
    ET.SubElement(ET.SubElement(parent, "font"), "font", {
        "family": "Liberation Sans", "size": str(float(size)),
        "style": "BOLD" if bold else "REGULAR",
    })


def display(name, width, height):
    root = ET.Element("display", version="2.0.0")
    for key, value in (("name", name), ("width", width), ("height", height),
                       ("grid_visible", False)):
        prop(root, key, value)
    color(root, "background_color", BACKGROUND)
    return root


def widget(root, kind, name, x, y, width, height):
    version = "3.0.0" if kind in ("action_button", "group") else "2.0.0"
    node = ET.SubElement(root, "widget", type=kind, version=version)
    for key, value in (("name", name), ("x", x), ("y", y),
                       ("width", width), ("height", height)):
        prop(node, key, value)
    return node


def label(root, name, text, x, y, width, height=24, size=14, bold=False,
          centered=False, foreground=INK):
    node = widget(root, "label", name, x, y, width, height)
    prop(node, "text", text)
    font(node, size, bold)
    color(node, "foreground_color", foreground)
    prop(node, "horizontal_alignment", 1 if centered else 0)
    prop(node, "vertical_alignment", 1)
    return node


def monitor_pvs(node, code, pvs):
    script = ET.SubElement(ET.SubElement(node, "scripts"), "script",
                           file="EmbeddedPy", check_connections="false")
    prop(script, "text", code)
    for pv in pvs:
        prop(script, "pv_name", pv)


def numeric_readback(root, name, pv, x, y, width, height, precision, font_size,
                     format_option=1, show_units=True):
    node = widget(root, "textupdate", name, x, y, width, height)
    prop(node, "pv_name", pv)
    prop(node, "format", format_option)
    prop(node, "precision", precision)
    prop(node, "show_units", show_units)
    prop(node, "horizontal_alignment", 1)
    prop(node, "vertical_alignment", 1)
    font(node, font_size, True)
    color(node, "foreground_color", INK)
    color(node, "background_color", BACKGROUND)
    return node


def button(root, name, text, x, y, width, background, height=32, font_size=13):
    node = widget(root, "action_button", name, x, y, width, height)
    prop(node, "text", text)
    font(node, font_size, True)
    color(node, "foreground_color", WHITE)
    color(node, "background_color", background)
    return node


def open_display_button(root, name, text, filename, x, y, width):
    node = button(root, name, text, x, y, width, INK)
    action = ET.SubElement(ET.SubElement(node, "actions"), "action",
                           type="open_display")
    prop(action, "file", filename)
    prop(action, "target", "window")


def output_button(root, pv_prefix, channels, value, name, text, x, y, width):
    node = button(root, name, text, x, y, width, GREEN if value else RED)
    first = f"{channels[0]:02d}"
    if len(channels) == 1:
        prop(node, "pv_name", f"{pv_prefix}{first}")
    suffix = first if len(channels) == 1 else f"{first}–{channels[-1]:02d}"
    prop(node, "tooltip", f"Write {value} to {pv_prefix}{suffix}")
    actions = ET.SubElement(node, "actions", execute_as_one="true")
    for channel in channels:
        action = ET.SubElement(actions, "action", type="write_pv")
        prop(action, "description", f"CH{channel:02d} {'ON' if value else 'OFF'}")
        prop(action, "pv_name", f"{pv_prefix}{channel:02d}")
        prop(action, "value", value)


def output_state(root, name, pv, tooltip, x, y):
    state = widget(root, "led", name, x, y, 88, 22)
    prop(state, "pv_name", pv)
    prop(state, "tooltip", tooltip)
    prop(state, "square", True)
    prop(state, "labels_from_pv", False)
    prop(state, "off_label", "OFF")
    prop(state, "on_label", "ON")
    color(state, "off_color", MUTED)
    color(state, "on_color", GREEN)
    color(state, "foreground_color", WHITE)
    font(state, 11, True)


def card_background(root, name, x, y, height, width=200):
    card = widget(root, "rectangle", name, x, y, width, height)
    prop(card, "line_width", 1)
    color(card, "line_color", BORDER)
    color(card, "background_color", WHITE)


def powerpi_channel_readbacks(root, ch, x, y):
    rail_pv = f"{FPF2_POWERPI_CA}ENABLE_RBV:{ch}"
    current_pv = f"{FPF2_POWERPI_CA}CURRENT:{ch}"
    status = widget(root, "led", f"{ch} output status", x, y + 3, 16, 16)
    prop(status, "pv_name", rail_pv)
    prop(status, "border_alarm_sensitive", True)
    prop(status, "square", True)
    prop(status, "tooltip", "12 V rail readback\n$(pv_name)\n$(pv_value)")
    color(status, "on_color", POWERPI_VOLTAGE_ON)
    color(status, "off_color", POWERPI_VOLTAGE_OFF)

    label(root, f"{ch} current label", "I (A)", x + 22, y, 34, height=22,
          size=13, bold=True, foreground=MUTED)
    # Display unavailable current as plain text. NaN compares unequal to itself.
    severity = f"highestSeverity(`{current_pv}`)"
    current_value = (f'={severity} >= 3 || (`{current_pv}` != `{current_pv}`) '
                     f'? "non" : `{current_pv}`')
    readback = numeric_readback(root, f"{ch} current in amperes", current_value, x + 58, y,
                                POWERPI_TOGGLE_WIDTH - 58, 22, precision=3, font_size=13,
                                format_option=0, show_units=False)
    prop(readback, "tooltip", f"IOC current readback in amperes\n{current_pv}\n$(pv_value)")


def powerpi_channel(root, channel, caption, x, y):
    ch = f"CH{channel:02d}"
    powerpi_channel_readbacks(root, ch, x, y - 25)
    node = widget(root, "bool_button", f"{ch} toggle", x, y,
                  POWERPI_TOGGLE_WIDTH, POWERPI_TOGGLE_HEIGHT)
    prop(node, "pv_name", f"{FPF2_ENABLE_CA}{channel:02d}")
    prop(node, "enabled", False)
    prop(node, "tooltip", f"{caption}\n$(pv_name)\n$(pv_value)")
    prop(node, "bit", 0)
    prop(node, "mode", 0)
    prop(node, "labels_from_pv", False)
    prop(node, "show_led", False)
    prop(node, "off_label", f"OFF CH {channel}")
    prop(node, "on_label", f"ON CH {channel}")
    color(node, "off_color", POWERPI_OFF)
    color(node, "on_color", POWERPI_PENDING)
    color(node, "foreground_color", (0, 0, 0))
    font(node, 20, True)
    monitor_pvs(node, POWERPI_BUTTON_COLOR, (f"{FPF2_POWERPI_CA}ENABLE_RBV:{ch}",))


def powerpi_row_toggle(root, channels, x, y):
    first, last = channels[0], channels[-1]
    name = f"Row CH{first:02d}–CH{last:02d} toggle"
    node = button(root, name, "UNAVAILABLE", x, y, POWERPI_TOGGLE_WIDTH, INK,
                  height=POWERPI_TOGGLE_HEIGHT, font_size=20)
    prop(node, "enabled", False)
    prop(node, "tooltip", f"Toggle CH{first:02d}–CH{last:02d}. "
         "Turns all off when all are on, otherwise turns all on. "
         "Only OFF commands are available during a thermal trip or while trip status is unavailable.")

    monitor_pvs(node, ROW_STATUS, (
        *(f"{FPF2_ENABLE_CA}{channel:02d}" for channel in channels),
        ROW_TRIPS_PV, POWERPI_ROW_REFRESH_PV,
    ))

    action = ET.SubElement(ET.SubElement(node, "actions"), "action", type="execute")
    prop(action, "description", f"Toggle CH{first:02d}–CH{last:02d}")
    script = ET.SubElement(action, "script", file="EmbeddedPy")
    prop(script, "text", ROW_TOGGLE)


def powerpi_row(root, number, channels, x, y):
    first, last = channels[0], channels[-1]
    section = f"SCIFI{number}" if number else "Reserved"
    title = f"{section}  ·  CH{first:02d}–CH{last:02d}"
    group = widget(root, "group", title, x, y, POWERPI_ROW_WIDTH, POWERPI_ROW_HEIGHT)
    prop(group, "style", 3)
    prop(group, "transparent", True)
    card_background(group, "Row background", 0, 0, POWERPI_ROW_HEIGHT, width=POWERPI_ROW_WIDTH)
    label(group, "Row title", title, 16, 8, POWERPI_ROW_WIDTH - 32, size=16, bold=True)
    control_y = POWERPI_CONTROL_Y
    powerpi_row_toggle(group, channels, 16, control_y)
    step = POWERPI_TOGGLE_WIDTH + POWERPI_COLUMN_GAP
    column_x = 16 + step
    for column, channel in enumerate(channels):
        if column == 2:
            row = first // len(BOARD_GROUPS)
            label(root, "PT1000 label", "PT1000", x + column_x, y + control_y - 23,
                  POWERPI_TEMP_WIDTH, height=20, size=13, centered=True, foreground=MUTED)
            numeric_readback(group, THERMAL_READBACKS[row], THERMAL_INPUTS[row], column_x,
                             control_y, POWERPI_TEMP_WIDTH, POWERPI_TOGGLE_HEIGHT - 20,
                             precision=1, font_size=19)
            label(group, f"{THERMAL_SENSORS[row]} limit", "Limit unavailable",
                  column_x, control_y + POWERPI_TOGGLE_HEIGHT - 20, POWERPI_TEMP_WIDTH,
                  height=20, size=12, centered=True, foreground=MUTED)
            column_x += POWERPI_TEMP_WIDTH + POWERPI_COLUMN_GAP
        caption = f"Boards {BOARD_GROUPS[column]}" if number else f"Front-panel button S{channel + 1}"
        powerpi_channel(group, channel, caption, column_x, control_y)
        column_x += step


def board_sensor_group(root):
    sensor = widget(root, "group", "Board Sensor", 24, 59, POWERPI_ROW_WIDTH, 83)
    prop(sensor, "style", 3)
    prop(sensor, "transparent", True)
    card_background(sensor, "Board sensor background", 0, 0, 83, width=POWERPI_ROW_WIDTH)
    label(sensor, "Board sensor title", "Board Sensor", 14, 8, POWERPI_ROW_WIDTH - 28,
          size=16, bold=True)
    column_width = (POWERPI_ROW_WIDTH - 28) // 3
    for column, caption in enumerate(("Pressure", "Humidity", "Temperature")):
        x = 14 + column * column_width
        label(sensor, f"{caption} label", caption, x, 43, 100, foreground=MUTED)
        width = column_width - 120
        if caption == "Temperature":
            width = 96
            label(sensor, "BME280 limit", "Limit unavailable", x + 102 + width,
                  38, column_width - 102 - width, height=34, size=12, centered=True,
                  foreground=MUTED)
        numeric_readback(sensor, caption, f"{FPF2_POWERPI_CA}BME280:{caption.upper()}",
                         x + 102, 38, width, 34, precision=2, font_size=19)


def thermal_panel(root, x, y, channels, sensor_indices):
    card_background(root, "Thermal shutdown background", x, y, POWERPI_THERMAL_HEIGHT,
                    width=POWERPI_ROW_WIDTH)
    status = label(root, "Thermal shutdown status", "Thermal trip status unavailable - ON commands blocked",
                   x + 14, y + 8, POWERPI_ROW_WIDTH - 28, height=27, size=16, bold=True)
    prop(status, "transparent", False)
    color(status, "background_color", (255, 237, 174))
    label(root, "Thermal recovery", "After cooling and clearance, re-enable outputs manually.",
          x + 14, y + 37, 650, foreground=MUTED)
    label(root, "Thermal limits status", "Thermal limits unavailable",
          x + 674, y + 37, POWERPI_ROW_WIDTH - 688, foreground=MUTED)

    displayed_sensors = tuple((index, THERMAL_READBACKS[index]) for index in sensor_indices)
    buttons = tuple(f"CH{channel:02d} toggle" for channel in channels)
    monitor_pvs(status, THERMAL_MONITOR +
                f"\nupdate_thermal(widget, pvs, {THERMAL_SENSORS!r}, {displayed_sensors!r}, {buttons!r})\n", (
        POWERPI_TRIPS_PV, POWERPI_LIMITS_PV,
        *(THERMAL_INPUTS[index] for index in sensor_indices),
        *(f"{FPF2_ENABLE_CA}{channel:02d}" for channel in channels),
    ))


def powerpi_temperature_trend(root, x, y, height):
    card_background(root, "Temperature trend background", x, y, height, width=POWERPI_ROW_WIDTH)
    label(root, "Temperature trend title", "Temperature trend", x + 16, y + 8,
          POWERPI_ROW_WIDTH - 32, size=16, bold=True)
    trend = widget(root, "databrowser", "PowerPi temperature trend", x + 12, y + 36,
                   POWERPI_ROW_WIDTH - 24, height - 48)
    prop(trend, "file", "../../plots/powerpi01_pt1000.plt")
    prop(trend, "show_toolbar", False)


def powerpi_panel():
    rows = [*FPF2_ENABLE_CHANNELS.items(), (None, range(8, 12)), (None, range(12, 16))]
    thermal_y = 154
    first_row_y = thermal_y + POWERPI_THERMAL_HEIGHT + 12
    row_spacing = POWERPI_ROW_HEIGHT + 12
    trend_y = first_row_y + len(rows) * row_spacing
    trend_height = 292
    root = display("FPF2:POWERPI01", POWERPI_ROW_WIDTH + 48, trend_y + trend_height + 24)
    label(root, "Title", "FPF2  /  POWERPI01",
          24, 18, POWERPI_ROW_WIDTH, 36, 26, True)
    board_sensor_group(root)
    thermal_panel(root, 24, thermal_y, range(16), range(len(THERMAL_SENSORS)))

    for row, (number, channels) in enumerate(rows):
        powerpi_row(root, number, channels, 24, first_row_y + row * row_spacing)
    powerpi_temperature_trend(root, 24, trend_y, trend_height)
    return root


def detector_panel(chamber, number):
    detector = f"{chamber}:SCIFI{number}"
    prefix = f"SFRS:{detector}:LV:"
    out_prefix = f"{prefix}OUT:CH:"
    enable_channels = FPF2_ENABLE_CHANNELS.get(number) if chamber == "FPF2" else None
    powerpi_offset = POWERPI_THERMAL_HEIGHT + 12 if enable_channels else 0
    root = display(f"{detector} — Low voltage", 1820, 1226 + powerpi_offset)
    label(root, "Title", f"{detector}  /  LOW VOLTAGE", 24, 18, 1100, 36, 26, True)
    label(root, "Prefix", prefix, 24, 58, 1000, foreground=MUTED)
    channel_summary = "16 BOARD READBACKS" if enable_channels else "16 CHANNELS  ·  00–15"
    label(root, "Channels", channel_summary, 1500, 24, 296,
          centered=True, foreground=MUTED)

    picture = widget(root, "picture", "Detector layout", 357, 351, 1105, 523)
    prop(picture, "file", "../../CSS_examples/New Concept/SCIFI/det_scifi.svg")

    for channel in range(16):
        ch = f"CH{channel:02d}"
        x, y = CHANNEL_POSITIONS[channel]
        card_background(root, f"{ch} card", x, y, 164 if enable_channels else 250)
        heading = f"BOARD {channel + 1}" if enable_channels else f"BOARD {channel + 1}  /  {ch}"
        label(root, f"{ch} heading", heading,
              x + 8, y + 8, 184, 26, 16, True, True)
        for field, caption, offset in (("V_RBV", "Voltage", 40),
                                       ("I_RBV", "Current", 104)):
            label(root, f"{ch} {caption} label", caption, x + 12, y + offset, 176,
                  size=12, centered=True, foreground=MUTED)
            numeric_readback(root, f"{ch} {field}", f"{prefix}{field}:CH:{channel:02d}",
                             x + 12, y + offset + 24, 176, 32, precision=3, font_size=18)

        if enable_channels:
            continue
        label(root, f"{ch} OUT label", "OUT", x + 12, y + 174, 64, size=12,
              foreground=MUTED)
        output_state(root, f"{ch} OUT value", f"{out_prefix}{channel:02d}",
                     "OUT command PV: $(pv_name)\n$(pv_value)", x + 100, y + 174)
        output_button(root, out_prefix, [channel], 1, f"{ch} ON", "ON",
                      x + 12, y + 208, 82)
        output_button(root, out_prefix, [channel], 0, f"{ch} OFF", "OFF",
                      x + 106, y + 208, 82)

    if enable_channels:
        label(root, "PowerPi", "POWERPI01  /  CHANNEL CONTROLS",
              147, 1056, POWERPI_ROW_WIDTH, size=16, bold=True)
        thermal_panel(root, 147, 1084, enable_channels, (number - 1,))
        powerpi_row(root, number, enable_channels, 147, 1084 + powerpi_offset)
        open_display_button(root, "Open POWERPI01", "VIEW ALL 16 CHANNELS", FPF2_POWERPI_DISPLAY,
                            180 + POWERPI_ROW_WIDTH, 1154 + powerpi_offset, 260)
        return root

    output_button(root, out_prefix, range(16), 1, "ALL ON", "ALL ON",
                  147, 1162, 124)
    output_button(root, out_prefix, range(16), 0, "ALL OFF", "ALL OFF",
                  283, 1162, 124)
    label(root, "All scope", "ALL controls CH00–CH15 of this detector.",
          431, 1166, 530, foreground=MUTED)
    label(root, "Output source", "OUT shows the output command PV.",
          1256, 1166, 416, foreground=MUTED)
    return root


def save(root, filename):
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(OUTPUT / filename, encoding="UTF-8",
                               xml_declaration=True)


def main():
    with (ROOT / "data/scifi_temperature.csv").open(newline="") as stream:
        detectors = sorted({(row["CHAMBER"], int(row["SCIFI_NUMBER"]))
                            for row in csv.DictReader(stream)})
    OUTPUT.mkdir(parents=True, exist_ok=True)
    powerpi_y = 112 + ((len(detectors) + 1) // 2) * 52
    index = display("SCIFI low voltage", 720, powerpi_y + 54)
    label(index, "Title", "SCIFI  /  LOW VOLTAGE", 24, 20, 672, 36, 26, True)
    label(index, "Subtitle", "Select a detector or open the POWERPI01 front panel.",
          24, 62, 672, foreground=MUTED)
    for i, (chamber, number) in enumerate(detectors):
        filename = f"{chamber}_SCIFI{number}_LV.bob"
        save(detector_panel(chamber, number), filename)
        open_display_button(index, f"Open {chamber} SCIFI{number}",
                            f"{chamber}  /  SCIFI{number}", filename,
                            24 + (i % 2) * 344, 112 + (i // 2) * 52, 328)
    save(powerpi_panel(), FPF2_POWERPI_DISPLAY)
    open_display_button(index, "Open POWERPI01", "FPF2  /  POWERPI01", FPF2_POWERPI_DISPLAY,
                        24, powerpi_y, 672)
    save(index, "SCIFI_LV.bob")
    print(f"Generated {len(detectors)} detector panels, {FPF2_POWERPI_DISPLAY}, and SCIFI_LV.bob in {OUTPUT}")


if __name__ == "__main__":
    main()
