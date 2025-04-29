import matplotlib.pyplot as plt 
import matplotlib.animation as animation
import time
import serial
import numpy as np
import configparser
import os 
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
║  \___/| .__/\__|_\__/__/  software v1.0 │ Author: Lucas Z. Brito               ║
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
            'data_dir': '',
            'gui': True,
        }

        with open(os.path.join(path, 'settings.ini'), 'w') as configfile:
            config.write(configfile)


def get_user_input(path):
    config = configparser.ConfigParser() 
    config.read(os.path.join(path, 'settings.ini'))

    default_settings = config['user_input']

    prompts = [
               f'Enter FPGA port ({default_settings["port"]}):\t\t\t\t',
               f'Number of intervals ({default_settings["n_intervals"]}):\t\t\t\t', 
               f'Time per interval (s) ({default_settings["dt"]}):\t\t\t\t', 
               f'Coincidence time (ns) ({default_settings["coinc_time"]}):\t\t\t\t']
    
    user_settings = {
                     'port' : '',
                     'n_intervals': '', 
                     'dt': '', 
                     'coinc_time': '',
                     'gui': '',
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

    return user_settings


def decode_int_5byte(data): 
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
    tbi = raw_data.find(255) 
    
    # Added error handling if 255 isn't found
    if tbi == -1:
        tbi = 0
    
    # Save to clean data array, starting from previous iteration's termination
    return raw_data[(tbi + 1):(tbi + data_len - 40)] 


def convert_frame(ser, length): 
    data_len = 41 * (length * 10) + 40 # time interval in tenths of seconds

    # this array stores the bytes received from the altera (valued 0-255).
    raw_data = bytearray()
    for i in range(length):
        altera_data = ser.read(512) # Each time interval we read 512 bytes.
        raw_data += altera_data

    # Find termination byte (255) index 
    try:
        clean_data = clean_up_data(raw_data, data_len)
        
        counts = np.zeros(8, dtype=np.int64)

        times = np.arange(0, 41 * length * 10, 41)
        detector_pairs = np.arange(0, 8)

        # loop through time 
        for t in times:
            # Check if we have enough data
            if t + 40 <= len(clean_data):
                # should be 5 * 8 = 40 bytes. 
                data_to_decode = clean_data[t:(t + 40)]
                l = 0

                # loop through each detector pair (5 bytes each)
                for d in detector_pairs: 
                    if l + 5 <= len(data_to_decode):
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

        return counts
    except Exception as e:
        print(f"Error processing data: {e}")
        return np.zeros(8, dtype=np.int64)


# Separated animation update function from data collection
def animate(i, ser, time_interval, results, times, ax, pbar=None, max_frames=None):
    # Check if we've reached the maximum number of frames
    if max_frames is not None and i >= max_frames:
        # Don't update the progress bar anymore
        return ax
        
    # Get new data
    counts = collect_data(ser, time_interval)
    
    # Add to results array
    if i >= len(results):
        results.append(counts)
    else:
        results[i] = counts
        
    # Update times if needed
    if i >= len(times):
        times.append(i)
    
    # Clear the axes
    for a in ax:
        a.clear()

    # Plot data
    data_array = np.array(results)
    if len(data_array) > 0:
        ax[0].plot(times[:len(data_array)], data_array[:, 0:4], label=DETECTORS[0:4])
        ax[0].legend(loc='center left', bbox_to_anchor=(0, 0.5))
        
        ax[1].plot(times[:len(data_array)], data_array[:, 4:], label=DETECTORS[4:])
        ax[1].legend(loc='center left', bbox_to_anchor=(0, 0.5))
        
        ax[0].set_ylabel('Counts')
        ax[1].set_xlabel('Time')
        ax[1].set_ylabel('Counts')

    # Update progress bar but only if we haven't reached the max frames
    if pbar is not None and i < max_frames:
        pbar.update(1)
        
    return ax


def collect_data(ser, time_interval):
    # We count differently depending on the time interval given. Minimum is 
    # 0.1 second (ds), if greater than 1 sec we split it into 1 sec groups.
    counts = np.zeros(8, dtype=np.int64) 
    if time_interval < 1: 
        time.sleep(time_interval)
        counts += convert_frame(ser, 1)
    elif time_interval > 10: 
        for i in range(int(time_interval / 10)):
            counts += convert_frame(ser, 1)
            time.sleep(1)
        
        # do remainder
        remainder = time_interval % 10
        if remainder > 0:
            counts += convert_frame(ser, int(remainder))
    else:
        counts += convert_frame(ser, int(time_interval))
    
    return counts


def acc_coinc(a, b, coinc_time, dt, n_measures):
    """
    Accidental coincidences (deltat = coinc_time * 10e-9)
    """
    # calculate the accidental coincidences (kiko ln 499) 
    return np.sum(a) * np.sum(b) * coinc_time * 10e-9 / (n_measures * dt)


def acquire_data(ser, t_int, n_ints, gui, idle): 
    # Create plot 
    fig, ax = plt.subplots(nrows=2) 
    plt.ion()  # Turn on interactive mode
    
    # Storage for results
    results = []
    times = []
    
    # Setup the animation
    if idle:
        # For idle mode, we'll use a continuous animation
        ani = animation.FuncAnimation(
            fig, 
            animate, 
            fargs=(ser, t_int, results, times, ax),
            interval=int(t_int * 1000),  # Convert to milliseconds
            blit=False,
            save_count=100  # Limit frames stored in memory
        )
        
        try:
            plt.show(block=True)  # Block until window is closed
        except KeyboardInterrupt:
            plt.close()
    else:
        # Fix: Set the total to n_ints instead of n_ints-1 to match the frames
        pbar = tqdm(total=n_ints, ncols=83, bar_format='|{bar}| {elapsed}<{remaining}')
        
        # Collect data for exactly n_ints frames
        ani = animation.FuncAnimation(
            fig, 
            animate,
            # Pass the maximum frames parameter to the animate function
            fargs=(ser, t_int, results, times, ax, pbar, n_ints),
            frames=n_ints,  # Exactly n_ints frames
            interval=int(t_int * 1000),  # Convert to milliseconds
            blit=False,
            repeat=False  # Don't repeat
        )

        # Create a non-blocking figure manager to keep plot open
        manager = plt.get_current_fig_manager()
        
        # Show the plot non-blocking
        plt.show(block=False)
        
        # Wait until we have collected all the data
        while len(results) < n_ints:
            # Update the figure without blocking
            fig.canvas.draw_idle()
            fig.canvas.flush_events()
            time.sleep(0.1)  # Small sleep to prevent CPU hogging
            
        # Close the progress bar once data collection is complete
        pbar.close()
        
        # Keep the plot open for a bit so user can see final results
        plt.pause(1)
    
    return np.array(results)


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

        print(HEADER_STRING)
        print("0         0         0         0         0         0         0" + \
              "         0")
        
        n_intervals = 0
        idle = True

        if not (settings['n_intervals'] == 'inf'): 
            n_intervals = int(settings['n_intervals'])
            idle = False
        
        try:
            results = acquire_data(ser, float(settings['dt']), 
                                    n_intervals,
                                    str2bool(settings['gui']),
                                    idle)
            
            if not idle and len(results) > 0:
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
        except Exception as e:
            print(f"Error during data acquisition: {e}")
        finally:
            ser.close()

        running = True if input('\nRun again (y/[n])?').lower().replace(' ', '') == 'y' \
                        else False