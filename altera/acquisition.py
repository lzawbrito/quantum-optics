"""
Based on https://egalvez.colgate.domains/pql/wp-content/uploads/2022/07/FreeRunning4DetectorsAlteraV2.txt.

todo: 
[ ] fix idle overwritten by settings/do settings things more carefully 
[ ] on filename prompt instead of paren fill out the previous dir
[ ] progress bar
[ ] just type inf for idle mode
"""
import matplotlib.pyplot as plt 
import matplotlib.animation as animation
import time
import serial
import numpy as np
import configparser
import os 
import struct
from tqdm import tqdm
os.system("")
# https://stackoverflow.com/questions/12492810/python-how-can-i-make-the-ansi-escape-codes-to-work-also-in-windows

BAUDRATE = 19200 
DETECTORS = ["A", "B", "A'", "B'", "AB", "AA'", "A'B'", "BB'"]
HEADER_STRING = ''.join([s.ljust(10) for s in DETECTORS])

WELCOME_STRING = r'''
╔═════════════════════════════════════════╤══════════════════════════════════════╗
║   ___                _                  │                                      ║
║  / _ \ _  _ __ _ _ _| |_ _  _ _ __      │ github.com/lzawbrito/quantum-optics  ║
║ | (_) | || / _` | ' \  _| || | '  \     │                                      ║
║  \__\_\\_,_\__,_|_||_\__|\_,_|_|_|_|    │ Instructional labs @ Brown U.        ║
║  / _ \ _ __| |_(_)__ ___                │ Department of Physics.               ║
║ | (_) | '_ \  _| / _(_-<  Acquisition   │                                      ║
║  \___/| .__/\__|_\__/__/  software v0.1 │ Author: Lucas Z. Brito               ║
║       |_|                               │                                      ║
╚═════════════════════════════════════════╧══════════════════════════════════════╝ 
'''

def str2bool(string):
    if string.lower() == 'true':
        return True
    else:
        return False

# https://itnext.io/overwrite-previously-printed-lines-4218a9563527
def clear_line(n=1):
    LINE_UP = '\033[1A'
    LINE_CLEAR = '\x1b[2K'
    for i in range(n):
        print(LINE_UP, end=LINE_CLEAR)

def create_settings_if_none(path): 
    if not os.path.isfile(os.path.join(path, 'settings.ini')):
        print('Missing settings.ini, created new.')
        config = configparser.ConfigParser()
        config['user_input'] = {
            'port': 'COM8', 
            'n_intervals': '1',
            'dt': '1', 
            'coinc_time': '40',
            'data_dir': './data/',
            'gui': True,
            'idle': False,
        }

        with open(os.path.join(path, 'settings.ini'), 'w') as configfile:
            config.write(configfile)


def get_user_input(path):

    config = configparser.ConfigParser() 
    config.read(os.path.join(path, 'settings.ini'))

    default_settings = config['user_input']

    prompts = [
               f'Enter FPGA port ({default_settings['port']}):\t\t\t\t',
               f'Number of intervals ({default_settings['n_intervals']}):\t\t\t\t', 
               f'Time per interval (s) ({default_settings['dt']}):\t\t\t\t', 
               f'Coincidence time (ns) ({default_settings['coinc_time']}):\t\t\t\t']
    
    user_settings = {
                     'port' : '',
                     'n_intervals': '', 
                     'dt': '', 
                     'coinc_time': '',
                     'gui': '',
                     'idle': str2bool(default_settings['idle']),
                    }

    for prompt, setting in zip(prompts, user_settings.keys()): 
        user_input = input(prompt)

        if setting == 'idle': 
            continue

        if user_input == '': 
            user_input = default_settings[setting]

        if user_settings['idle'] and setting == 'n_intervals':
            print('Idle mode is on. Program will run until stopped by user.')
            user_settings[setting] = '0'
            continue

        user_settings[setting] = user_input

    # Handle data directory input

    overwrite = False

    data_dir = ''
    while not overwrite:  
        default_dir = default_settings['data_dir']
        default_dir= (default_dir[:15] + '...' + default_dir[-15:]) \
                if len(default_dir) > 30 else default_dir

        data_dir = input(f'Data directory ({default_dir}):\n>\t')
        if data_dir == '': 
            data_dir = default_settings['data_dir']
        print()

        if os.path.isfile(data_dir): 
            # user_overwrite = '' 
            user_overwrite = input(f'File {data_dir} already exists. ' + 
                                    'Overwrite (y/[n])?\t').lower().replace(' ', '')
            overwrite = True if user_overwrite == 'y' else False
            # if we overwrite then we can just let python file object overwrite 
            # contents of directory
        else: 
            try: 
                np.savetxt(data_dir, [])
            except FileNotFoundError: 
                print(f'Error: could not create file {data_dir}. ' + 
                      'Are you sure all parent directories exist?')
                continue
            break
    
    user_settings['data_dir'] = data_dir
        
    # for key in user_settings.keys():
    #     print(user_settings[key])

    return user_settings


def decode_int_5byte(data): 
    count = 0 
    i = 0
    for b in data: 
        count += 2 ** (i * 7) * b
        i += 1
    return count

# def decode_int(data): 
#     return struct.unpack('<I', data)[0]

def encode7bit(int):
    bytes_ = []
    for i in range(5):
        bytes_.append(int & 0x7f) # bitwise and with 0x7f 7 one bits, i.e., just get 7 bits
        int >>= 7 # consider next 7 bits

    return bytes_

def clean_up_data(raw_data, data_len): 
    tbi = raw_data.find(255) 
    # print(tbi)
    # Save to clean data array, starting from previous iteration's termination
    return raw_data[(tbi + 1):(tbi + data_len - 40)] 


def update_plot(i, times, results, ax): 
    for a in ax: 
        a.clear()
    ax[0].plot(range(times[i] + 1), results[0:(times[i] + 1), 0:4], label=DETECTORS[0:4])
    ax[0].legend(loc='center left', bbox_to_anchor=(0, 0.5))

    ax[1].plot(range(times[i] + 1), results[0:(times[i] + 1), 4:], label=DETECTORS[4:])
    ax[1].legend(loc='center left', bbox_to_anchor=(0, 0.5))

    ax[0].set_ylabel('Counts')
    ax[1].set_xlabel('Time')
    ax[1].set_ylabel('Counts')

    return None 


def convert_counts(i, ser, time_interval, results, times, idle, ax=None): 
    """..."""

    def convert_frame(length): 
        data_len = 41 * (length * 10) + 40 # time interval in tenths of seconds

        # this array stores the bytes received from the altera (valued 0-255).
        raw_data = bytearray()
        for i in range(length):
            altera_data = ser.read(512) # Each time interval we read 512 bytes.
            raw_data += altera_data

        # Find termination byte (255) index 
        clean_data = clean_up_data(raw_data, data_len)

        counts = np.zeros(8, dtype=np.int64)

        times = np.arange(0, 41 * length * 10, 41)
        detector_pairs = np.arange(0, 8)


        # loop through time 
        for t in times:
            # should be 5 * 8 = 40 bytes. 
            data_to_decode = clean_data[t:(t + 40)]
            l = 0

            # loop through each detector pair (5 bytes each)
            for d in detector_pairs: 
                # reverse of byte array
                count_from_data = decode_int_5byte(data_to_decode[l:l + 5])
                counts[d] = counts[d] + count_from_data
                l += 5 # move forward 5 bytes for next detector pair
        
        clear_line(1)
        out_string = ''
        for c in counts: 
            if c > 1e7:
                out_string += "{:.2e}  ".format(c)
            else: 
                out_string += str(c).ljust(8) + "  "
        tqdm.write(out_string) 
        # print(out_string)

        return counts
    

    # We count differently depending on the time interval given. Minimum is 
    # 0.1 second (ds), if greater than 1 sec we split it into 1 sec groups.
    counts = np.zeros(8, dtype=np.int64) 
    if time_interval < 1: 
        time.sleep(1)
        counts += convert_frame(1)
    elif time_interval > 10: 
        for i in range(int(time_interval / 10)):
            time.sleep(1)
            counts += convert_frame(1) 
        
        # do remainder
        counts += convert_frame(int(time_interval % 10))
    else:
        time.sleep(1)
        counts += convert_frame(int(time_interval))

    if not idle:
        results[i, :] = counts
        times.append(i)

    if ax is not None: 
        update_plot(i, times, results, ax)
    
    if i > np.shape(results)[1]: 
        plt.close() # if you close it here it's going to error 


def acc_coinc(a, b, coinc_time, dt, n_measures):
    """
    Accidental coincidences (deltat = coinc_time * 10e-9)
    """

    # calculate the accidental coincidences (kiko ln 499) 
    return np.sum(a) * np.sum(b) * coinc_time * 10e-9 / (n_measures * dt)


def acquire_data(ser, t_int, n_ints, gui, idle): 
    # Create plot 
    fig, ax = plt.subplots(nrows=2) 
    if not gui: 
        ax = None
    # TODO set up axes and stuff
    times = []

    # Need a n_measurements x 8 (detectors + detector pairs) matrix for results
    # n_measurements = n_intervals
    # (A, B, A', B', AB, AA', BB', A'B')

    results = np.zeros((n_ints, 8), dtype=np.int64)

    if gui:
        anim = animation.FuncAnimation(fig, convert_counts, 
                                fargs=(ser, t_int, results, times, ax), frames=range(n_ints))

    i = 0

    times = [] 
    # while i < n_ints or idle:
    #     convert_counts(i, ser, t_int, results, times, idle)
    #     i += 1
    if idle: 
        while True:
            convert_counts(i, ser, t_int, results, times, idle)
            i += 1
    else: 
        for i in tqdm(range(n_ints), ncols=83, bar_format='|{bar}| {elapsed}<{remaining}'):
            convert_counts(i, ser, t_int, results, times, idle)

    if gui: 
        plt.show()
    # two issues: (1) initializes and then there's two 0 values at first. 
    #             (2) plot will keep looping frames
    return results 


if __name__ == '__main__':
    print(WELCOME_STRING)
    fpath = os.path.dirname(os.path.abspath(__file__))

    create_settings_if_none(fpath)    
    running = True

    while running: 
        settings = get_user_input(fpath)

        # save user settings. so this here so that if there's an error later no 
        # need to retype
        config = configparser.ConfigParser()
        config['user_input'] = settings

        with open(os.path.join(fpath, 'settings.ini'), 'w') as configfile:
            config.write(configfile)

        print(f'\nBaudrate:\t\t{BAUDRATE} bps')

        ser = serial.Serial(settings['port'], BAUDRATE, timeout=0)

        # todo can make one 'detectors' array and join all these string together
        print(HEADER_STRING)
        print("0         0         0         0         0         0         0" + \
              "         0")
        
        results = acquire_data(ser, float(settings['dt']), 
                                    int(settings['n_intervals']),
                                    settings['gui'],
                                    settings['idle'])
        print("\nMeans")
        mean_string = ""
        print(HEADER_STRING)
        for c in np.mean(results, axis=0):
            if c > 1e7:
                mean_string += "{:.2e}  ".format(c)
            else: 
                mean_string += str(round(c)).ljust(8) + "  "
        print(mean_string)

        # np.save(os.path.join(settings['data_dir'], 'test.npy'), results)
        np.savetxt(settings['data_dir'], results, fmt='%i', 
                    header=' '.join(DETECTORS))

        ser.close()

        running = True if input('Run again (y/[n])?').lower().replace(' ', '') == 'y' \
                        else False

