#!/bin/zsh

PATH1="${HOME}/socatply1"
PATH2="${HOME}/socatply2"

# run socat in background
socat -d -d pty,link=$PATH1,raw,ispeed=19200,echo=0,ospeed=19200 pty,link=$PATH2,raw,ispeed=19200,echo=0,ospeed=19200 &
# pty + link makes symlink to specified path so you can read it from PATH1,2

sleep 1 # to prevent overlap printing
echo ""
echo "Printing to port ${PATH1}"
echo "To read use ${PATH2}"
echo "Starting in 10 seconds..." 
echo ""
sleep 10

# run python script that writes to port 
/Users/lzawbrito/projects/quantum-optics/.venv/bin/python \
	/Users/lzawbrito/projects/quantum-optics/altera/virtual_port.py -p $PATH1 &

echo "Press enter to close..."
read 

ID=$(pgrep socat)  # find the socat job id 
kill $ID           # kill that job 

sleep 1