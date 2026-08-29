# Battery / Charger Power Indicator (Windows)

System-tray app that shows battery percentage, and charging wattage when available. Plays your custom MP3 voice clips when you plug in, unplug, or when charging power changes significantly.

## Setup

1. Install Python 3.10+ from python.org (tick “Add to PATH”).
2. Open Command Prompt in this folder and run: pip install -r requirements.txt
3. Make sure the `sounds` folder (with your MP3s) sits next to `battery_watt_tray.py`.
4. Start the app: python battery_watt_tray.py
5. When asked “Run in background? (y/n)”:
- **y** → restarts silently with no console window
- **n** → runs in the current terminal

## Usage

- Hover the tray icon for battery % and wattage (if supported by your laptop).
- Right-click the icon → Quit to stop.
- Plug/unplug the charger or wait for a big wattage change to hear your voice clips.

## Optional: Start with Windows

Press `Win + R`, type `shell:startup`, and drop a shortcut to the script (or a `.bat` that runs it) into that folder.

## Notes

- Real-time wattage is not available on every laptop — it depends on the hardware.
- This project was created with the help of AI.

## Requirements
- nothing have fun with it and wait for upcoming updates in the future!