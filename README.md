# Adventuring Inventory

A simple Raspberry Pi-based NFC-powered inventory system that uses a PN532 NFC reader and an ST7789-compatible SPI display to add/remove items by tapping NFC tags. Items are stored in a plaintext file (`inventory.txt`) and the UI is controlled with three GPIO buttons.

Note: This project can run using a Pimoroni Pirate Audio HAT as the screen (see "Pirate Audio" section below).

## Features
- Add or remove items by tapping NFC tags (NDEF Text Records).
- Visual feedback on a 240x240 ST7789-compatible display (or Pirate Audio HAT).
- Browse inventory with left/right buttons.
- Hold the third button to clear the whole inventory.
- Minimal, file-backed storage (`inventory.txt`).

## Repository layout
- `inventory_system/main.py` — main application script
- `inventory.txt` — created/updated at runtime (stores inventory items)
- `M0D.png` — optional logo shown on boot (place in project root)

## Hardware required
- Raspberry Pi (3/4/Zero W)
- PN532 NFC/RFID breakout or HAT (I2C mode)
- pimodori pirate audio hat for the buttons and screen any works.
- Wires, breadboard, and pull-up resistors (or use internal pull-ups)
- a phone with nfc tools(to write the nfc ndef text to it)

### Pirate Audio (Pimoroni) HAT
If you're using the [Pimoroni Pirate Audio HAT](https://shop.pimoroni.com/products/pirate-audio) as the display, it provides a compact screen and audio features. The HAT typically exposes the display over SPI and uses specific GPIO pins for DC/backlight/chip select. Because Pirate Audio wiring/pin mapping can differ from a raw SPI display breakout, you may need to update the `st7789.ST7789(...)` constructor parameters in `main.py` to match the HAT's pins or use Pimoroni's helper libraries.

## GPIO / Wiring (as used in code)
Note: the code uses BCM pin numbering.

- NFC (PN532) — I2C:
  - SDA -> SDA (board.SDA)
  - SCL -> SCL (board.SCL)
  - VCC -> 3.3V
  - GND -> GND

- Display (ST7789) — SPI (SPI bus 0):
  - MOSI -> SPI MOSI (SPI0 MOSI)
  - SCLK -> SPI SCLK (SPI0 SCLK)
  - CS -> CE1 (chip-select 1) — code uses `cs=1`
  - DC  -> BCM 9 (as configured in `main.py`: `dc=9`)
  - BL  -> BCM 13 (backlight)
  - VCC -> 3.3V
  - GND -> GND

- Pirate Audio HAT users:
  - If using Pirate Audio, many HAT variants route SPI and control pins directly through the HAT header. Confirm the HAT documentation for DC, CS, and BL pins and update the `st7789` constructor in `main.py` accordingly. You may also prefer to use Pimoroni's libraries if available for your HAT variant.

- Buttons (BCM numbering, as used in `main.py`):
  - Left button  -> BCM 5
  - Right button -> BCM 6
  - Hold/Clear   -> BCM 16
  - Buttons use pull-up (pressed = LOW)

If you change pins in hardware, update the constants in `inventory_system/main.py`.

## Software / Dependencies

The script uses Adafruit Blinka + CircuitPython PN532, Pillow (PIL), RPi.GPIO, st7789 display driver, and an NDEF parsing library.

Recommended installation (run on Raspberry Pi OS, with I2C & SPI enabled via `raspi-config`):

1. Enable interfaces:
   - sudo raspi-config → Interface Options → Enable I2C and SPI

2. Update & install system packages:
   - sudo apt update
   - sudo apt install -y python3-pip python3-pil python3-rpi.gpio i2c-tools

3. Install Python packages:
   - pip3 install --upgrade adafruit-blinka
   - pip3 install adafruit-circuitpython-pn532
   - pip3 install pillow
   - pip3 install RPi.GPIO
   - pip3 install st7789
   - pip3 install ndef

Notes:
- Package names for display/NFC libraries vary by platform; the code imports `st7789` and `adafruit_pn532.i2c.PN532_I2C`.
- If installation fails for `st7789`, try `st7789rpi` or check the library README for the correct package for your environment.
- For Pirate Audio HAT users, Pimoroni may provide specific Python libraries or examples—check the HAT documentation.

## Running

From the repository root:
- sudo python3 inventory_system/main.py

Why sudo? Access to GPIO and SPI/I2C often require root privileges on Raspberry Pi. Alternatively configure permissions or run via a systemd service with appropriate privileges.

## How it works (quick)
- On boot the display shows a splash screen (uses `M0D.png` if present).
- The script polls the PN532 for tags. When a tag with an NDEF TextRecord is read it toggles the item name in `inventory.txt` (add or remove).
- Buttons navigate the list or clear it when the "clear" button is held for ~2 seconds.

Controls:
- BCM 5: previous item
- BCM 6: next item
- BCM 16: hold to clear inventory

## Configuration notes
- `inventory_file` variable in `main.py` sets the inventory filename (default `inventory.txt`).
- `MAX_VISIBLE_ITEMS`, `SPACING`, `HOLD_DELAY`, and button pins are configurable at the top of `main.py`.
- Display params (width/height, rotation, pins) are defined in the `st7789.ST7789(...)` constructor — update these when using Pirate Audio HAT if needed.

## Troubleshooting

- PN532 initialization failure:
  - Ensure I2C is enabled (`sudo raspi-config`).
  - Verify the device shows on I2C bus: `i2cdetect -y 1`.
  - Check wiring and power (use 3.3V, not 5V, unless your breakout supports it).

- Display not initializing:
  - Confirm SPI is enabled.
  - Check that the `dc`, `cs`, and `backlight` pins are wired as in the script.
  - If using Pirate Audio, consult the HAT docs for the correct pin mapping and any required software.
  - Ensure the `st7789` library you installed is compatible with your display.

- Permission errors / GPIO access:
  - Run with `sudo` or configure correct group/udev rules for GPIO/SPI.

- NDEF reading:
  - The code reads NTAG blocks and looks for an NDEF Text record. If your tags use a different format, they might not be parsed.

## Extending / Improvements
- adding a medival astetic



## License
MIT License — see LICENSE file (add one to the repo if desired).

## Contact / Contributions
Open an issue or submit a PR to propose improvements or fixes.
