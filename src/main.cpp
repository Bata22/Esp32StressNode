#include <Arduino.h>
#include <Wire.h>
#include "MAX30102.h"
#include "GSR.h"
#include "Ds18b20.h"
#include <ArduinoJson.h>
#include <time.h>
#include "NodePayload.h"
#include "WifiMine.h"
#include "MQTT.h"

time_t now;
HeartRateSensor resultsMax;
int baseline;
int GSR;
float temperatureC_DS10B20;
String payloadJson;

void setup()
{
  Serial.begin(115200);
  setup_wifi();
  initMqtt();
  baseline = calibrateGSR();
  Serial.println("Initializing...");
  initMAXSensor(); // hr and spo2 sensor
  initDS18B20();
}

void loop()
{
  // Set Timestamp
  now = time(NULL);
  connectMqtt();

  // Monitoring HR and spo2 max
  resultsMax = heart_and_spo2_sensor();

  // Print results
  if (resultsMax.spo2 > 70 && resultsMax.validSpo2 == 1)
  {
    Serial.print("SPO2= ");
    Serial.print(resultsMax.spo2);
    Serial.print("|Valid= ");
    Serial.println(resultsMax.validSpo2);
  }
  if (resultsMax.heartRate > 40 && resultsMax.heartRate < 200 && resultsMax.validHeartRate == 1)
  {
    Serial.print("HR= ");
    Serial.print(resultsMax.heartRate);

    Serial.print(" |Valid= ");
    Serial.println(resultsMax.validHeartRate);
  }
  delay(500);
  GSR = readGSR(baseline);
  delay(100);
  temperatureC_DS10B20 = temperatureDS18B20();
  // TODO: ADD json payload
  if (resultsMax.validHeartRate == 1 && resultsMax.validSpo2 == 1 && resultsMax.heartRate > 40 && resultsMax.spo2 > 70)
  {
    payloadJson = NodePayload(now, resultsMax.heartRate, resultsMax.spo2, GSR, temperatureC_DS10B20);
    publishNode(payloadJson);
  }

  
}
