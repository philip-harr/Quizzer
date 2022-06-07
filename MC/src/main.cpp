#include <Arduino.h>

#define QUIZ_PIN0 8
#define QUIZ_PIN1 22
#define QUIZ_PIN2 24
#define QUIZ_PIN3 26
#define QUIZ_PIN4 28
#define QUIZ_PIN5 30

#define NO_PIN 0x7b

struct HandlePin
{
// public:
  HandlePin(uint8_t pinNr);
  ~HandlePin();

  bool readPin();
// private:
  uint8_t pin;
  uint8_t pinMask;
  volatile uint8_t* pinPort;
};

HandlePin::HandlePin(uint8_t pinNr)
{
  pin=pinNr;
  pinMode(pinNr, INPUT_PULLUP);
  pinMask = digitalPinToBitMask(pinNr);
  pinPort = portInputRegister(digitalPinToPort(pinNr));
}

bool HandlePin::readPin()
{
  return digitalRead(pin);
  return (pinMask & *pinPort) != 0;
}


HandlePin *pinList[6];
int8_t latestPinPress = NO_PIN;


void setup() 
{
  pinList[0] = new HandlePin(QUIZ_PIN0);
  pinList[1] = new HandlePin(QUIZ_PIN1);
  pinList[2] = new HandlePin(QUIZ_PIN2);
  pinList[3] = new HandlePin(QUIZ_PIN3);
  pinList[4] = new HandlePin(QUIZ_PIN4);
  pinList[5] = new HandlePin(QUIZ_PIN5);

  Serial.begin(500000);
  while(!Serial){}
  // Serial.write("Chip is up and running\n");
}



void readPins()
{
  if(latestPinPress == NO_PIN)
  {
    for(int8_t i = 0; i < 6; ++i)
    {
      if(! (pinList[i])->readPin())
      {
        // Serial.write("Pin is high\n");
        latestPinPress = i;
        break;
      }
        // Serial.write("Pin is low");
    }
  }
}

void clearPin()
{
  latestPinPress = NO_PIN;
}

void processCmd(uint8_t * cmd)
{

  if(cmd[0] == 0x47 && cmd[1]==0x50) //get pin
  {
    Serial.write(latestPinPress);
    // Serial.write("CMD Get Pin\n");
  }
  else if(cmd[0] == 0x43 && cmd[1]==0x50) //clear pin
  {
    clearPin();
    // Serial.write("CMD Clear Pin\n");
  }
  else
  {
    String toSend = "Invalid CMd: " + String((char*)cmd) + "\n";
    Serial.write(toSend.c_str());
  }
}

void loop() 
{
  if(Serial.available() > 0)
  {
    // Serial.write("Processing CMD");
    uint8_t buf[15];
    Serial.readBytesUntil('\n', buf, 15);
    // Serial.write("received...\n\n");
    // Serial.write(buf, 3);
    // Serial.write("\nreceived..\n");
    processCmd(buf);
  }
  else if(latestPinPress == NO_PIN)
  {
    // Serial.write("Measuring");
    readPins();
    delayMicroseconds(100);
  }
  else
  {
    // Serial.write("Waiting for CMD");
    delay(10);
  }
}