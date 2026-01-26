import time
import board
import busio
import RPi.GPIO as GPIO
from PIL import Image, ImageDraw, ImageFont
import st7789 as st7789
import ndef
from adafruit_pn532.i2c import PN532_I2C

# --- 1. NFC Initialization (I2C) ---
# Start this first to ensure a clean handshake with the PN532
i2c = busio.I2C(board.SCL, board.SDA)
try:
    pn532 = PN532_I2C(i2c, debug=False)
    pn532.SAM_configuration()
    print("NFC Reader: Online")
except Exception as e:
    print(f"NFC Reader: Failed ({e})")
    pn532 = None

# --- 2. Display Initialization (SPI) ---
disp = st7789.ST7789(
    port=0,
    cs=1,            
    dc=9,
    backlight=13,    
    spi_speed_hz=40 * 1000 * 1000,
    width=240,
    height=240,
    rotation=90
)
disp.begin()

# --- 3. GPIO & Global Config ---
BUTTONS = [5, 6, 16]
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTONS, GPIO.IN, pull_up_down=GPIO.PUD_UP)

inventory_file = "inventory.txt"
current_selection = 0
MAX_VISIBLE_ITEMS = 5
SPACING = 45
HOLD_DELAY = 2.0  
last_scan_time = 0 

# --- 4. Helper Functions ---
def load_inventory():
    try:
        with open(inventory_file, "r") as file:
            return [line.strip() for line in file.readlines() if line.strip()]
    except FileNotFoundError:
        return []

def read_ndef_text():
    """Exact NTAG block reading logic."""
    if pn532 is None: return None
    uid = pn532.read_passive_target(timeout=0.1)
    
    if uid is not None:
        all_data = bytearray()
        try:
            for block in range(4, 20):
                data = pn532.ntag2xx_read_block(block)
                if data is not None:
                    all_data.extend(data)
            
            if 0x03 in all_data:
                start_index = all_data.find(0x03) + 2 
                records = list(ndef.message_decoder(all_data[start_index:]))
                for record in records:
                    if isinstance(record, ndef.TextRecord):
                        return record.text
        except Exception as e:
            print(f"Read error: {e}")
    return None

def toggle_item(item_name):
    """Adds/Removes item and shows BIG text feedback."""
    global inventory, current_selection
    current_list = load_inventory()
    
    if item_name in current_list:
        current_list.remove(item_name)
        color, msg = (180, 0, 0), "REMOVED"
    else:
        current_list.append(item_name)
        color, msg = (0, 160, 0), "ADDED"

    with open(inventory_file, "w") as f:
        for item in current_list:
            f.write(f"{item}\n")
    
    inventory = current_list
    
    # BIG TEXT ALERT SCREEN
    fb = Image.new("RGB", (240, 240), color)
    draw_f = ImageDraw.Draw(fb)
    
    try:
        status_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 45)
        item_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    except:
        status_font = ImageFont.load_default()
        item_font = ImageFont.load_default()

    # Draw Centered Status
    draw_f.text((15, 60), msg, font=status_font, fill=(255, 255, 255))
    
    # Draw Item Name (Truncated for fit)
    display_name = (item_name[:12] + "..") if len(item_name) > 12 else item_name
    draw_f.text((15, 130), display_name, font=item_font, fill=(255, 255, 255))
    
    disp.display(fb)
    time.sleep(1.5)
    show_inventory()

# --- 5. UI Functions ---
def bootup():
    bg = Image.new("RGB", (240, 240), (0, 0, 0))
    draw = ImageDraw.Draw(bg)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 19)
        icon = Image.open("M0D.png").convert("RGBA").resize((160, 160))
        bg.paste(icon, (40, 20), icon)
    except:
        font = ImageFont.load_default()

    draw.text((45, 200), "Adventuring Inventory", font=font, fill=(255, 255, 255)) 
    disp.display(bg)
    time.sleep(2)

def show_inventory():
    global current_selection, inventory
    inventory = load_inventory()
    bg = Image.new("RGB", (240, 240), (0, 0, 0))
    draw = ImageDraw.Draw(bg)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except:
        font = ImageFont.load_default()

    if not inventory:
        draw.text((65, 110), "[ EMPTY ]", font=font, fill=(100, 100, 100))
        disp.display(bg)
        return

    # Scrolling Logic
    start_index = max(0, current_selection - (MAX_VISIBLE_ITEMS // 2))
    end_index = min(len(inventory), start_index + MAX_VISIBLE_ITEMS)
    if end_index == len(inventory):
        start_index = max(0, end_index - MAX_VISIBLE_ITEMS)

    for i in range(start_index, end_index):
        rel_idx = i - start_index
        y_pos = 10 + (rel_idx * SPACING)
        color = (0, 255, 0) if i == current_selection else (255, 255, 255)
        if i == current_selection:
            draw.rectangle((5, y_pos - 2, 235, y_pos + 37), fill=(50, 50, 50))
        draw.text((15, y_pos), f"{inventory[i]}", font=font, fill=color)

    disp.display(bg)

# --- 6. Interaction ---
def handle_button(pin):
    global current_selection, inventory
    inventory = load_inventory()
    list_size = len(inventory)
    if pin == 5 and list_size > 0:
        current_selection = (current_selection - 1) % list_size
    elif pin == 6 and list_size > 0:
        current_selection = (current_selection + 1) % list_size
    elif pin == 16:
        start_hold = time.time()
        while GPIO.input(pin) == GPIO.LOW:
            if time.time() - start_hold > HOLD_DELAY:
                with open(inventory_file, "w") as f: f.write("")
                inventory = []; current_selection = 0
                show_inventory()
                return
            time.sleep(0.05)
    show_inventory()

# --- 7. Main Loop ---
bootup()
show_inventory()

for p in [5, 6, 16]:
    GPIO.add_event_detect(p, GPIO.FALLING, callback=handle_button, bouncetime=300)

try:
    while True:
        scanned_name = read_ndef_text()
        if scanned_name and (time.time() - last_scan_time > 3):
            toggle_item(scanned_name)
            last_scan_time = time.time()
        time.sleep(0.1) 
except KeyboardInterrupt:
    GPIO.cleanup()