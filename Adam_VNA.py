import visa
import csv
import os
import socket

print('Welcome to Adam VNA Controller!')
print('Initializing connection...')

rm = visa.ResourceManager()
SCPI_E5061 = rm.open_resource('TCPIP0::192.168.0.1::inst0::INSTR')

# Remote notification target (set during setup)
remote_ip   = None
remote_port = None


# ---------------------------------------------------------------------------
# Remote notification
# ---------------------------------------------------------------------------

def setup_remote():
    global remote_ip, remote_port
    print('\nRemote notification setup:')
    remote_ip   = input('  Target IP address : ').strip()
    remote_port = int(input('  Target port       : ').strip())
    if _try_send('PING'):
        print('  Connection OK.')
    else:
        print('  Could not reach target — notifications disabled until reconnect.')


def _try_send(message):
    """
    Send filename string to the camera server over TCP and return the reply.
    The server expects a plain string (e.g. 'Die1_X2Y4'), captures one frame,
    saves it, then replies 'OK saved=...' or 'ERR ...'.
    Returns the reply string on success, None on network failure.
    """
    try:
        with socket.create_connection((remote_ip, remote_port), timeout=5) as sock:
            sock.sendall((message + '\n').encode('utf-8'))
            reply = sock.recv(4096).decode('utf-8').strip()
        return reply
    except Exception as e:
        return None


def notify(die_num, x, y):
    """Send die+XY as filename to camera server. On failure, ask retry or dismiss."""
    if remote_ip is None:
        return
    message = f'Die{die_num}_X{x}Y{y}'
    while True:
        reply = _try_send(message)
        if reply is not None:
            if reply.startswith('OK'):
                print(f'  Camera: {reply}')
            else:
                print(f'  Camera error: {reply}')
            return
        # Network failure — ask user
        print(f'  [!] Could not reach camera server ({remote_ip}:{remote_port})')
        choice = input('      Retry (r) or dismiss (d)? ').strip().lower()
        if choice == 'r':
            continue
        else:
            print('      Notification dismissed.')
            return


# ---------------------------------------------------------------------------
# VNA setup
# ---------------------------------------------------------------------------

def initialize():
    SCPI_E5061.write(':SYST:PRES')
    SCPI_E5061.write(':DISP:WIND:ACT')
    SCPI_E5061.write(':DISP:SPL D1')
    SCPI_E5061.write(':CALC1:PARameter1:COUN 1')
    SCPI_E5061.write(':CALC1:PARameter1:SEL')
    SCPI_E5061.write(':CALC1:PARameter1:DEF S11')
    SCPI_E5061.write(':CALC1:FORM MLOG')           # log magnitude → dB
    SCPI_E5061.write(':SENS1:SWE:TYPE LIN')
    SCPI_E5061.write(':SENS1:FREQ:STAR 300000')    # default 300 kHz
    SCPI_E5061.write(':SENS1:FREQ:STOP 500000000') # default 500 MHz
    SCPI_E5061.write(':SENS1:SWE:POIN 1001')
    SCPI_E5061.write(':SENS1:SWE:TIME:AUTO 1')
    print('VNA initialized!')


def set_frequency():
    start = input('  Start frequency (Hz): ').strip()
    stop  = input('  Stop  frequency (Hz): ').strip()
    SCPI_E5061.write(f':SENS1:FREQ:STAR {start}')
    SCPI_E5061.write(f':SENS1:FREQ:STOP {stop}')
    print(f'  Frequency range set: {start} Hz – {stop} Hz')


def get_frequencies():
    raw = SCPI_E5061.query(':SENS1:FREQ:DATA?')
    return [float(f) for f in raw.strip().split(',')]


def get_trace_db():
    SCPI_E5061.write('FORMat:DATA ASCii')
    raw = SCPI_E5061.query(':CALC1:DATA:FDAT?')
    values = raw.strip().split(',')
    # FDAT for MLOG returns (value, 0) pairs — take every other element
    return [float(values[i]) for i in range(0, len(values), 2)]


def close():
    SCPI_E5061.close()
    rm.close()
    print('Connections closed.')


# ---------------------------------------------------------------------------
# Device sequencing
# ---------------------------------------------------------------------------

def generate_sequence(x_dim, y_dim, order):
    """
    Return an ordered list of (x, y) positions.
    order='x' : X is the fast axis  X1Y1 → X2Y1 → ... → X1Y2 → ...
    order='y' : Y is the fast axis  X1Y1 → X1Y2 → ... → X2Y1 → ...
    """
    seq = []
    if order == 'x':
        for y in range(1, y_dim + 1):
            for x in range(1, x_dim + 1):
                seq.append((x, y))
    else:
        for x in range(1, x_dim + 1):
            for y in range(1, y_dim + 1):
                seq.append((x, y))
    return seq


def device_path(die_num, x, y):
    """Returns (die_folder, device_subfolder, full_path)"""
    die_folder    = f'Die{die_num}'
    device_folder = f'X{x}Y{y}'
    return die_folder, device_folder, os.path.join(die_folder, device_folder)


# ---------------------------------------------------------------------------
# Capture
# ---------------------------------------------------------------------------

def capture_and_save(die_num, x, y):
    _, device_folder, full_path = device_path(die_num, x, y)
    os.makedirs(full_path, exist_ok=True)

    freqs   = get_frequencies()
    db_vals = get_trace_db()

    filepath = os.path.join(full_path, f'{device_folder}.csv')
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Frequency(Hz)', 'dB'])
        for freq, db in zip(freqs, db_vals):
            writer.writerow([freq, db])

    print(f'  Saved → {filepath}  ({len(freqs)} points)')
    notify(die_num, x, y)


# ---------------------------------------------------------------------------
# Die session
# ---------------------------------------------------------------------------

def setup_die():
    print('')
    die_num = input('Die number          : ').strip()
    dims    = input('Dimension (X Y)     : ').strip().split()
    x_dim, y_dim = int(dims[0]), int(dims[1])
    order   = input('Traverse order (x/y): ').strip().lower()
    if order not in ('x', 'y'):
        print('  Invalid order, defaulting to x.')
        order = 'x'
    return die_num, x_dim, y_dim, order


def run_die(die_num, x_dim, y_dim, order):
    sequence    = generate_sequence(x_dim, y_dim, order)
    total       = len(sequence)
    order_label = 'X-first' if order == 'x' else 'Y-first'

    print(f'\nDie {die_num} | {x_dim}×{y_dim} | {order_label} | {total} devices')
    print('Enter = capture   s = skip   freq = change frequency range   q = quit\n')

    for i, (x, y) in enumerate(sequence):
        current = f'X{x}Y{y}'
        while True:
            cmd = input(f'[{i + 1}/{total}]  Die{die_num}/{current}  > ').strip().lower()
            if cmd == '':
                capture_and_save(die_num, x, y)
                break
            elif cmd == 's':
                print('  Skipped.')
                break
            elif cmd == 'freq':
                set_frequency()
            elif cmd == 'q':
                return False        # signal: quit everything
            else:
                print('  Enter=capture  s=skip  freq=set range  q=quit')

    print(f'\nDie {die_num} complete! ({total} devices)')
    return True                     # signal: continue


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    initialize()
    setup_remote()

    while True:
        die_num, x_dim, y_dim, order = setup_die()
        cont = run_die(die_num, x_dim, y_dim, order)
        if not cont:
            break
        again = input('\nStart another die? (Enter = yes  q = quit): ').strip().lower()
        if again == 'q':
            break

    close()


main()
