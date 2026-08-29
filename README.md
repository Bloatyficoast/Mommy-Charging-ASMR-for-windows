## How to Install & Run – Mommy Charging ASMR
1. Install Python

Go to https://www.python.org/downloads/
Download the latest version
Run the installer
Important: Check the box “Add Python to PATH”
Click Install

2. Download the project

Download the ZIP from GitHub and extract it,
or
Clone it with Git:Bashgit clone https://github.com/Bloatyficoast/Mommy-Charging-ASMR-for-windows.git

3. Open the folder
Open Command Prompt and go into the project folder:
Bashcd "C:\Users\YOUR_USER\Downloads\Mommy Voice Charging!!"
(Change the path if your folder is somewhere else)
4. Install required packages
Bashpip install -r requirements.txt
5. Run the app
Bashpython battery_watt_tray.py
You will see this question:
textRun in background? (y/n):

Type y → App runs silently in the background (no black window)
Type n → App runs in the current window

6. Using the app

Look for the icon in the system tray (bottom-right, near the clock)
Hover over it to see battery % and charging watts
Right-click the icon → Quit to close it
Plug / unplug your charger to hear the voice clips


Optional: Start automatically when Windows boots

Press Win + R
Type shell:startup and press Enter
Create a shortcut to battery_watt_tray.py and put it in that folder
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
