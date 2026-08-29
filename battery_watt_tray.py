"""
Battery / Charger Power Indicator - Windows tray app
------------------------------------------------------
Shows battery percentage in the system tray. When a charger is plugged in,
switches the icon/tooltip to show charging wattage (when the system exposes it).

Also plays your own custom MP3 voice clips when you plug in / unplug, and
whenever the charging wattage changes by more than WATT_CHANGE_THRESHOLD
watts.

Requires (Windows only):
    pip install pystray Pillow wmi pywin32
"""

import sys
import time
import threading
import random
import os
import subprocess
from ctypes import windll

if sys.platform != "win32":
    print("This app only runs on Windows (uses WMI / Win32 battery APIs).")
    sys.exit(1)

import pythoncom
import wmi
from PIL import Image, ImageDraw, ImageFont
import pystray

REFRESH_SECONDS = 3

VOICE_ENABLED = True
WATT_CHANGE_THRESHOLD = 5.0
MIN_SECONDS_BETWEEN_ANNOUNCEMENTS = 8

SOUNDS_DIR = "sounds"

SOUND_FILES = {
    "plugged_in": [
        "Mommy-2026-08-29-16-09-You're-all-set-baby,-charging-at-45-watts.-you'r(1).mp3",
        "Mommy-2026-08-29-16-13-Good-boy,-you're-plugged-in-and-charging-at-45-w.mp3",
        "Mommy-2026-08-29-16-17-Good-boy-you're-plugged-in-now.-mmmm-i-can-feel.mp3",
    ],
    "plugged_in_no_watts": [
        "Mommy-2026-08-29-16-14-Charger's-connected.-You're-such-a-good-boy...-f.mp3",
        "Mommy-2026-08-29-16-17-Good-boy-you're-plugged-in-now.-mmmm-i-can-feel.mp3",
    ],
    "unplugged": [
        "Mommy-2026-08-29-16-18-You're-unplugged,-at-80-percent.-you-filled-me-u.mp3",
    ],
    "wattage_change": [
        "1.mp3",
        "Mommy-2026-08-29-16-19-Just-letting-you-know,-charging-speed-shifted-to.mp3",
    ],
}


def play_mp3(path: str):
    """Play an MP3 using Windows MCI (no extra packages needed)."""
    path = os.path.abspath(path)
    windll.winmm.mciSendStringW('close mommy_sound', None, 0, 0)
    windll.winmm.mciSendStringW(f'open "{path}" type mpegvideo alias mommy_sound', None, 0, 0)
    windll.winmm.mciSendStringW('play mommy_sound wait', None, 0, 0)
    windll.winmm.mciSendStringW('close mommy_sound', None, 0, 0)


def get_battery_info():
    c = wmi.WMI()
    batteries = c.Win32_Battery()

    if not batteries:
        return {"percent": None, "charging": False, "watts": None}

    batt = batteries[0]
    percent = batt.EstimatedChargeRemaining

    status = batt.BatteryStatus
    charging = status in (2, 6, 7, 8, 9)

    watts = None
    try:
        wmi_root = wmi.WMI(namespace="root\\wmi")
        status_objs = wmi_root.BatteryStatus()
        if status_objs:
            s = status_objs[0]
            charge_rate = getattr(s, "ChargeRate", None)
            discharge_rate = getattr(s, "DischargeRate", None)
            if charging and charge_rate:
                watts = charge_rate / 1000.0
            elif not charging and discharge_rate:
                watts = discharge_rate / 1000.0
    except Exception:
        watts = None

    return {"percent": percent, "charging": charging, "watts": watts}


def make_icon_image(text, charging):
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    bg_color = (30, 150, 60, 255) if charging else (60, 60, 60, 255)
    draw.rounded_rectangle([2, 10, size - 2, size - 10], radius=10, fill=bg_color)

    try:
        font = ImageFont.truetype("arial.ttf", 22 if len(text) <= 3 else 16)
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - w) / 2, (size - h) / 2 - bbox[1]), text, fill="white", font=font)
    return img


def build_tooltip(info):
    pct = info["percent"]
    if info["charging"]:
        if info["watts"]:
            return f"Charging - {info['watts']:.1f}W ({pct}%)"
        return f"Charging ({pct}%) - wattage not available on this hardware"
    return f"On battery - {pct}%"


def build_label(info):
    if info["charging"] and info["watts"]:
        return f"{info['watts']:.0f}W"
    if info["percent"] is not None:
        return f"{info['percent']}%"
    return "?"


class Speaker:
    def __init__(self, sounds_dir, sound_files):
        self._queue = []
        self._lock = threading.Lock()
        self._wake = threading.Event()
        self._sounds_dir = sounds_dir
        self._sound_files = sound_files
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def play(self, event_key):
        files = self._sound_files.get(event_key)
        if not files:
            return
        if isinstance(files, str):
            files = [files]
        candidates = []
        for name in files:
            path = os.path.join(self._sounds_dir, name)
            if os.path.isfile(path):
                candidates.append(path)
            else:
                print(f"[Speaker] Missing sound file: {path}")
        if not candidates:
            return
        chosen = random.choice(candidates)
        with self._lock:
            self._queue.append(chosen)
        self._wake.set()

    def _run(self):
        while True:
            self._wake.wait()
            with self._lock:
                items = self._queue[:]
                self._queue.clear()
                self._wake.clear()
            for path in items:
                self._play_file(path)

    def _play_file(self, path):
        try:
            play_mp3(path)
        except Exception as e:
            print(f"[Speaker] Playback error for '{path}': {e}")


def update_loop(icon: pystray.Icon, speaker: Speaker):
    # COM must be initialized in every thread that uses WMI
    pythoncom.CoInitialize()

    last_watts = None
    last_charging = None
    last_announce_time = 0.0

    try:
        while True:
            info = get_battery_info()
            label = build_label(info)
            icon.icon = make_icon_image(label, info["charging"])
            icon.title = build_tooltip(info)

            if VOICE_ENABLED:
                now = time.time()
                watts = info["watts"]
                charging = info["charging"]

                if charging != last_charging and now - last_announce_time >= MIN_SECONDS_BETWEEN_ANNOUNCEMENTS:
                    if charging and watts:
                        speaker.play("plugged_in")
                    elif charging:
                        speaker.play("plugged_in_no_watts")
                    else:
                        speaker.play("unplugged")
                    last_announce_time = now
                    last_watts = watts
                    last_charging = charging

                elif (
                    charging
                    and watts is not None
                    and last_watts is not None
                    and abs(watts - last_watts) >= WATT_CHANGE_THRESHOLD
                    and now - last_announce_time >= MIN_SECONDS_BETWEEN_ANNOUNCEMENTS
                ):
                    speaker.play("wattage_change")
                    last_announce_time = now
                    last_watts = watts

                last_charging = charging
                if watts is not None:
                    last_watts = watts

            time.sleep(REFRESH_SECONDS)
    finally:
        pythoncom.CoUninitialize()


def on_quit(icon, item):
    icon.stop()


def run_in_background():
    """
    Relaunch this script using pythonw.exe so it runs without a console window.
    """
    script = os.path.abspath(sys.argv[0])
    # Prefer pythonw.exe (no console). Fall back to python.exe with CREATE_NO_WINDOW.
    pythonw = sys.executable.replace("python.exe", "pythonw.exe")
    if not os.path.isfile(pythonw):
        pythonw = sys.executable

    CREATE_NO_WINDOW = 0x08000000
    DETACHED_PROCESS = 0x00000008

    flags = CREATE_NO_WINDOW | DETACHED_PROCESS

    subprocess.Popen(
        [pythonw, script, "--background"],
        creationflags=flags,
        close_fds=True,
    )
    print("Started in background. You can close this window.")
    sys.exit(0)


def main():
    # Already launched in background mode → skip the prompt
    if "--background" in sys.argv:
        pass
    else:
        # First launch: ask the user
        answer = input("Run in background? (y/n): ").strip().lower()
        if answer in ("y", "yes"):
            run_in_background()
            return
        # If n (or anything else), just continue and run normally

    initial = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    menu = pystray.Menu(
        pystray.MenuItem("Battery / Charger Power Indicator", None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", on_quit),
    )
    icon = pystray.Icon("battery_watt", initial, "Battery", menu)

    speaker = Speaker(SOUNDS_DIR, SOUND_FILES)
    t = threading.Thread(target=update_loop, args=(icon, speaker), daemon=True)
    t.start()

    icon.run()


if __name__ == "__main__":
    main()