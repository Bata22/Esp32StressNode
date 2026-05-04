#include <ArduinoJson.h>
#include <time.h>
#include "NodePayload.h"
String NodePayload(time_t now, int heartRate, int spo2, int gsr, float temperatureC)
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
    jsonDoc["ErrorMessage"] = "RADI";

    String response;
    serializeJson(jsonDoc, response);

    return response;
}
