import serial
import struct
import time
import numpy as np
import argparse
from acquisition import encode7bit

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--port')      

args = parser.parse_args()
serial_port = args.port


# Open the virtual serial port
ser = serial.Serial(serial_port, baudrate=19200)

i = 0

try:
    # Send data to the virtual serial port
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    while True:
        time.sleep(0.1)

        counts = [np.random.randint(100) for i in range(8)]
        # print(counts)
        # int32 -> 4 bytes. 4 bytes * 8 numbers = 32 bytes
        # upon encoding this becomes 5 bytes * 8 numbers + 1 stop byte = 41 bytes.

        print(counts, end='\r')
        packet = bytearray()
        for count in counts: 
            packet += bytearray(encode7bit(count))

        packet.append(0xff) # 0xff = 255 termination byte.

        try:
            ser.write(packet)
        except serial.SerialException: 
            print("Breaking print loop")
            break

        i += 1
except KeyboardInterrupt:
    ser.close()
