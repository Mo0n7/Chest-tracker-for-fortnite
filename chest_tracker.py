
import os
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path

                                                                      
TARGET = 137000
INITIAL_COUNT = 0                                                      
SHOW_PERCENT = True
FONT = ("Consolas", 8)
TEXT_COLOR = "#E8E8E8"
BG_COLOR = "#000000"
ALPHA = 0.65
TRANSPARENT_BG = False                                              

AUTOSTART = False                                                             

                                                                              
HOTKEYS = {
    "add": "F8",
    "undo": "F7",
    "lock": "F9",
    "quit": "F10",
}

SAVE_FILE = Path(__file__).resolve().with_name("chest_stats.txt")
                                                                      

IS_WINDOWS = sys.platform.startswith("win")

MOD_ALT, MOD_CONTROL, MOD_SHIFT, MOD_NOREPEAT = 0x1, 0x2, 0x4, 0x4000
WM_HOTKEY = 0x0312

SPECIAL_VK = {
    "INSERT": 0x2D, "DELETE": 0x2E, "HOME": 0x24, "END": 0x23,
    "PAGEUP": 0x21, "PAGEDOWN": 0x22, "SPACE": 0x20, "TAB": 0x09,
    "NUM+": 0x6B, "NUM-": 0x6D, "NUM*": 0x6A, "NUM/": 0x6F,
}


def parse_hotkey(spec):
    """'ctrl+F8' -> (modifiers, virtual-key code)."""
    mods, vk = 0, None
    spec = spec.replace(" ", "").upper()
    if spec.endswith("NUM+"):
        vk = SPECIAL_VK["NUM+"]
        spec = spec[:-4]
    for part in spec.split("+"):
        if part == "":
            continue
        if part in ("CTRL", "CONTROL"):
            mods |= MOD_CONTROL
        elif part == "ALT":
            mods |= MOD_ALT
        elif part == "SHIFT":
            mods |= MOD_SHIFT
        elif part in SPECIAL_VK:
            vk = SPECIAL_VK[part]
        elif len(part) >= 2 and part[0] == "F" and part[1:].isdigit() and 1 <= int(part[1:]) <= 24:
            vk = 0x70 + int(part[1:]) - 1
        elif part.startswith("NUM") and part[3:].isdigit():
            vk = 0x60 + int(part[3:])
        elif len(part) == 1 and (part.isalnum()):
            vk = ord(part)
        else:
            raise ValueError(f"Невідома клавіша: {part}")
                                                                     
    if vk is None and spec.upper().endswith("NUM+"):
        vk = SPECIAL_VK["NUM+"]
    if vk is None:
        raise ValueError(f"Не вказано клавішу: {spec}")
    return mods, vk


                                                 
def load_state():
    state = {"count": INITIAL_COUNT, "x": None, "y": None}
    try:
        for line in SAVE_FILE.read_text(encoding="utf-8").splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                if k in state:
                    try:
                        state[k] = int(v.strip())
                    except ValueError:
                        pass
    except OSError:
        pass
    state["count"] = max(0, state["count"])
    return state


def save_state(count, x, y):
    tmp = SAVE_FILE.with_suffix(".tmp")
    try:
        tmp.write_text(f"count={count}\nx={x}\ny={y}\n", encoding="utf-8")
        os.replace(tmp, SAVE_FILE)                   
    except OSError:
        pass


                                                                 
def apply_autostart(enable):
    if not IS_WINDOWS:
        return
    try:
        import winreg
        run_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        name = "FortniteChestTracker"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_key, 0,
                            winreg.KEY_SET_VALUE) as key:
            if enable:
                pyw = Path(sys.executable).with_name("pythonw.exe")               
                exe = pyw if pyw.exists() else Path(sys.executable)
                script = Path(__file__).resolve()
                winreg.SetValueEx(key, name, 0, winreg.REG_SZ, f'"{exe}" "{script}"')
            else:
                try:
                    winreg.DeleteValue(key, name)
                except FileNotFoundError:
                    pass
    except Exception:
        pass


                                                           
def hotkey_thread(events):
    """RegisterHotKey і цикл повідомлень мають жити в одному потоці."""
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    ids = {}
    failed = False
    for i, (action, spec) in enumerate(HOTKEYS.items(), start=1):
        try:
            mods, vk = parse_hotkey(spec)
            if user32.RegisterHotKey(None, i, mods | MOD_NOREPEAT, vk):
                ids[i] = action
            else:
                failed = True                                       
        except ValueError:
            failed = True
    if failed:
        events.put("hotkey_fail")

    msg = wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
        if msg.message == WM_HOTKEY and msg.wParam in ids:
            events.put(ids[msg.wParam])


                                  
class ChestOverlay:
    def __init__(self):
        state = load_state()
        self.count = state["count"]
        self.locked = False
        self.hotkey_problem = False
        self.events = queue.Queue()

        self.root = tk.Tk()
        self.root.title("Chest Tracker")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg=BG_COLOR)
        if TRANSPARENT_BG and IS_WINDOWS:
            self.root.attributes("-transparentcolor", BG_COLOR)
        else:
            self.root.attributes("-alpha", ALPHA)

        self.label = tk.Label(self.root, text="", font=FONT, fg=TEXT_COLOR,
                              bg=BG_COLOR, padx=4, pady=1)
        self.label.pack()
        self.refresh()

        self.root.update_idletasks()
        w = self.root.winfo_reqwidth()
        x, y = state["x"], state["y"]
        if x is None or y is None:
            x = self.root.winfo_screenwidth() - w - 6
            y = 4
        self.root.geometry(f"+{x}+{y}")

        self._drag = (0, 0)
        for widget in (self.root, self.label):
            widget.bind("<ButtonPress-1>", self._drag_start)
            widget.bind("<B1-Motion>", self._drag_move)
            widget.bind("<ButtonRelease-1>", lambda e: self.save())
            widget.bind("<Button-3>", self._menu)

        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="+1", command=self.add)
        self.menu.add_command(label="-1", command=self.undo)
        self.menu.add_separator()
        self.menu.add_command(label="Скинути лічильник", command=self.reset)
        self.menu.add_command(label="Вийти", command=self.quit)

        if IS_WINDOWS:
            threading.Thread(target=hotkey_thread, args=(self.events,),
                             daemon=True).start()

        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self.root.after(30, self._poll)

                          
    def refresh(self):
        text = f"{self.count}/{TARGET}"
        if SHOW_PERCENT:
            text += f" {self.count / TARGET * 100:.1f}%"
        if self.hotkey_problem:
            text += " [!]"                                           
        self.label.config(text=text)

    def save(self):
        save_state(self.count, self.root.winfo_x(), self.root.winfo_y())

                 
    def add(self):
        self.count += 1
        self.refresh()
        self.save()

    def undo(self):
        if self.count > 0:
            self.count -= 1
            self.refresh()
            self.save()

    def reset(self):
        self.count = 0
        self.refresh()
        self.save()

    def toggle_lock(self):
        """Click-through: кліки проходять крізь оверлей (це лише власне вікно скрипта)."""
        self.locked = not self.locked
        if not IS_WINDOWS:
            return
        try:
            import ctypes
            user32 = ctypes.windll.user32
            hwnd = user32.GetParent(self.root.winfo_id()) or self.root.winfo_id()
            GWL_EXSTYLE = -20
            style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style |= 0x00080000 | 0x00000080                                
            if self.locked:
                style |= 0x00000020                                 
            else:
                style &= ~0x00000020
            user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        except Exception:
            pass

    def quit(self):
        self.save()
        self.root.destroy()

                  
    def _drag_start(self, e):
        self._drag = (e.x_root - self.root.winfo_x(), e.y_root - self.root.winfo_y())

    def _drag_move(self, e):
        dx, dy = self._drag
        self.root.geometry(f"+{e.x_root - dx}+{e.y_root - dy}")

    def _menu(self, e):
        self.menu.tk_popup(e.x_root, e.y_root)

                                          
    def _poll(self):
        try:
            while True:
                action = self.events.get_nowait()
                if action == "add":
                    self.add()
                elif action == "undo":
                    self.undo()
                elif action == "lock":
                    self.toggle_lock()
                elif action == "hotkey_fail":
                    self.hotkey_problem = True
                    self.refresh()
                elif action == "quit":
                    self.quit()
                    return
        except queue.Empty:
            pass
        self.root.after(30, self._poll)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    if IS_WINDOWS:
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            pass

    if "--set" in sys.argv:
        try:
            value = int(sys.argv[sys.argv.index("--set") + 1])
        except (IndexError, ValueError):
            print("Використання: python chest_tracker.py --set 1500")
            sys.exit(1)
        st = load_state()
        save_state(max(0, value), st["x"], st["y"])
        print(f"Лічильник встановлено: {max(0, value)}")
        sys.exit(0)

    apply_autostart(AUTOSTART)
    ChestOverlay().run()
