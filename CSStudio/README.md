# Huber chiller display

Open `huber_chiller.bob` in Phoebus Display Builder (runtime) for control and
monitoring of the Huber Unichiller OLÉ IOC. For example, from this repository:

```bash
/home/irakli/EPICS/phoebus-5.0.5/phoebus-product/phoebus.sh -resource "$PWD/CSStudio/huber_chiller.bob"
```

The display macro `P` defaults to `SFRS:FHF1:SCIFI3:CHILLER:` (including the
trailing colon), matching the neighbouring `huber-unichiller-P012OLE` IOC's
`scripts/run-ioc.sh`. Change the display's `P` macro when using another prefix.
The IOC must be running and reachable through Channel Access.

The display provides:

- Internal, external, and device setpoint temperatures, with IOC alarm borders.
- Setpoint entry: type a temperature in °C and press Enter to write `TEMP_SET`.
  The IOC enforces its drive limits, shown from `TEMP_SET.DRVL` and `.DRVH`.
- Start and Stop buttons writing `1` and `0` to `RUN`; `RUN_RBV` shows the
  controller's actual state independently of the command.
- Communication validity (`COMM_OK`), device alarm code (`ALARM_RBV`), external
  sensor presence, and controller identity.
- Live internal-temperature and device-setpoint trends. These collect data while
  the display is open; no archive is configured.

`TEMP_EXTERNAL_RBV = -151 °C` means the external sensor is absent; the IOC marks
this readback INVALID. It is omitted from the trend to preserve a useful scale.
`COMM_OK` reflects valid core replies, not absence of a device alarm. Alarm code
zero means clear. Disconnected or invalid readbacks must not be interpreted as
current device state.

PV bindings were checked against the neighbouring IOC's `db/huber.db`, and the
file was loaded with the installed Phoebus 5.0.5 model reader with zero widget
errors. Live hardware operation and visual runtime rendering remain unverified.
