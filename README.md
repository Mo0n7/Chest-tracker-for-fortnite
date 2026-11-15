#  Fortnite Chest Tracker (Overlay)

A lightweight desktop overlay built with pure Python to track your chest openings during intense grind sessions.

###  Why does this exist?
Right now, the **Pirate Event** is live and players are grinding for the ultra-rare **Pirate Token** (with a brutal **1 in 137,000** base drop chance). When you're opening 500+ chests a day and thousands overall, losing track of your progress is painful.

This tool solves that: a minimal, non-intrusive click-through overlay that stays out of your way while you play.

---

### ⚠️ Disclaimer (Use at Your Own Risk)
This is an independent third-party overlay utility. While it is designed to be as non-invasive as possible, **no third-party software can ever be guaranteed 100% safe** against anti-cheat updates or heuristic flags. **Use this tool at your own risk** — the author takes no responsibility for any account restrictions or bans.

**How it works under the hood:**
* **No keyboard/mouse hooks** (unlike `pynput` or `keyboard` libraries). Uses native Windows `RegisterHotKey` API.
* **No screen capturing or OCR** — doesn't read pixels or capture your game window.
* **Zero memory/process access** — never touches Fortnite's files or RAM.

---

###  Features
* **Zero Dependencies:** Runs out of the box using only Python's standard library (`tkinter`, `ctypes`, `winreg`).
* **Click-Through Mode (Ghost Mode):** Lock the overlay so your mouse clicks pass straight through into the game.
* **Crash-Safe Auto-Save:** Uses atomic file replacement (`chest_stats.txt`) so your progress won't corrupt even if your PC loses power.
* **Progress & Percentage:** Tracks your current count against the 137,000 target with live percentage calculation.
* **Customizable:** Change hotkeys, colors, transparency, or autostart settings right at the top of the script.

---

###  Controls & Hotkeys

| Key / Action | Function |
| :--- | :--- |
| **`F8`** | `+1` Chest opened |
| **`F7`** | `-1` Undo (if you misclicked) |
| **`F9`** | Toggle **Click-Through Mode** (Lock/Unlock mouse interaction) |
| **`F10`** | Save and quit |
| **Left Click + Drag** | Move the overlay anywhere on screen (when unlocked) |
| **Right Click** | Open quick menu (`+1`, `-1`, `Reset`, `Quit`) |

---

###  Quick Start

1. Make sure you have **Python 3** installed.
2. Set Fortnite display mode to **Windowed Fullscreen** (required for Windows overlays to render on top).
3. Run the tracker:
   ```bash
   python chest_tracker.py
