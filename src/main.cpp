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
#include "SystemInfo.h"

time_t now;
HeartRateSensor resultsMax;
// uint8_t publishFlag = 0;
int baseline;
int GSR;
float temperatureC_DS10B20;
String payloadJson;
String nodeId = "";

void setup()

{
  Serial.begin(115200);
  nodeId = getUniqeNodeId();
  Serial.print("Uredjaj je pokrenut ID: ");
  Serial.println(nodeId);
  setup_wifi();
  baseline = calibrateGSR();
  Serial.println("Initializing...");
  initMAXSensor(); // hr and spo2 sensor
  initDS18B20();
  initMqtt();
  // publishFlag = 1;
}

void loop()
{

  // Set Timestamp
  now = time(NULL);
  connectMqtt();
  
  unsigned long MaxTrajanje = millis();
  // Monitoring HR and spo2 max
  resultsMax = heart_and_spo2_sensor(mqttLoop);
  Serial.print(millis() - MaxTrajanje);
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
  // if (resultsMax.validHeartRate == 1 && resultsMax.validSpo2 == 1 && resultsMax.heartRate > 40 && resultsMax.spo2 > 70)
  // {

  // }
  payloadJson = NodePayload(nodeId,now, resultsMax.heartRate, resultsMax.spo2, resultsMax.validHeartRate, resultsMax.validSpo2, connectedMax30102, GSR, conncetedGSR, temperatureC_DS10B20, connectedDs18b20);
   publishNode(payloadJson);
  // if (publishFlag == 1)
  // {
   
    
  // }
}
