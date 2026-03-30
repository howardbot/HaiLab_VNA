import os
import re
import csv
import math
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np

# Matches folder names like: Die3_X2Y4, Die10_X1Y1
FOLDER_RE = re.compile(r'^(Die(\w+)_X(\d+)Y(\d+))$')
# Matches file names like: Die3_X2Y4.csv
FILE_RE   = re.compile(r'^Die\w+_X\d+Y\d+\.csv$')


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def scan(root='.'):
    """Return a dict: {device_name: [sorted list of csv paths]}"""
    devices = {}
    for entry in sorted(os.listdir(root)):
        if FOLDER_RE.match(entry) and os.path.isdir(os.path.join(root, entry)):
            traces = sorted(
                os.path.join(root, entry, f)
                for f in os.listdir(os.path.join(root, entry))
                if FILE_RE.match(f)
            )
            if traces:
                devices[entry] = traces
    return devices


def group_by_die(devices):
    """Return a dict: {die_number: {device_name: [traces]}}"""
    dies = {}
    for name, traces in devices.items():
        m = FOLDER_RE.match(name)
        die_num = m.group(2)
        dies.setdefault(die_num, {})[name] = traces
    return dies


def list_devices(devices):
    dies = group_by_die(devices)
    for die_num in sorted(dies):
        print(f'\n  Die {die_num}:')
        for dev in sorted(dies[die_num]):
            n = len(dies[die_num][dev])
            print(f'    {dev}  ({n} trace{"s" if n != 1 else ""})')


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_csv(path):
    freqs, dbs = [], []
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            freqs.append(float(row['Frequency(Hz)']))
            dbs.append(float(row['dB']))
    return np.array(freqs), np.array(dbs)


# ---------------------------------------------------------------------------
# Plotting helpers
# ---------------------------------------------------------------------------

def _colors(n):
    return cm.tab10(np.linspace(0, 0.9, max(n, 1)))


def _save_fig(fig, path):
    fig.savefig(path, dpi=150, bbox_inches='tight')
    print(f'  Saved: {path}')


def plot_device(device_name, trace_paths, ax=None, show=True, save=False):
    """Plot the single trace for one device."""
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(8, 4))

    freqs, dbs = load_csv(trace_paths[0])
    ax.plot(freqs / 1e6, dbs, linewidth=0.8)

    ax.set_xlabel('Frequency (MHz)')
    ax.set_ylabel('S11 (dB)')
    ax.set_title(device_name)
    ax.grid(True, linestyle='--', alpha=0.4)

    if standalone:
        plt.tight_layout()
        if save:
            # Save into the device's own folder: Die3_X2Y4/Die3_X2Y4_plot.png
            out = os.path.join(device_name, f'{device_name}_plot.png')
            _save_fig(fig, out)
        if show:
            plt.show()
        return fig


def plot_die(die_num, die_devices, show=True, save=False):
    """One figure with a subplot grid for every device in the die."""
    names = sorted(die_devices)
    n = len(names)
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)

    fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 3.5 * rows),
                             squeeze=False)
    fig.suptitle(f'Die {die_num}', fontsize=14, fontweight='bold')

    for idx, name in enumerate(names):
        ax = axes[idx // cols][idx % cols]
        plot_device(name, die_devices[name], ax=ax, show=False, save=False)

    for idx in range(n, rows * cols):
        axes[idx // cols][idx % cols].set_visible(False)

    plt.tight_layout()

    if save:
        # Save one copy into each device subfolder within this die
        for name in names:
            out = os.path.join(name, f'Die{die_num}_overview.png')
            _save_fig(fig, out)

    if show:
        plt.show()
    return fig


def plot_all(devices, show=True, save=False):
    """One figure per die."""
    dies = group_by_die(devices)
    figs = []
    for die_num in sorted(dies):
        figs.append(plot_die(die_num, dies[die_num], show=show, save=save))
    return figs


# ---------------------------------------------------------------------------
# Interactive menu
# ---------------------------------------------------------------------------

def help_menu():
    print('\nCommands:')
    print('  [Enter] / all          plot every detected device (grouped by die)')
    print('  die <number>           plot all devices in a die  (e.g. die 3)')
    print('  dev <name>             plot all traces for one device (e.g. dev Die3_B2)')
    print('  Add -s to any plot command to save instead of display:')
    print('    dev Die3_B2 -s       -> saves Die3_B2/Die3_B2_plot.png')
    print('    die 3 -s             -> saves Die3_*/Die3_overview.png (per device folder)')
    print('    all -s               -> same, for every die')
    print('  ls                     list detected devices')
    print('  rescan                 re-scan directory for new data')
    print('  h                      show this help')
    print('  q                      quit')


def main():
    print('Adam VNA Plot')
    print('Scanning current directory...')

    devices = scan()

    if not devices:
        print('No data found. Make sure you run this script from the folder')
        print('that contains Die*_* subfolders created by Adam_VNA.py.')
        return

    print(f'Found {len(devices)} device(s):')
    list_devices(devices)
    help_menu()

    while True:
        cmd = input('\nCommand: ').strip()
        tokens = cmd.split()

        if not tokens:
            tokens = ['all']

        save = '-s' in tokens
        if save:
            tokens = [t for t in tokens if t != '-s']

        # -s: save only (no display); otherwise show only (no save)
        show = not save

        if not tokens or tokens[0] == 'all':
            plot_all(devices, show=show, save=save)

        elif tokens[0] == 'die':
            if len(tokens) < 2:
                print('  Usage: die <number> [-s]')
                continue
            die_num = tokens[1]
            dies = group_by_die(devices)
            if die_num not in dies:
                print(f'  Die {die_num} not found. Use "ls" to see available dies.')
            else:
                plot_die(die_num, dies[die_num], show=show, save=save)

        elif tokens[0] == 'dev':
            if len(tokens) < 2:
                print('  Usage: dev <device_name> [-s]  (e.g. dev Die3_B2 -s)')
                continue
            name = tokens[1]
            if name not in devices:
                print(f'  Device "{name}" not found. Use "ls" to see available devices.')
            else:
                plot_device(name, devices[name], show=show, save=save)

        elif tokens[0] == 'ls':
            list_devices(devices)

        elif tokens[0] == 'rescan':
            devices = scan()
            print(f'Rescanned — {len(devices)} device(s) found.')
            list_devices(devices)

        elif tokens[0] == 'h':
            help_menu()

        elif tokens[0] == 'q':
            print('Goodbye.')
            break

        else:
            print('  Unknown command. Type h for help.')


main()
