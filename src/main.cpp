#include <Arduino.h>
#include <Wire.h>
#include "MAX30102.h"
#include "GSR.h"
#include "Ds18b20.h"
#include <ArduinoJson.h>
#include <time.h>

time_t now;
HeartRateSensor resultsMax;
int baseline;
int GSR;
float temperatureC_DS10B20;
void NodePayload();
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
  //Set Time stamp
  now = time(NULL);
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
  NodePayload();
}

void NodePayload() {
  JsonDocument jsonDoc; //StaticJsonDocument<200>
  //TODO: dynamic NODEID when i have more nodes
  jsonDoc["NodeID"] = "01-ESP32";
  //TODO: NTP sync when gateway available
  jsonDoc["TimeStamp"] = (uint32_t)now;
  JsonObject sensorData = jsonDoc["sensorData"].to<JsonObject>();
  sensorData["HeartRate"] = resultsMax.heartRate;
  sensorData["SpO2"] = resultsMax.spo2;
  sensorData["GSR"] =  GSR;
  sensorData["Temperature"] = temperatureC_DS10B20;
  //TODO: dynamic cheks for sensor response and do concatenation stings
  jsonDoc["ErrorMessage"] = "RADI"; 

     String response;
  serializeJson(jsonDoc, response);
  //TODO: Send to mqtt broker
  Serial.println(response);
  }
