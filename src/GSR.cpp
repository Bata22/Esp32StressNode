#include <Arduino.h>
#define GSRSonde 35

int calibrateGSR() // for 30 s on 5ms sample
{
  int sensorValue = 0;
  long sum = 0;
  for (int i = 0; i < 6000; i++) 
  {
    sensorValue = analogRead(GSRSonde);
    sum += sensorValue;

    delay(5);
  }
  return sum / 6000;
}
  

int readGSR(int baseline)
{
  int sensorValue = 0;
  int gsrAverage = 0;
  float humanResistance = 0.0;
  long sum = 0;
  for (int i = 0; i < 10; i++)
  {
    sensorValue = analogRead(GSRSonde);
    sum += sensorValue;

    delay(5);
  }
  gsrAverage = sum / 10;
  // konverzija sa 12 bit na 10 bit
  int gsr_10bit = map(gsrAverage, 0, 4095, 0, 1023);
  float numerator = (1024 + 2 * gsr_10bit) * 10000.0;
  float denominator = baseline - gsr_10bit;
  if (denominator != 0)
  {
    humanResistance = numerator / denominator;
  }
  else
  {
    humanResistance = 0;
  }
  
  Serial.print("GSR prosek ");
  Serial.println(gsr_10bit);

  Serial.print("Covekova otpornost ");
  Serial.println(humanResistance);
  return gsr_10bit;
}



