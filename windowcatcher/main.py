import argparse
import pyautogui
import time
import win32gui
import win32process
import pygetwindow
from PIL import Image
import screeninfo
import toml

def find_last_non_black_column(image_path):
    image = Image.open(image_path).convert("L")  # Grayscale
    width, height = image.size
    pixels = image.load()

    for x in range(width - 1, -1, -1):  # Bottom to top
        all_black = True
        for y in range(height):

            if pixels[x, y] > 120:
                all_black = False
                break
        if not all_black:
            print(f"Last non-black row (from right left) is at x = {x}")
            return x

    print("Image is completely black.")
    return -1

def find_last_non_black_row(image_path):
    image = Image.open(image_path).convert("L")  # Grayscale
    width, height = image.size
    pixels = image.load()

    for y in range(height - 1, -1, -1):  # Bottom to top
        all_black = True
        for x in range(width):

            if pixels[x, y] > 120:
                all_black = False
                break
        if not all_black:
            print(f"Last non-black row (from bottom up) is at y = {y}")
            return y

    print("Image is completely black.")
    return -1

def find_window_by_pid(pid):
    """
    Find the window handle (hwnd) for the given process ID.
    """
    def callback(hwnd, hwnds):
        try:
            _, found_pid = win32process.GetWindowThreadProcessId(hwnd)
            if found_pid == pid and win32gui.IsWindowVisible(hwnd):
                hwnds.append(hwnd)
        except:
            pass
        return True

    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds

def foreground_terminal(pid):
    hwnds = find_window_by_pid(pid)
    if not hwnds:
        print(f"No visible window found for PID {pid}")
        return False
    
    win32gui.ShowWindow(hwnds[0], 5)  # SW_SHOW
    win32gui.SetForegroundWindow(hwnds[0])
    time.sleep(0.5)  # Give focus time to apply
    return True

def save_pic(path, title):
    w = pygetwindow.getWindowsWithTitle(title)[0]
    screen_width = 0
    for m in screeninfo.get_monitors():
        if m.is_primary:
            screen_width = m.width
    left, top = w.topleft
    right, bottom = w.bottomright
    extra = screen_width * 0.005

    pyautogui.screenshot(path)
    im = Image.open(path)
    im = im.crop((left + extra, top + (extra * 3.5), right - extra, bottom))
    im.save(path)
    y = find_last_non_black_row(path)
    im = im.crop((0, 0, im.width, y))
    im.save(path)
    im = Image.open(path)
    x = find_last_non_black_column(path)
    im = im.crop((0, 0, x, im.height))
    im.save(path)

def type_to_screen(message):
    pyautogui.typewrite(message)
    pyautogui.press('enter')

# Load and process TOML config
def process_elements(pid, config_path, title, output_directory):
    config = toml.load(config_path)
    actions = config.get("actions", [])

    if not foreground_terminal(pid):
        return

    for action in actions:
        name = action.get("name")
        command = action.get("command")
        output = action.get("output")

        try:
            type_to_screen(command)
            save_pic(f"{output_directory}/{output}", title)

        except Exception as e:
            print(f"  ⚠️ Error during processing: {e}")

def main():
    parser = argparse.ArgumentParser(description="Type into a window by PID using pyautogui.")
    parser.add_argument("pid", type=int, help="PID of the target window's process")
    parser.add_argument("title", type=str, help="Terminal Title")
    parser.add_argument("toml-file", type=str, help="Path to the TOML configuration file.")
    parser.add_argument("output-directory", type=str, help="Path to the directory that images will be saved.")


    args = parser.parse_args()

    process_elements(args.pid, args.toml_file, args.title, args.output_directory)

if __name__ == "__main__":
    main()
