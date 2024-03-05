import serial
import struct
import time
import numpy as np
from free_running_4detectors import encode7bit

# Define the virtual serial port name
serial_port = input('Port: ')
if serial_port == '': 
    serial_port = '/dev/ttys013'

# Open the virtual serial port
ser = serial.Serial(serial_port, baudrate=19200)

i = 0

try:
    # Send data to the virtual serial port
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    while True:
        counts = [np.random.randint(255, dtype='int32') for i in range(8)]
        # print(counts)
        # int32 -> 4 bytes. 4 bytes * 8 numbers = 32 bytes
        # upon encoding this becomes 5 bytes * 8 numbers + 1 stop byte = 41 bytes.

        print(counts, end='\r')
        packet = bytearray()
        for count in counts: 
            packet += bytearray(encode7bit(count))

        packet.append(0xff) # 0xff = 255 termination byte.

        ser.write(packet)

        i += 1
except KeyboardInterrupt:
    ser.close()
