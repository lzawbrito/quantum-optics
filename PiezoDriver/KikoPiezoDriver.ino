// analog_out.ino. Copied from https://egalvez.colgate.domains/web/research/Photon/root/arduino33.txt
//
//
// Primary computer writes instructions to serial port (COM1, COM2, etc).
// Arduino reads from serial port, and outputs that analog voltage.
//
// 02mar2015, stz -- remove all Serial.print() statements.
//                   these are implicated in serial coms slow-downs!


#define PIN_COUNT 10  // using this many digital pins for output
#define PIN_BASE  4   // this is the lowest digital pin number used for output
#define BIGGEST_WORD (1<<PIN_COUNT)  // largest # we can output = 2^PIN_COUNT
#define BUFLEN    128

#define OUTMIN  (0.0)
#define OUTMAX (10.0)


// setup()
//
// arduino required function.
// runs once only at power-up or at reset
//
void setup()
{ int i,p;
  
  // designate pins we are using for output.
  for(p=0; p<PIN_COUNT; p++)
    pinMode(p + PIN_BASE, OUTPUT);
  
  // start Arduino's serial port @ 9600 baud.
//  Serial.begin(9600);
  Serial.begin(115200);

  
  // set all output pins initially to ZERO.
  for(p=0; p<PIN_COUNT; p++)
    digitalWrite(p + PIN_BASE, LOW);
}

// digitalWriteWord(int)
//
// utility function to put a binary word bitwise onto all the output pins.
// 'w' is the word we wish to express on the output pins.
// 'p' variable counts up through pins.
// 'm' variable is a mask, with only one bit set HIGH. 
//     effectively a shift register, 'm' shifts left (up to LSB) 1 bit position
//     each time through loop.
//
void digitalWriteWord(int w)
{ int p,m;
  
  if(w >= BIGGEST_WORD)
    w = BIGGEST_WORD - 1;
  else if(w < 0)
    w = 0;
  
  for(p=0, m=1; p<PIN_COUNT; p++, m<<=1)
    digitalWrite(p + PIN_BASE, (w&m ? HIGH : LOW));
}

// loop()

void loop()
{ int cmd;
  char b[BUFLEN];
  float x,y;
  
  if(Serial.available() > 0)  // if bytes are waiting for us in the serial port...
  {
    x = Serial.parseFloat();  // try to read them as a floating point number
    if(x >= OUTMIN
    && x <= OUTMAX)
    { 
      y = BIGGEST_WORD * ((x - OUTMIN) / (OUTMAX - OUTMIN));  // range mapping
      digitalWriteWord((int)y);  // express that voltage at the output.
    }
    else // out of range
    { // send an error message back through the serial port.
      // You won't see this, unless you have opened the Serial Monitor in
      //  the arduino IDE, while the program is running.
      
      // found hint online that Serial.print is implicated in
      // slow-down of serial coms -- don't do this!
      
      /**
      Serial.print("Range Error: asked to output ");
      Serial.println(x);
      Serial.print("  OUTMIN = ");
      Serial.println(OUTMIN);
      Serial.print("  OUTMAX = ");
      Serial.println(OUTMAX);
      **/
    }
    Serial.readBytesUntil('\n',b,BUFLEN);  // read & discard newline
  }
}

// eof