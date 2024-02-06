# quantum-optics
- Use `arduino-cli board list` to find all connected boards. This should also list the “core” for each board, which is essentially their API 
  for talking to the board. In our case it’s `arduino:avr:uno` (the core is just `arduino:avr`)
- Install the corresponding core onto your computer with arduino-cli core install arduino:avr
- Create a “sketch” `arduino-cli sketch new [sketch name]`; this is essentially your “project” which you will compile and load onto board. 
  It should create a folder and a .ino file which is written in the arduino language (variant of C++). 
- Compile with `arduino-cli compile --fqbn arduino:avr:uno [sketch name]`; `fqbn` is the identification for that board
- Upload the compiled code to the board with `upload -p [port] --fqbn arduino:avr:uno [sketch name]`. `[port]` is the port your arduino is 
  connected to, should be listed when you use arduino-cli board list.
- Arduino LED should flash for a bit and then sketch is uploaded.
