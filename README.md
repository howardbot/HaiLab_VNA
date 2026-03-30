# HaiLab_VNA

Python scripts for remote control of the Agilent/Keysight E5061 Vector Network Analyzer (VNA) over Ethernet (SCPI/VISA). Used to collect S11 measurements synchronized with neural recording hardware (TDT Synapse).

---

## Files

### `Remote Control(10Hz)_E5061B.py`
Original VNA remote control script. Collects S11 traces at 10 Hz and saves to CSV. Supports low/high frequency presets (`lo`/`hi`).

### `Remote Control(10Hz Jack).py`
Updated version (Jack, Jan 2021). Adds custom frequency range input — e.g., `s 100 500` sets a range in Hz or MHz in addition to `lo`/`hi` presets.

### `Adam_VNA.py`
Single-trace capture script organized by die and device position. Designed for systematic measurement of devices arranged in a die grid.

**Features:**
- Press **Enter** to capture one S11 trace (no continuous recording)
- Saves **Frequency (Hz)** and **dB** (log magnitude) columns to CSV
- Each device gets its own subfolder named `Die{number}_{Row}{Col}` (e.g., `Die3_B2/`)
- Traces within a subfolder are auto-numbered: `Die3_B2_trace001.csv`, `Die3_B2_trace002.csv`, ...
- User sets die number and row/column label at startup or any time mid-session

**Commands:**

| Command | Action |
|---|---|
| `[Enter]` | Capture one trace and save to CSV |
| `d` | Set die number and device position (row/column) |
| `freq` | Set start/stop frequency range (Hz) |
| `h` | Show help |
| `q` | Quit and close connections |

**Output folder structure example:**
```
Die3_B2/
    Die3_B2_trace001.csv
    Die3_B2_trace002.csv
Die3_C1/
    Die3_C1_trace001.csv
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

Append `save` to any plot command to save the figure as a PNG into the corresponding folder:

| Command | Saves to |
|---|---|
| `dev Die3_B2 save` | `Die3_B2/Die3_B2_plot.png` |
| `die 3 save` | `Die3_*/Die3_overview.png` (one copy per device folder in die) |
| `all save` | Same as above, for every die |

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
