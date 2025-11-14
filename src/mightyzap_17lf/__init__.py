# mightyzap_17lf library

from pymodbus import FramerType
from pymodbus.client import ModbusSerialClient


class MightyZap17Lf:
    REG_SERIAL_NUMBER = 0
    REG_FIRMWARE_VERSION = 1
    REG_GOAL_POSITION = 205
    REG_GOAL_SPEED = 208
    REG_PRESENT_POSITION = 210
    REG_PRESENT_MOTOR_PWM = 213

    def __init__(self, serial_port: str, baudrate=57_600):
        self.id = 1  # Currently only device #1 is supported
        self.client = ModbusSerialClient(
            port=serial_port,
            framer=FramerType.RTU,
            baudrate=baudrate,
            stopbits=1,
            timeout=1,
        )
        if not self.client:
            # todo(mst): Use a more appropriate exception
            raise RuntimeError("Invalid comms")

    @property
    def serial_number(self) -> int:
        return self._read(MightyZap17Lf.REG_SERIAL_NUMBER)

    @property
    def firmware_version(self) -> int:
        # todo(mst) split 16-bit number into 3 digits for actual version number
        return self._read(MightyZap17Lf.REG_FIRMWARE_VERSION)

    @property
    def position(self) -> int:
        return self._read(MightyZap17Lf.REG_PRESENT_POSITION)

    @position.setter
    def position(self, position: int):
        assert 0 < position < 10_000
        self._write(MightyZap17Lf.REG_GOAL_POSITION, position, device_id=self.id)

    @property
    def speed(self) -> int:
        return self._read(MightyZap17Lf.REG_GOAL_SPEED)

    @speed.setter
    def speed(self, speed: int):
        assert 0 < speed < 1000
        self._write(MightyZap17Lf.REG_GOAL_POSITION, speed, device_id=self.id)

    def _read(self, register: int, device_id: int | None = None) -> int:
        if device_id is None:
            device_id = self.id

        result = self.client.read_holding_registers(address=register, device_id=self.id)

        return result.registers[0] if not result.isError() else 0

    def _write(self, register: int, value: int, device_id: int | None = None) -> None:
        if device_id is None:
            device_id = self.id

        self.client.write_register(address=register, value=value, device_id=self.id)
