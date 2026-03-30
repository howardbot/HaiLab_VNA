# HaiLab_VNA

Python scripts for remote control of the Agilent/Keysight E5061 Vector Network Analyzer (VNA) over Ethernet (SCPI/VISA). Used to collect S11 measurements synchronized with neural recording hardware (TDT Synapse).

---

## Files

### `Remote Control(10Hz)_E5061B.py`
Original VNA remote control script. Collects S11 traces at 10 Hz and saves to CSV. Supports low/high frequency presets (`lo`/`hi`).

### `Remote Control(10Hz Jack).py`
Updated version (Jack, Jan 2021). Adds custom frequency range input — e.g., `s 100 500` sets a range in Hz or MHz in addition to `lo`/`hi` presets.

### `Adam_VNA.py`
Systematic single-trace capture script that walks through every device in a die automatically. Designed for measuring a full pad of devices organized in a die grid.

**Startup prompts:**
1. Die number
2. Die dimension — X and Y count (e.g., `4 5` for a 4×5 grid)
3. Traversal order — `x` (X-first: X1Y1 → X2Y1 → ...) or `y` (Y-first: X1Y1 → X1Y2 → ...)

**Per-device loop:**
- Shows the current device name and progress (e.g., `[3/20] Die1_X3Y1`)
- Press **Enter** to capture one trace and auto-advance to the next device
- Type `s` to skip the current device
- Type `freq` to change the frequency range at any point
- Type `q` to quit

**Output folder structure example (4×2 die, X-first):**
```
Die1_X1Y1/Die1_X1Y1.csv
Die1_X2Y1/Die1_X2Y1.csv
Die1_X3Y1/Die1_X3Y1.csv
Die1_X4Y1/Die1_X4Y1.csv
Die1_X1Y2/Die1_X1Y2.csv
...
```

**CSV format:**
```
Frequency(Hz),dB
300000.0,-12.34
...
```

### `Adam_VNA_plot.py`
Auto-detects all data collected by `Adam_VNA.py` and plots it interactively. Run from the same folder that contains the `Die*_*` subfolders.

**Features:**
- Scans the current directory for all `Die{number}_{Row}{Col}/` folders and their CSVs
- Overlays all traces for a single device on one axes (color-coded by trace number)
- Plots an entire die as a subplot grid (one subplot per device)
- Plots all detected data at once (one figure per die)
- `rescan` command picks up newly captured data without restarting

**Commands:**

| Command | Action |
|---|---|
| `[Enter]` / `all` | Plot every detected device, grouped by die |
| `die <number>` | Plot all devices in one die (e.g. `die 3`) |
| `dev <name>` | Plot all traces for one device (e.g. `dev Die3_B2`) |
| `ls` | List all detected devices and trace counts |
| `rescan` | Re-scan directory for new data |
| `h` | Show help |
| `q` | Quit |

Add `-s` to any plot command to save the figure as a PNG instead of displaying it:

| Command | Saves to |
|---|---|
| `dev Die3_X2Y4 -s` | `Die3_X2Y4/Die3_X2Y4_plot.png` |
| `die 3 -s` | `Die3_X*Y*/Die3_overview.png` (one copy per device folder in die) |
| `all -s` | Same as above, for every die |

**Plot axes:** X = Frequency (MHz), Y = S11 (dB)

---

## Requirements

- `pyvisa` — VISA instrument communication
- `tdt` — TDT Synapse API (for sync scripts only)
- `matplotlib`, `numpy` — plotting (`Adam_VNA_plot.py` only)
- VNA connected at `192.168.0.1` over Ethernet

## Hardware

- Agilent/Keysight E5061A/B Vector Network Analyzer
- TDT (Tucker-Davis Technologies) Synapse neural recording system
