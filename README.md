# MightyZap 17Lf Python Library and CLI

A Python library to control the [MightyZap 17Lf
series](https://mightyzap.com/en/linear_actuator_intro/) of linear actuators.

## Installation

### As a CLI tool

```bash
uv tool install mightyzap-17lf
```

### As a Python library

```bash
mkdir project & cd project
uv init
uv add mightyzap-17lf
uv run python
>>> from mightyzap_17lf import MightyZap17Lf
>>> mighty = MightyZap17Lf("COM4")
>>> mighty.speed = 500
>>> mighty.position = 10000
```

### Configuring EEPROM (non-volatile) settings

Settings such as `accel`, `decel`, `min_pos_offset`, `max_pos_offset` and
`speed_limit` live in the actuator's EEPROM, which has a **limited number of
write cycles**. They are readable directly but can only be *written* inside a
`configure()` block, which also skips writes that wouldn't change the stored
value:

```python
with mighty.configure() as cfg:
    cfg.accel = 200
    cfg.speed_limit = 800

print(mighty.accel)  # reading is always allowed
```

For frequent control, use the RAM-backed `speed`, `current` and `position`
properties instead — they have no write-cycle limit.

## CLI usage

```bash
# Set position 8000
$ mz COM4 position 8000
# Set position 10000 with speed 500
$ mz COM4 position 10000 500
# Read current position
$ mz COM4 position
10000

# Set register 12 to 800 (long stroke limit)
$ mz COM4 register 12 800
# Read register 12
$ mz COM4 register 12

$ mz COM4 firmware_version
v1.2.3
$ mz COM4 serial_number
4752
```

### EEPROM (non-volatile) configuration

The `accel`, `decel`, `speed-limit`, `min-pos-offset` and `max-pos-offset`
commands read or write the actuator's EEPROM settings. Because EEPROM has a
limited number of write cycles, writes require confirmation (use `--yes`/`-y`
to skip the prompt in scripts) and a write that wouldn't change the stored
value is skipped automatically:

```bash
# Read the current acceleration
$ mz COM4 accel
200
# Write it (prompts for confirmation)
$ mz COM4 accel 250
accel is stored in EEPROM (limited write cycles). Change 200 -> 250? [y/N]: y
accel set to 250
# Non-interactive (e.g. in a script)
$ mz COM4 speed-limit 800 --yes
```

The same confirmation applies to the low-level `register` command when the
address falls in the EEPROM region (`0x00`–`0x32`).