"""
Based on https://egalvez.colgate.domains/pql/wp-content/uploads/2022/07/FreeRunning4DetectorsAlteraV2.txt.
"""

import time
import serial
import numpy as np
import configparser
import os 
import struct
os.system("")
# https://stackoverflow.com/questions/12492810/python-how-can-i-make-the-ansi-escape-codes-to-work-also-in-windows

BAUDRATE = 19200 

WELCOME_STRING = r'''
   ___                _                   | 
  / _ \ _  _ __ _ _ _| |_ _  _ _ __       |  github.com/lzawbrito/quantum-optics
 | (_) | || / _` | ' \  _| || | '  \      |  
  \__\_\\_,_\__,_|_||_\__|\_,_|_|_|_|     |  Instructional labs @ Brown U.
  / _ \ _ __| |_(_)__ ___                 |  Department of Physics.
 | (_) | '_ \  _| / _(_-<  Acquisition    |      
  \___/| .__/\__|_\__/__/  software v0.0  |  Author: Lucas Z. Brito
       |_|                                |
'''

# https://itnext.io/overwrite-previously-printed-lines-4218a9563527
def clear_line(n=1):
    LINE_UP = '\033[1A'
    LINE_CLEAR = '\x1b[2K'
    for i in range(n):
        print(LINE_UP, end=LINE_CLEAR)

def create_settings_if_none(path): 
    if not os.path.isfile(os.path.join(path, 'settings.ini')):
        config = configparser.ConfigParser()
        config['user_input'] = {
            'port': 'COM8', 
            'n_intervals': '1',
            'dt': '1', 
            'coinc_time': '40',
            'data_dir': './data/'
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
                     'coinc_time': ''
                    }

    for prompt, setting in zip(prompts, user_settings.keys()): 
        user_input = input(prompt)
        if user_input == '': 
            user_input = default_settings[setting]

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

        if os.path.isdir(data_dir): 
            # user_overwrite = '' 
            user_overwrite = input(f'Directory {data_dir} already exists. ' + 
                                    'Overwrite (y/[n])?\t').lower().replace(' ', '')
            overwrite = True if user_overwrite == 'y' else False
            # if we overwrite then we can just let python file object overwrite 
            # contents of directory
        else: 
            try: 
                os.mkdir(data_dir)
            except FileNotFoundError: 
                print(f'Error: could not create directory {data_dir}. ' + 
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


def convert_counts(ser, time_interval): 
    """..."""

    def convert_frame(length): # is frame right terminology?
        # time.sleep(1)
        data_len = 41 * (length * 10) + 40 # time interval in tenths of seconds

        # this array stores the bytes received from the altera (valued 0-255).
        raw_data = bytearray()
        for i in range(length):
            altera_data = ser.read(512) # Each time interval we read 512 bytes.
            raw_data += altera_data

        # Find termination byte (255) index 
        clean_data = clean_up_data(raw_data, data_len)
        # print(clean_data)

        # print(f'len(clean_data):\t{len(clean_data)}')

        counts = np.zeros(8, dtype=np.int64)

        times = np.arange(0, 41 * length, 41)
        detector_pairs = np.arange(0, 8)

        # loop through each detector pair (5 bytes each)
        l = 0
        print(len(clean_data))

        # loop through time 
 
        for t in times:
            # should be 5 * 8 = 40 bytes. 
            data_to_decode = clean_data[t:(t + 40)]
            for d in detector_pairs: 
                # reverse of byte array
                count_from_data = decode_int_5byte(data_to_decode[l:l+5])
                counts[d] = counts[d] + count_from_data

                l += 5 # move forward 5 bytes for next detector pair
        
        clear_line(1)
        out_string = ''
        for c in counts: 
            out_string += "{:.2e}  ".format(c)

        print(out_string) 
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
            counts += convert_frame(10) 
        
        # do remainder
        counts += convert_frame(int(time_interval % 10))
    else:
        time.sleep(1)
        counts += convert_frame(int(time_interval))

    return counts 


def acc_coinc(a, b, coinc_time, dt, n_measures):
    """
    Accidental coincidences (deltat = coinc_time * 10e-9)
    """

    # calculate the accidental coincidences (kiko ln 499) 
    return np.sum(a) * np.sum(b) * coinc_time * 10e-9 / (n_measures * dt)


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

        # Need a n_measurements x 8 (detectors + detector pairs) matrix for results
        # n_measurements = n_intervals
        # (A, B, A', B', AB, AA', BB', A'B')
        results = np.zeros((int(settings['n_intervals']), 8), dtype=np.int64)

        print("A         B         A'        B'        AB        AA'       BB'" + \
              "       A'B'")
        print("0         0         0         0         0         0         0" + \
              "         0")
        for i in range(int(settings['n_intervals'])): 
            results[i, :] = convert_counts(ser, float(settings['dt']))

        np.save(os.path.join(settings['data_dir'], 'test.npy'), results)
        np.savetxt(os.path.join(settings['data_dir'], 'test.txt'), results, fmt='%i', header="A   B   A'  B'  AB  AA'  BB'  A'B'")

        ser.close()

        running = True if input('Run again (y/[n])?').lower().replace(' ', '') == 'y' \
                        else False

