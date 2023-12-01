#define PIN_COUNT 10  // using this many digital pins for output
#define PIN_BASE  4   // this is the lowest digital pin number used for output
#define BIGGEST_WORD (1<<PIN_COUNT)  // largest # we can output = 2^PIN_COUNT
#define BUFLEN    128

#define OUTMIN  (0.0)
#define OUTMAX (10.0)

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