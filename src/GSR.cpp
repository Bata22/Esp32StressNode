#include <Arduino.h>
#define GSRSonde 35

int8_t conncetedGSR;
int calibrateGSR() // for 30 s on 5ms sample
{
  int sensorValue = 0;
  int sensorValueArray[20];
  long sum = 0;
  for (byte i = 0; i < 20; i++)
  {
    sensorValue = analogRead(GSRSonde);
    sensorValueArray[i] = sensorValue;
  }
  for (byte i = 0 ; i < 19; i++)
  {
    if (sensorValueArray[i] == 0)
    {
      conncetedGSR = 0;
      break;
    }
    if ((sensorValueArray[i + 1]) - sensorValueArray[i] > 400)
    {
      conncetedGSR = 0;
      break;
    }
    else
    {
      conncetedGSR = 1;
    }
  }
  if (conncetedGSR == 1)
  {
    for (int16_t i = 0; i < 6000; i++)
    {
      sensorValue = analogRead(GSRSonde);
      // printf("sensorValue %d", sensorValue); Check what value you get from sensors
      sum += sensorValue;
      yield();
      delay(5);
    }
  }
  return sum / 6000;
}

int readGSR()
{
  int sensorValue = 0;
  int gsrAverage = 0;
  long sum = 0;
  for (int i = 0; i < 10; i++)
  {
    sensorValue = analogRead(GSRSonde);
    sum += sensorValue;
    
  }
  gsrAverage = sum / 10;
  
 
  return gsrAverage;
}
