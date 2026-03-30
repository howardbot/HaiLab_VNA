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

---

## Requirements

- `pyvisa` — VISA instrument communication
- `tdt` — TDT Synapse API (for sync scripts only)
- VNA connected at `192.168.0.1` over Ethernet

## Hardware

- Agilent/Keysight E5061A/B Vector Network Analyzer
- TDT (Tucker-Davis Technologies) Synapse neural recording system
