import typer
from . import MightyZap17Lf

app = typer.Typer()

mightyzap: MightyZap17Lf


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


@app.command()
def register(address: int, value: int = typer.Argument(default=None)) -> None:
    if value is None:
        print(mightyzap._read(address))
    else:
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
