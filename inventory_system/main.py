import time
import board
import busio
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont
import st7789 as st7789
import ndef
from adafruit_pn532.i2c import PN532_I2C
import os

# --- 1. CONFIGURATION & MAGICAL THEME ---
RUNE_FONT_PATH = "BabelStoneRunic.ttf"
INVENTORY_FILE = "inventory.txt"
BUTTONS = [16, 24] # Pin 6 removed as it wasn't used in your logic
HOLD_DELAY = 2.0

# Globals
current_selection = 0
last_scan_time = 0

# Colors
GOLD = (212, 175, 55)
GLOW_BLUE = (0, 255, 230)
GHOST_BLUE = (0, 80, 150)
DEEP_VOID = (5, 5, 15)

# --- 2. HARDWARE INITIALIZATION ---
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# NFC Setup
i2c = busio.I2C(board.SCL, board.SDA)
try:
    pn532 = PN532_I2C(i2c, debug=False)
    pn532.SAM_configuration()
    print("NFC: Runic Link Established")
except Exception as e:
    print(f"NFC: Connection Failed ({e})")
    pn532 = None

# Display Setup
disp = st7789.ST7789(
    port=0, cs=1, dc=9, backlight=13,
    spi_speed_hz=40 * 1000 * 1000,
    width=240, height=240, rotation=90
)
disp.begin()

# --- 3. THE TRANSMUTER (HELPER FUNCTIONS) ---

def to_runes(text):
    mapping = {
        'a': 'ᚨ', 'b': 'ᛒ', 'c': 'ᚲ', 'd': 'ᛞ', 'e': 'ᛖ', 
        'f': 'ᚠ', 'g': 'ᚷ', 'h': 'ᚼ', 'i': 'ᛁ', 'j': 'ᛃ', 
        'k': 'ᚲ', 'l': 'ᛚ', 'm': 'ᛗ', 'n': 'ᚾ', 'o': 'ᛟ', 
        'p': 'ᛈ', 'q': 'ᚲ', 'r': 'ᚱ', 's': 'ᛊ', 't': 'ᛏ', 
        'u': 'ᚢ', 'v': 'ᚠ', 'w': 'ᚿ', 'x': 'ᛄ', 'y': 'ᛦ', 'z': 'ᛉ',
        ' ': ' '
    }
    return "".join(mapping.get(c.lower(), '᛫') for c in text)

def load_inventory():
    try:
        if not os.path.exists(INVENTORY_FILE): return []
        with open(INVENTORY_FILE, "r") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    except: return []

def draw_rune_border(draw):
    try:
        corner_font = ImageFont.truetype(RUNE_FONT_PATH, 20)
        draw.text((5, 5), "ᚠ", font=corner_font, fill=GOLD)
        draw.text((215, 5), "ᚢ", font=corner_font, fill=GOLD)
        draw.text((5, 215), "ᛏ", font=corner_font, fill=GOLD)
        draw.text((215, 215), "ᛟ", font=corner_font, fill=GOLD)
    except: pass

def bootup():
    bg = Image.new("RGB", (240, 240), DEEP_VOID)
    draw = ImageDraw.Draw(bg)
    try:
        if os.path.exists("M0D.png"):
            icon = Image.open("M0D.png").convert("RGBA").resize((40, 40))
            bg.paste(icon, (100, 30), icon)
        rune_font_large = ImageFont.truetype(RUNE_FONT_PATH, 45)
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    except:
        rune_font_large = title_font = ImageFont.load_default()

    draw.text((45, 85), to_runes("RUNIC"), font=rune_font_large, fill=GLOW_BLUE)
    draw.text((75, 145), "KEEPER", font=title_font, fill=GOLD)
    draw_rune_border(draw)
    disp.display(bg)
    time.sleep(2.5)

def show_inventory():
    global current_selection 
    inventory = load_inventory()
    bg = Image.new("RGB", (240, 240), DEEP_VOID)
    draw = ImageDraw.Draw(bg)
    
    try:
        rune_font = ImageFont.truetype(RUNE_FONT_PATH, 26)
        latin_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
    except:
        rune_font = latin_font = ImageFont.load_default()

    if not inventory:
        draw.text((65, 110), "᛫ EMPTY ᛫", font=rune_font, fill=GHOST_BLUE)
    else:
        if current_selection >= len(inventory): current_selection = 0
        start = max(0, current_selection - 2)
        end = min(len(inventory), start + 5)
        
        for i in range(start, end):
            rel_idx = i - start
            y_pos = 20 + (rel_idx * 44)
            if i == current_selection:
                draw.rectangle((10, y_pos - 4, 230, y_pos + 38), outline=GLOW_BLUE, width=2)
                draw.text((20, y_pos), inventory[i].upper(), font=latin_font, fill=GLOW_BLUE)
                draw.text((175, y_pos + 2), to_runes(inventory[i][:4]), font=rune_font, fill=GOLD)
            else:
                draw.text((20, y_pos), to_runes(inventory[i]), font=rune_font, fill=GHOST_BLUE)

    draw_rune_border(draw)
    disp.display(bg)

def toggle_item(item_name):
    current_list = load_inventory()
    if item_name in current_list:
        current_list.remove(item_name)
        status, color = "FREED", (80, 20, 20)
    else:
        current_list.append(item_name)
        status, color = "BOUND", (20, 60, 40)

    with open(INVENTORY_FILE, "w") as f:
        for item in current_list: f.write(f"{item}\n")

    fb = Image.new("RGB", (240, 240), color)
    draw = ImageDraw.Draw(fb)
    try:
        f_rune = ImageFont.truetype(RUNE_FONT_PATH, 50)
        draw.text((30, 60), to_runes(status), font=f_rune, fill=GOLD)
    except:
        draw.text((30, 60), status, fill=GOLD)
    
    disp.display(fb)
    time.sleep(1.2)
    show_inventory()

def read_ndef_text():
    if pn532 is None: return None
    uid = pn532.read_passive_target(timeout=0.1)
    if uid:
        try:
            all_data = bytearray()
            for block in range(4, 16):
                data = pn532.ntag2xx_read_block(block)
                if data: all_data.extend(data)
            if 0x03 in all_data:
                start = all_data.find(0x03) + 2
                records = list(ndef.message_decoder(all_data[start:]))
                for r in records:
                    if isinstance(r, ndef.TextRecord): return r.text
        except: pass
    return None

# --- 4. MAIN LOOP ---

bootup()
show_inventory()

try:
    while True:
        # Check Button 24 (UP)
        if GPIO.input(24) == GPIO.LOW:
            inv = load_inventory()
            if inv:
                current_selection = (current_selection - 1) % len(inv)
                show_inventory()
            # Wait for button release (debounce)
            while GPIO.input(24) == GPIO.LOW: time.sleep(0.05)

        # Check Button 16 (DOWN or LONG PRESS)
        if GPIO.input(16) == GPIO.LOW:
            press_time = time.time()
            is_long_press = False
            
            while GPIO.input(16) == GPIO.LOW:
                if time.time() - press_time > HOLD_DELAY:
                    # Trigger Inventory Clear
                    open(INVENTORY_FILE, "w").close()
                    current_selection = 0
                    is_long_press = True
                    show_inventory()
                    while GPIO.input(16) == GPIO.LOW: time.sleep(0.05)
                    break
                time.sleep(0.05)
            
            if not is_long_press:
                inv = load_inventory()
                if inv:
                    current_selection = (current_selection + 1) % len(inv)
                    show_inventory()

        # Check NFC
        scanned = read_ndef_text()
        if scanned and (time.time() - last_scan_time > 3):
            toggle_item(scanned)
            last_scan_time = time.time()
            
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nClosing Runic Link...")
finally:
    GPIO.cleanup()
