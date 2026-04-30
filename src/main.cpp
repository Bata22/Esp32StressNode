#include <Arduino.h>
#include <Wire.h>
#include "MAX30102.h"
#include "GSR.h"
#include "Ds18b20.h"

int baseline;
void setup()
{
  Serial.begin(115200);
  baseline = calibrateGSR();
  Serial.println("Initializing...");
  initMAXSensor(); // hr and spo2 sensor
  initDS18B20();
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
  readGSR(baseline);
  delay(100);
  temperatureDS18B20();
  // TODO: ADD json payload
}