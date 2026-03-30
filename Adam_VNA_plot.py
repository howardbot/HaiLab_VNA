import os
import re
import csv
import matplotlib.pyplot as plt
import numpy as np

# Matches top-level die folders: Die1, Die2, ...
DIE_RE    = re.compile(r'^Die(\w+)$')
# Matches device subfolders: X1Y1, X2Y4, ...
DEVICE_RE = re.compile(r'^X(\d+)Y(\d+)$')
# Matches CSV files inside a device folder: X1Y1.csv
FILE_RE   = re.compile(r'^X\d+Y\d+\.csv$')


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def scan(root='.'):
    """
    Return a nested dict: {die_num: {device_name: csv_path}}
    Structure on disk: Die1/X1Y1/X1Y1.csv
    """
    dies = {}
    for die_entry in sorted(os.listdir(root)):
        m = DIE_RE.match(die_entry)
        die_path = os.path.join(root, die_entry)
        if not m or not os.path.isdir(die_path):
            continue
        die_num = m.group(1)
        for dev_entry in sorted(os.listdir(die_path)):
            if not DEVICE_RE.match(dev_entry):
                continue
            dev_path = os.path.join(die_path, dev_entry)
            if not os.path.isdir(dev_path):
                continue
            csv_files = [f for f in os.listdir(dev_path) if FILE_RE.match(f)]
            if csv_files:
                csv_path = os.path.join(dev_path, csv_files[0])
                dies.setdefault(die_num, {})[dev_entry] = csv_path
    return dies


def list_devices(dies):
    for die_num in sorted(dies, key=lambda d: int(d) if d.isdigit() else d):
        devs = dies[die_num]
        print(f'\n  Die {die_num}:  ({len(devs)} device{"s" if len(devs) != 1 else ""})')
        for dev in sorted(devs, key=lambda s: [int(c) for c in re.findall(r'\d+', s)]):
            print(f'    {dev}')


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

def _save_fig(fig, path):
    fig.savefig(path, dpi=150, bbox_inches='tight')
    print(f'  Saved: {path}')


def plot_device(die_num, device_name, csv_path, show=True, save=False):
    """Plot one device on its own figure."""
    fig, ax = plt.subplots(figsize=(8, 4))

    freqs, dbs = load_csv(csv_path)
    ax.plot(freqs / 1e6, dbs, linewidth=0.8)
    ax.set_xlabel('Frequency (MHz)')
    ax.set_ylabel('S11 (dB)')
    ax.grid(True, linestyle='--', alpha=0.4)

    plt.tight_layout()
    if save:
        out = os.path.join(f'Die{die_num}', device_name, f'{device_name}_plot.png')
        _save_fig(fig, out)
    if show:
        plt.show()
    else:
        plt.close(fig)


def plot_die(die_num, die_devices, show=True, save=False):
    """Plot each device in the die individually."""
    for name in sorted(die_devices, key=lambda s: [int(c) for c in re.findall(r'\d+', s)]):
        plot_device(die_num, name, die_devices[name], show=show, save=save)


def plot_all(dies, show=True, save=False):
    """Plot every device across all dies."""
    for die_num in sorted(dies, key=lambda d: int(d) if d.isdigit() else d):
        plot_die(die_num, dies[die_num], show=show, save=save)


# ---------------------------------------------------------------------------
# Interactive menu
# ---------------------------------------------------------------------------

def help_menu():
    print('\nCommands:')
    print('  [Enter] / all              plot every detected device (grouped by die)')
    print('  die <number>               plot all devices in a die  (e.g. die 3)')
    print('  dev <die_number> <XnYm>    plot one device  (e.g. dev 3 X2Y4)')
    print('  Add -s to save instead of display:')
    print('    dev 3 X2Y4 -s            -> Die3/X2Y4/X2Y4_plot.png')
    print('    die 3 -s                 -> Die3/X*Y*/Die3_overview.png')
    print('    all -s                   -> same, for every die')
    print('  ls                         list detected devices')
    print('  rescan                     re-scan directory for new data')
    print('  h                          show this help')
    print('  q                          quit')


def main():
    print('Adam VNA Plot')
    print('Scanning current directory...')

    dies = scan()

    if not dies:
        print('No data found. Make sure you run this script from the folder')
        print('that contains Die* subfolders created by Adam_VNA.py.')
        return

    total_devs = sum(len(d) for d in dies.values())
    print(f'Found {len(dies)} die(s), {total_devs} device(s):')
    list_devices(dies)
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
            plot_all(dies, show=show, save=save)

        elif tokens[0] == 'die':
            if len(tokens) < 2:
                print('  Usage: die <number> [-s]')
                continue
            die_num = tokens[1]
            if die_num not in dies:
                print(f'  Die {die_num} not found. Use "ls" to see available dies.')
            else:
                plot_die(die_num, dies[die_num], show=show, save=save)

        elif tokens[0] == 'dev':
            if len(tokens) < 3:
                print('  Usage: dev <die_number> <XnYm> [-s]  (e.g. dev 3 X2Y4 -s)')
                continue
            die_num, dev_name = tokens[1], tokens[2]
            if die_num not in dies:
                print(f'  Die {die_num} not found.')
            elif dev_name not in dies[die_num]:
                print(f'  Device {dev_name} not found in Die {die_num}.')
            else:
                plot_device(die_num, dev_name, dies[die_num][dev_name], show=show, save=save)

        elif tokens[0] == 'ls':
            list_devices(dies)

        elif tokens[0] == 'rescan':
            dies = scan()
            total_devs = sum(len(d) for d in dies.values())
            print(f'Rescanned — {len(dies)} die(s), {total_devs} device(s) found.')
            list_devices(dies)

        elif tokens[0] == 'h':
            help_menu()

        elif tokens[0] == 'q':
            print('Goodbye.')
            break

        else:
            print('  Unknown command. Type h for help.')


main()
