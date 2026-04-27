#include <Arduino.h>
#include <Wire.h>
#include "MAX30102.h"

// const byte RATE_SIZE = 4;
// byte rates[RATE_SIZE];
// byte rateSpot = 0;
// long lastBeat = 0;

// float beatsPerMinute;
// int beatAvg;
// int btnState = 0;

// SP02 setup
// static uint32_t irBuffer[100];
// static uint32_t redBuffer[100];
// static int32_t spo2;
// static int8_t validSPO2;
// static int32_t heartRate;
// static int8_t validHeartRate;
// static byte pulseLED = 11;
// static byte readLED = 13;

void setup()
{
  Serial.begin(115200);
  Serial.println("Initializing...");
  initSensor();
}

void loop()
{
  // Monitoring HR and spo2 max
  HeartRateSensor result = heart_and_spo2_sensor();

  // Print results
  if (result.spo2 > 70 && result.validSpo2 == 1)
  {
    Serial.print("SPO2= ");
    Serial.print(result.spo2);
    Serial.print("|Valid= ");
    Serial.println(result.validSpo2);
  }
  if (result.heartRate > 40 && result.heartRate < 200 && result.validHeartRate == 1)
  {
    Serial.print("HR= ");
    Serial.print(result.heartRate);

    Serial.print(" |Valid= ");
    Serial.println(result.validHeartRate);
  }

  delay(500);
  // TODO: ADD GSR
  // TODO: ADD Temp DS18b20
  // TODO: ADD json payload
}