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
BUTTONS = [5, 6, 16] 
HOLD_DELAY = 2.0

# Globals
current_selection = 0
last_scan_time = 0

# Colors
GOLD = (212, 175, 55)
GLOW_BLUE = (0, 255, 230)       # Bright blue for selection
GHOST_BLUE = (0, 80, 150)       # Deep mystical blue for other items
DEEP_VOID = (5, 5, 15)

# --- 2. HARDWARE INITIALIZATION ---
i2c = busio.I2C(board.SCL, board.SDA)
try:
    pn532 = PN532_I2C(i2c, debug=False)
    pn532.SAM_configuration()
    print("NFC: Runic Link Established")
except Exception as e:
    print(f"NFC: Connection Failed ({e})")
    pn532 = None

disp = st7789.ST7789(
    port=0, cs=1, dc=9, backlight=13,
    spi_speed_hz=40 * 1000 * 1000,
    width=240, height=240, rotation=90
)
disp.begin()

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# --- 3. THE TRANSMUTER ---

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
    # Create the dark void background
    bg = Image.new("RGB", (240, 240), DEEP_VOID)
    draw = ImageDraw.Draw(bg)
    
    try:
        # 1. Load and Paste the M0D icon at 40x40
        icon = Image.open("M0D.png").convert("RGBA").resize((40, 40))
        # Pasting at (100, 30) centers it horizontally (240/2 - 40/2 = 100)
        bg.paste(icon, (100, 30), icon)
        
        # 2. Setup Fonts
        rune_font_large = ImageFont.truetype(RUNE_FONT_PATH, 45)
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    except Exception as e:
        print(f"Bootup Assets Missing: {e}")
        rune_font_large = title_font = ImageFont.load_default()

    # 3. Draw the Runic Title (Center-ish)
    # "RUNIC" in runes
    draw.text((45, 85), to_runes("RUNIC"), font=rune_font_large, fill=GLOW_BLUE)
    
    # 4. Draw "KEEPER" in English
    draw.text((75, 145), "KEEPER", font=title_font, fill=GOLD)
    
    # 5. Draw the decorative corner runes
    draw_rune_border(draw)

    # Display to screen
    disp.display(bg)
    time.sleep(2.5)
# --- 4. UI FUNCTIONS ---
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
                # Active Selection (Bright Blue + Border)
                draw.rectangle((10, y_pos - 4, 230, y_pos + 38), outline=GLOW_BLUE, width=2)
                draw.text((20, y_pos), inventory[i].upper(), font=latin_font, fill=GLOW_BLUE)
                draw.text((175, y_pos + 2), to_runes(inventory[i][:4]), font=rune_font, fill=GOLD)
            else:
                # Inactive Items (Now Ghostly Blue Runes)
                draw.text((20, y_pos), to_runes(inventory[i]), font=rune_font, fill=GHOST_BLUE)

    draw_rune_border(draw)
    disp.display(bg)

def toggle_item(item_name):
    global current_selection
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

# --- 5. INTERACTION LOGIC ---

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

def handle_button(pin):
    global current_selection
    inv = load_inventory()
    
    if pin == 5 and inv: 
        current_selection = (current_selection - 1) % len(inv)
    elif pin == 6 and inv: 
        current_selection = (current_selection + 1) % len(inv)
    elif pin == 16: 
        start_time = time.time()
        while GPIO.input(16) == GPIO.LOW:
            if time.time() - start_time > HOLD_DELAY:
                open(INVENTORY_FILE, "w").close()
                current_selection = 0
                show_inventory()
                return
            time.sleep(0.1)
    show_inventory()

# --- 6. MAIN LOOP ---
bootup()
show_inventory()

for p in BUTTONS:
    GPIO.add_event_detect(p, GPIO.FALLING, callback=handle_button, bouncetime=300)

try:
    while True:
        scanned = read_ndef_text()
        if scanned and (time.time() - last_scan_time > 3):
            toggle_item(scanned)
            last_scan_time = time.time()
        time.sleep(0.1)
except KeyboardInterrupt:
    GPIO.cleanup()
