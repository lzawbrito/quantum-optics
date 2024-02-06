#define PIN_COUNT 10  // using this many digital pins for output
#define PIN_BASE  4   // this is the lowest digital pin number used for output
#define OUTMIN  (0.0)
#define OUTMAX (10.0)
#define PERIOD 300

// https://arduino.github.io/arduino-cli/0.34/getting-started/
void setup() {
  int p;
  // use pins 4-10 as output
  for(p=0; p<PIN_COUNT; p++)
    pinMode(p + PIN_BASE, OUTPUT);
}

void loop() {
  int p;

  for(p=0; p<PIN_COUNT; p++)
    digitalWrite(p, HIGH);
  
}
// all pins on .300 V
// pins 13 and 14 off -> .077 V
// pin 14 off -> .151 V