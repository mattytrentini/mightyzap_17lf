# MightyZap 17Lf Python Library and CLI

A Python library to control the [MightyZap 17Lf
series](https://mightyzap.com/en/linear_actuator_intro/) of linear actuators.

## CLI

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