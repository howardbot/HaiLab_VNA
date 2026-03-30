import visa
import time
import csv
import os

print('Welcome to Adam VNA Controller!')
print('Initializing connection...')

rm = visa.ResourceManager()
SCPI_E5061 = rm.open_resource('TCPIP0::192.168.0.1::inst0::INSTR')

die_number = None
device_row = None
device_col = None


def initialize():
    SCPI_E5061.write(':SYST:PRES')
    SCPI_E5061.write(':DISP:WIND:ACT')
    SCPI_E5061.write(':DISP:SPL D1')
    SCPI_E5061.write(':CALC1:PARameter1:COUN 1')
    SCPI_E5061.write(':CALC1:PARameter1:SEL')
    SCPI_E5061.write(':CALC1:PARameter1:DEF S11')
    SCPI_E5061.write(':CALC1:FORM MLOG')          # log magnitude → dB output
    SCPI_E5061.write(':SENS1:SWE:TYPE LIN')
    SCPI_E5061.write(':SENS1:FREQ:STAR 300000')   # default: 300 kHz
    SCPI_E5061.write(':SENS1:FREQ:STOP 500000000')# default: 500 MHz
    SCPI_E5061.write(':SENS1:SWE:POIN 1001')
    SCPI_E5061.write(':SENS1:SWE:TIME:AUTO 1')
    print('VNA initialized!')


def get_frequencies():
    raw = SCPI_E5061.query(':SENS1:FREQ:DATA?')
    return [float(f) for f in raw.strip().split(',')]


def get_trace_db():
    SCPI_E5061.write('FORMat:DATA ASCii')
    raw = SCPI_E5061.query(':CALC1:DATA:FDAT?')
    values = raw.strip().split(',')
    # FDAT for scalar formats (MLOG) returns (value, 0) pairs — take every other
    return [float(values[i]) for i in range(0, len(values), 2)]


def set_device():
    global die_number, device_row, device_col
    die_number = input('  Die number: ').strip()
    device_row = input('  Row label (e.g. A, B, C): ').strip().upper()
    device_col = input('  Column number (e.g. 1, 2, 3): ').strip()
    print(f'  --> Device set to Die{die_number}_{device_row}{device_col}')


def capture_trace():
    folder = f'Die{die_number}_{device_row}{device_col}'
    os.makedirs(folder, exist_ok=True)

    existing = [f for f in os.listdir(folder) if f.endswith('.csv')]
    trace_num = len(existing) + 1

    freqs = get_frequencies()
    db_vals = get_trace_db()

    filename = f'{folder}_trace{trace_num:03d}.csv'
    filepath = os.path.join(folder, filename)

    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Frequency(Hz)', 'dB'])
        for freq, db in zip(freqs, db_vals):
            writer.writerow([freq, db])

    print(f'  Saved: {filepath}  ({len(freqs)} points)')


def set_frequency():
    start = input('  Start frequency (Hz): ').strip()
    stop  = input('  Stop  frequency (Hz): ').strip()
    SCPI_E5061.write(f':SENS1:FREQ:STAR {start}')
    SCPI_E5061.write(f':SENS1:FREQ:STOP {stop}')
    print(f'  Frequency range set: {start} Hz – {stop} Hz')


def close():
    SCPI_E5061.close()
    rm.close()
    print('Connections closed.')


def help_menu():
    print('\nCommands:')
    print('  [Enter]  capture one trace and save to CSV')
    print('  d        set die number and device position (row/column)')
    print('  freq     set start/stop frequency range')
    print('  h        show this help')
    print('  q        quit and close connections')


def main():
    initialize()
    print('\nSet up your first device:')
    set_device()
    help_menu()

    while True:
        current = f'Die{die_number}_{device_row}{device_col}'
        cmd = input(f'\n[{current}] Command (Enter = capture): ').strip().lower()

        if cmd == '':
            capture_trace()
        elif cmd == 'd':
            set_device()
        elif cmd == 'freq':
            set_frequency()
        elif cmd == 'h':
            help_menu()
        elif cmd == 'q':
            close()
            break
        else:
            print('  Unknown command. Type h for help.')


main()
