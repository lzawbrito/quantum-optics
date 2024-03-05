import serial 
import numpy as np
import struct
import time
from free_running_4detectors import decode_int


ser = serial.Serial('/dev/ttys001', baudrate=19200)


try:
    ser.flush()
    while True: 
        data = ser.read(5 * 8 + 1) 
        print(data)
        for i in range(8):
            print(decode_int(data[5 * i:5 * (i + 1)]))
        print()

except KeyboardInterrupt:
    ser.close()