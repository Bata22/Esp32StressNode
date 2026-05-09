#include <ArduinoJson.h>
#include <time.h>
#include "NodePayload.h"
String NodePayload(time_t now, int heartRate, int spo2,int8_t validHeartRate, int8_t validSpo2, int8_t connectedMax30102, int gsr, int8_t connectedGSR, float temperatureC, int8_t connectedDs18b20)
{
    JsonDocument jsonDoc; // StaticJsonDocument<200>
    // TODO: dynamic NODEID when i have more nodes
    jsonDoc["NodeID"] = "01-ESP32";
    // TODO: NTP sync when gateway available
    jsonDoc["TimeStamp"] = (uint32_t)now;
    JsonObject sensorData = jsonDoc["sensorData"].to<JsonObject>();
    sensorData["HeartRate"] = heartRate;
    sensorData["SpO2"] = spo2;
    sensorData["GSR"] = gsr;
    sensorData["Temperature"] = temperatureC;
    // TODO: dynamic cheks for sensor response and do concatenation stings
    if (connectedMax30102 == 1 && connectedGSR == 1 && connectedDs18b20 == 1 && validHeartRate == 1 && validSpo2 == 1 )
    {
        jsonDoc["ErrorMessage"] = "RADI";
    }else
    {
        String error = "MaxConecctionValue " + String(connectedMax30102) + " Valid HR  "+ String(validHeartRate) + " Valid Sp02"+ String(validSpo2) + " , GSRConnectionValue" + String(connectedGSR) + " , Ds18b20ConnectionValue" + String(connectedDs18b20);
        jsonDoc["ErrorMessage"] = error ;
    }

    String response;
    serializeJson(jsonDoc, response);

    return response;
}
