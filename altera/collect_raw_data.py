import serial 
import time 

fname = 'C:\Users\student\Desktop\quantum-optics\\raw_altera_data.txt'

bstring = ''
max_iter = 10
i = 0 
ser = serial.Serial('COM8', 19200, timeout=0, rtscts=1)
while i < max_iter: 
	bstring += ser.read(512)
	time.sleep(1)


f = open(fname, 'w')
f.write(fname)
f.close()

