#!/bin/zsh

socat_output=$(socat -d -d pty,raw,echo=0,ispeed=19200,ospeed=19200 pty,raw,echo=0,ispeed=19200,ospeed=19200 2>&1) 
port=$(echo "$socat_output" | grep -oE '/dev/ttys[0-9]+')
echo $port
/Users/lzawbrito/opt/miniconda3/envs/quantum-optics/bin/python /Users/lzawbrito/projects/quantum-optics/altera/virtual_port.py -p /dev/ttys10 
