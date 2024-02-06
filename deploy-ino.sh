#!/bin/zsh 
# Convenience script to compile and load .ino script

SKETCH="PiezoDriver"
PORT="/dev/cu.usbmodem101"
FQBN="arduino:avr:uno"

arduino-cli compile --fqbn "${FQBN}" "${SKETCH}"
arduino-cli upload -p "${PORT}" --fqbn "${FQBN}" ${SKETCH}