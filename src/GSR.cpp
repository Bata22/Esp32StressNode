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
    if (sensorValue == 0)
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

      delay(5);
    }
  }
  return sum / 6000;
}

int readGSR(int baseline)
{
  int sensorValue = 0;
  int gsrAverage = 0;
  float humanResistance = 0.0;
  long sum = 0;
  unsigned long lastAttempt = 0;
  for (int i = 0; i < 10; i++)
  {
    sensorValue = analogRead(GSRSonde);
    sum += sensorValue;
    if (millis() - lastAttempt > 5)
    {
      lastAttempt = millis();
    }
    // delay(5); i   vTaskDelay(5/ portTICK_PERIOD_MS); ali radi samo ako se podele taskovi
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
