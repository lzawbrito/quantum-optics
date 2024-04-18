#!/bin/zsh

# run socat in background
socat -d -d pty,raw,ispeed=19200,echo=0,ospeed=19200 \
	pty,raw,ispeed=19200,echo=0,ospeed=19200 & 

sleep 1 # to prevent overlap printing
read "port?Port: "
echo "Printing to port ${port}"

# run python script that writes to port 
/Users/lzawbrito/opt/miniconda3/envs/quantum-optics/bin/python \
	/Users/lzawbrito/projects/quantum-optics/altera/virtual_port.py -p $port &

echo "Press enter to close..."
read 

ID=$(pgrep socat)  # find the socat job id 
kill $ID           # kill that job 

sleep 1