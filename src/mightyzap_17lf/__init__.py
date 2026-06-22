# mightyzap_17lf library

from pymodbus import FramerType
from pymodbus.client import ModbusSerialClient

class MightyZap17Lf:
    # The 17Lf control table is split into two memory regions:
    #   * EEPROM / non-volatile (addresses 0x00-0x32, ~0-50): persists across
    #     power cycles but has a LIMITED number of write cycles, and each write
    #     blocks comms for ~250ms. Writable only via the `configure()` context
    #     manager (see below), which coalesces no-op writes to limit wear.
    #   * RAM / volatile (addresses 0xC8-0xF9, ~200-249): real-time parameters,
    #     unlimited writes, reset on power cycle. Used for frequent control.
    # See https://mightyzap-emanual.netlify.app/en/actuator/mini17lf/

    # Registers 0x00-0x32 are the non-volatile EEPROM region.
    EEPROM_ADDRESS_MAX = 0x32

    # --- EEPROM (non-volatile, limited writes) ---
    REG_SERIAL_NUMBER = 0
    REG_FIRMWARE_VERSION = 1
    REG_ACCEL = 15
    REG_DECEL = 16
    REG_MIN_POS_OFFSET = 17
    REG_MAX_POS_OFFSET = 18
    REG_SPEED_LIMIT = 20

    # --- RAM (volatile, safe to write frequently) ---
    REG_GOAL_POSITION = 205
    REG_GOAL_SPEED = 208
    REG_GOAL_CURRENT = 209
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

    @classmethod
    def is_eeprom_register(cls, address: int) -> bool:
        """True if `address` is in the non-volatile EEPROM region (limited writes)."""
        return 0 <= address <= cls.EEPROM_ADDRESS_MAX

    def configure(self) -> "_EepromConfig":
        """Unlock the EEPROM (non-volatile) configuration registers for writing.

        EEPROM registers have a limited number of write cycles, so they are not
        writable on the device object directly. Enter this context manager to
        set them:

            with mighty.configure() as cfg:
                cfg.accel = 200
                cfg.speed_limit = 800

        Writes are coalesced: a register is only written when its value actually
        changes, so re-applying the same configuration costs nothing. The
        returned handle is only valid inside its `with` block; using it
        afterwards raises RuntimeError. EEPROM values remain readable directly
        on the device (e.g. `mighty.accel`) since reads do not cause wear.
        """
        return _EepromConfig(self)

    @property
    def serial_number(self) -> int:
        return self._read(MightyZap17Lf.REG_SERIAL_NUMBER)

    @property
    def firmware_version(self) -> int:
        # todo(mst) split 16-bit number into 3 digits for actual version number
        return self._read(MightyZap17Lf.REG_FIRMWARE_VERSION)

    @property
    def min_pos_offset(self) -> int:
        # EEPROM register: read-only here. Write via `with mighty.configure() as cfg`.
        return self._read(MightyZap17Lf.REG_MIN_POS_OFFSET)

    @property
    def max_pos_offset(self) -> int:
        # EEPROM register: read-only here. Write via `with mighty.configure() as cfg`.
        return self._read(MightyZap17Lf.REG_MAX_POS_OFFSET)

    @property
    def speed_limit(self) -> int:
        # EEPROM register: read-only here. Write via `with mighty.configure() as cfg`.
        # For frequent speed control use the `speed` property (RAM Goal Speed).
        return self._read(MightyZap17Lf.REG_SPEED_LIMIT)

    @property
    def position(self) -> int:
        return self._read(MightyZap17Lf.REG_PRESENT_POSITION)

    @position.setter
    def position(self, position: int):
        assert 0 <= position <= 10_000
        self._write(MightyZap17Lf.REG_GOAL_POSITION, position, device_id=self.id)

    @property
    def speed(self) -> int:
        return self._read(MightyZap17Lf.REG_GOAL_SPEED)

    @speed.setter
    def speed(self, speed: int):
        assert 0 <= speed <= 1000
        self._write(MightyZap17Lf.REG_GOAL_SPEED, speed, device_id=self.id)

    @property
    def accel(self) -> int:
        # Note that accel and decel are in units of time so 0 is faster and 1000 is slower
        # EEPROM register: read-only here. Write via `with mighty.configure() as cfg`.
        return self._read(MightyZap17Lf.REG_ACCEL)

    @property
    def decel(self) -> int:
        # Note that accel and decel are in units of time so 0 is faster and 1000 is slower
        # EEPROM register: read-only here. Write via `with mighty.configure() as cfg`.
        return self._read(MightyZap17Lf.REG_DECEL)

    @property
    def current(self) -> int:
        return self._read(MightyZap17Lf.REG_GOAL_CURRENT)

    @current.setter
    def current(self, current_mA: int):
        assert 0 <= current_mA <= 1600
        self._write(MightyZap17Lf.REG_GOAL_CURRENT, current_mA, device_id=self.id)

    def _read(self, register: int, device_id: int | None = None) -> int:
        if device_id is None:
            device_id = self.id

        result = self.client.read_holding_registers(address=register, device_id=self.id)

        return result.registers[0] if not result.isError() else 0

    def _write(self, register: int, value: int, device_id: int | None = None) -> None:
        if device_id is None:
            device_id = self.id

        self.client.write_register(address=register, value=value, device_id=self.id)


class _EepromConfig:
    """Write handle for the 17Lf's EEPROM (non-volatile) configuration registers.

    Obtained from MightyZap17Lf.configure() and only valid inside its `with`
    block. Writes are coalesced — a register is only written when the value
    changes — to limit EEPROM wear and avoid the ~250ms comms stall each save
    incurs.
    """

    def __init__(self, device: "MightyZap17Lf"):
        self._device = device
        self._active = False

    def __enter__(self) -> "_EepromConfig":
        self._active = True
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self._active = False
        return None  # never suppress exceptions raised inside the block

    def _write(self, register: int, value: int) -> None:
        if not self._active:
            raise RuntimeError(
                "EEPROM configuration handle used outside its "
                "`with mighty.configure()` block"
            )
        # Coalesce: skip the write (and its ~250ms EEPROM save) if unchanged.
        if self._device._read(register) == value:
            return
        self._device._write(register, value, device_id=self._device.id)

    @property
    def accel(self) -> int:
        # Note that accel and decel are in units of time so 0 is faster and 1000 is slower
        return self._device._read(MightyZap17Lf.REG_ACCEL)

    @accel.setter
    def accel(self, accel: int):
        # Note that accel and decel are in units of time so 0 is faster and 1000 is slower
        assert 0 <= accel <= 1000
        self._write(MightyZap17Lf.REG_ACCEL, accel)

    @property
    def decel(self) -> int:
        # Note that accel and decel are in units of time so 0 is faster and 1000 is slower
        return self._device._read(MightyZap17Lf.REG_DECEL)

    @decel.setter
    def decel(self, decel: int):
        # Note that accel and decel are in units of time so 0 is faster and 1000 is slower
        assert 0 <= decel <= 1000
        self._write(MightyZap17Lf.REG_DECEL, decel)

    @property
    def min_pos_offset(self) -> int:
        return self._device._read(MightyZap17Lf.REG_MIN_POS_OFFSET)

    @min_pos_offset.setter
    def min_pos_offset(self, offset: int):
        assert 0 <= offset <= 1000
        self._write(MightyZap17Lf.REG_MIN_POS_OFFSET, offset)

    @property
    def max_pos_offset(self) -> int:
        return self._device._read(MightyZap17Lf.REG_MAX_POS_OFFSET)

    @max_pos_offset.setter
    def max_pos_offset(self, offset: int):
        assert 0 <= offset <= 1000
        self._write(MightyZap17Lf.REG_MAX_POS_OFFSET, offset)

    @property
    def speed_limit(self) -> int:
        return self._device._read(MightyZap17Lf.REG_SPEED_LIMIT)

    @speed_limit.setter
    def speed_limit(self, speed: int):
        assert 0 <= speed <= 1000
        self._write(MightyZap17Lf.REG_SPEED_LIMIT, speed)
