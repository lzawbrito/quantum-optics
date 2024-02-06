"""
Based on https://egalvez.colgate.domains/pql/wp-content/uploads/2022/07/FreeRunning4DetectorsAlteraV2.txt.
"""

import serial
import numpy as np

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

BLUE = '\033[94m'
GREEN = '\033[92m'
RED = '\033[91m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'
END = '\033[0m'


def get_user_input():
    # TODO at some point should have some defaults, would be nice if uses 
    # last input. use .ini or config or smth like that
    port        = input(BLUE + "Enter FPGA port:\t" + END)
    n_intervals = input(BLUE + "Number of intervals:\t" + END)
    dt          = input(BLUE + "Time per interval (s):\t" + END)
    coinc_time  = input(BLUE + "Coincidence time (ns):\t" + END)

    return port, n_intervals, dt, coinc_time

def bytes2count(data): 
    count = 0 
    i = 0
    for b in data: 
        count += 2 ** (i * 7) * b
        i += 1
    return count

def convert_counts(ser, time_interval): 
    """..."""

    def convert_frame(length): # is frame right terminology?
        data_len = 41 * (length * 10) + 40 # time interval in tenths of seconds

        # this array stores the bytes received from the altera (valued 0-255).
        raw_data = np.zeros(data_len)
        for i in range(length):
            altera_data = ser.read(512) # Each time interval we read 512 bytes.

            # store the altera data in raw_data. 
            raw_data[(i * 512 + 1):i*(512 + 1)] = altera_data 
            # TODO the above is likely incorrect, there's some fudging with 
            # zero indexing

        # Find termination byte (255) index 
        tbi = np.where(raw_data == 255)[0][0]
        clean_data = raw_data[tbi:(tbi + data_len - 40)] # Save to clean data array

        counts = np.zeros(8)

        times = np.arange(0, 41 * length, 41)
        detector_pairs = np.arange(0, 8)

        # loop through each detector pair (5 bytes each)
        l = 0
        for d in detector_pairs: 
            # loop through time 
            for t in times:
                count_from_data = bytes2count(clean_data[(d + l):(d + l + 5)])
                counts[d] = counts[d] + count_from_data

            l += 5 # move forward 5 bytes for next detector pair
        
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
        counts += convert_frame(time_interval % 10)
    else:
        counts =+ convert_frame(time_interval)

    return counts 


def acc_coinc(a, b, coinc_time, dt, n_measures):
    """
    Accidental coincidences (deltat = coinc_time * 10e-9)
    """

    return np.sum(a) * np.sum(b) * coinc_time * 10e-9 / (n_measures * dt)
    # calculate the accidental coincidences (kiko ln 499) 
    """
         countt=num2str((stateindexi-1)*2+3);
    xl2range2=strcat('A',countt);
    accidentalstotAB = sum(resultsmatrix(1:numofmeasurements, 1)) * sum(resultsmatrix(1:numofmeasurements, 2)) * deltat / (numofmeasurements*timeinterval);
    accidentalstotBAp=sum(resultsmatrix(1:numofmeasurements,2))*sum(resultsmatrix(1:numofmeasurements,3))*deltat/(numofmeasurements*timeinterval);
    accidentalstotABp=sum(resultsmatrix(1:numofmeasurements,1))*sum(resultsmatrix(1:numofmeasurements,4))*deltat/(numofmeasurements*timeinterval);
    accidentalstotApBp=sum(resultsmatrix(1:numofmeasurements,2))*sum(resultsmatrix(1:numofmeasurements,4))*deltat/(numofmeasurements*timeinterval);
    xlswrite(nams,[sum(resultsmatrix(1:numofmeasurements,1)),sum(resultsmatrix(1:numofmeasurements,2)),sum(resultsmatrix(1:numofmeasurements,3)),...
        sum(resultsmatrix(1:numofmeasurements,4)),sum(resultsmatrix(1:numofmeasurements,5)),sum(resultsmatrix(1:numofmeasurements,6)),...
        sum(resultsmatrix(1:numofmeasurements,7)),sum(resultsmatrix(1:numofmeasurements,8)),accidentalstotAB,accidentalstotBAp,accidentalstotABp,accidentalstotApBp],Sheet2,xl2range2)
    pause(statepause);
    count=1;"""

if __name__ == '__main__':
    print(WELCOME_STRING)
    port, n_intervals, dt, coinc_time = get_user_input()

    print(f'\nBaudrate:\t\t{BAUDRATE} bps')

    ser = serial.Serial(port, BAUDRATE, timeout=0,
                         parity=serial.PARITY_EVEN, rtscts=1)

    # Need a n_measurements x 8 (detectors + detector pairs) matrix for results
    # n_measurements = n_intervals
    # (A, B, A', B', AB, AA', BB', A'B')
    results = np.zeros((n_intervals, 8))

    for i in range(n_intervals): 
        results[i, :] = convert_counts(ser, dt)

    


