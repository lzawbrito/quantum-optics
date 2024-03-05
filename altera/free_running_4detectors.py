"""
Based on https://egalvez.colgate.domains/pql/wp-content/uploads/2022/07/FreeRunning4DetectorsAlteraV2.txt.
"""

import serial
import numpy as np
import configparser
import os 

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


def get_user_input(path):
    # TODO at some point should have some defaults, would be nice if uses 
    # last input. use .ini or config or smth like that

    config = configparser.ConfigParser() 

    config.read(os.path.join(path, 'settings.ini'))

    default_settings = config['user_input']

    prompts = [f'Enter FPGA port ({default_settings['port']}):\t\t',
               f'Number of intervals ({default_settings['n_intervals']}):\t\t', 
               f'Time per interval (s) ({default_settings['dt']}):\t\t', 
               f'Coincidence time (ns) ({default_settings['coinc_time']}):\t\t']
    
    user_settings = {'port' : '',
                     'n_intervals': '', 
                     'dt': '', 
                     'coinc_time': ''}

    for prompt, setting in zip(prompts, user_settings.keys()): 
        user_input = input(prompt)
        if user_input == '': 
            user_input = default_settings[setting]

        user_settings[setting] = user_input
    
    for key in user_settings.keys():
        print(user_settings[key])

    return user_settings


def decode_int(data): 
    count = 0 
    i = 0
    for b in data: 
        count += 2 ** (i * 7) * b
        i += 1
    return count


def encode7bit(int):
    bytes_ = []
    for i in range(5):
        bytes_.append(int & 0x7f) # bitwise and with 0x7f 7 one bits, i.e., just get 7 bits
        int >>= 7 # consider next 7 bits

    return bytes_

def clean_up_data(raw_data, data_len): 
    tbi = raw_data.find(255) # TODO sometimes missing stop byte? multiple stop bytes?
    # print(tbi)
    # Save to clean data array, starting from previous iteration's termination
    return raw_data[(tbi + 1):(tbi + data_len - 40)] 


def convert_counts(ser, time_interval): 
    """..."""

    def convert_frame(length): # is frame right terminology?
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

        counts = np.zeros(8, dtype=int)

        times = np.arange(0, 41 * length, 41)
        detector_pairs = np.arange(0, 8)

        # loop through each detector pair (5 bytes each)
        l = 0
        for d in detector_pairs: 
            # loop through time 
            for t in times:
                count_from_data = decode_int(clean_data[(d + l + t):(d + l + t + 5)])
                counts[d] = counts[d] + count_from_data

            l += 4 # move forward 5 bytes for next detector pair (i.e., 4 indices)
        
        return counts
        
    # We count differently depending on the time interval given. Minimum is 
    # 1 tenth of a second (ds), if greater than 10 tenths we split it into 10 ds groups.
    counts = np.zeros(8) 

    if time_interval < 1: 
        counts += convert_frame(1)
    elif time_interval > 10: 
        for i in range(int(time_interval / 10)):
            counts += convert_frame(10) 
        
        # do remainder
        counts += convert_frame(int(time_interval % 10))
    else:
        counts =+ convert_frame(int(time_interval))

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
    settings = get_user_input(fpath)

    print(f'\nBaudrate:\t\t{BAUDRATE} bps')

    ser = serial.Serial(settings['port'], BAUDRATE, timeout=0,
                         parity=serial.PARITY_EVEN, rtscts=1)

    # Need a n_measurements x 8 (detectors + detector pairs) matrix for results
    # n_measurements = n_intervals
    # (A, B, A', B', AB, AA', BB', A'B')
    results = np.zeros((int(settings['n_intervals']), 8), dtype=int)

    for i in range(int(settings['n_intervals'])): 
        results[i, :] = convert_counts(ser, float(settings['dt']))

    np.save('./altera/data/test.npy', results)
    np.savetxt('./altera/data/test.txt', results, fmt='%i')

    config = configparser.ConfigParser()
    config['user_input'] = settings

    with open(os.path.join(fpath, 'settings.ini'), 'w') as configfile:
        config.write(configfile)


