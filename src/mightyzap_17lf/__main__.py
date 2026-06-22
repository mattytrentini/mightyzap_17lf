import typer
from . import MightyZap17Lf

app = typer.Typer()

mightyzap: MightyZap17Lf


def _confirm_eeprom_write(label: str, current: int, value: int, yes: bool) -> bool:
    """Coalesce + gate an EEPROM write. Returns True if the write should proceed.

    Skips no-op writes (and avoids prompting for them), and otherwise requires
    confirmation unless `yes` is set. EEPROM has a limited number of write
    cycles, so writes are made deliberate.
    """
    if current == value:
        print(f"{label} already {value}, skipping (no EEPROM write)")
        return False
    if not yes:
        if not typer.confirm(
            f"{label} is stored in EEPROM (limited write cycles). "
            f"Change {current} -> {value}?"
        ):
            raise typer.Abort()
    return True


def _config_command(attr: str, value: int | None, yes: bool) -> None:
    """Read (value is None) or write an EEPROM configuration property by name."""
    current = getattr(mightyzap, attr)
    if value is None:
        print(current)
        return
    if _confirm_eeprom_write(attr, current, value, yes):
        with mightyzap.configure() as cfg:
            setattr(cfg, attr, value)
        print(f"{attr} set to {value}")


# --- RAM commands (safe to write frequently) ---


@app.command()
def position(
    value: int = typer.Argument(default=None), speed: int = typer.Argument(default=None)
) -> None:
    if speed is not None:
        mightyzap.speed = speed

    if value is not None:
        mightyzap.position = value
    else:
        print(mightyzap.position)


# --- EEPROM commands (non-volatile, limited writes; gated + coalesced) ---

_YES_HELP = "Skip the EEPROM write confirmation prompt"


@app.command()
def accel(
    value: int = typer.Argument(default=None),
    yes: bool = typer.Option(False, "--yes", "-y", help=_YES_HELP),
) -> None:
    _config_command("accel", value, yes)


@app.command()
def decel(
    value: int = typer.Argument(default=None),
    yes: bool = typer.Option(False, "--yes", "-y", help=_YES_HELP),
) -> None:
    _config_command("decel", value, yes)


@app.command()
def speed_limit(
    value: int = typer.Argument(default=None),
    yes: bool = typer.Option(False, "--yes", "-y", help=_YES_HELP),
) -> None:
    _config_command("speed_limit", value, yes)


@app.command()
def min_pos_offset(
    value: int = typer.Argument(default=None),
    yes: bool = typer.Option(False, "--yes", "-y", help=_YES_HELP),
) -> None:
    _config_command("min_pos_offset", value, yes)


@app.command()
def max_pos_offset(
    value: int = typer.Argument(default=None),
    yes: bool = typer.Option(False, "--yes", "-y", help=_YES_HELP),
) -> None:
    _config_command("max_pos_offset", value, yes)


# --- Low-level escape hatch ---


@app.command()
def register(
    address: int,
    value: int = typer.Argument(default=None),
    yes: bool = typer.Option(False, "--yes", "-y", help=_YES_HELP),
) -> None:
    if value is None:
        print(mightyzap._read(address))
        return

    if MightyZap17Lf.is_eeprom_register(address):
        current = mightyzap._read(address)
        if not _confirm_eeprom_write(f"register {address}", current, value, yes):
            return

    mightyzap._write(address, value)


@app.command()
def firmware_version() -> None:
    print(mightyzap.firmware_version)


@app.command()
def serial_number() -> None:
    print(mightyzap.serial_number)


@app.callback()
def main(serial_port: str):
    global mightyzap
    mightyzap = MightyZap17Lf(serial_port)


if __name__ == "__main__":
    app()
