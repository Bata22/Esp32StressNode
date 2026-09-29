#include <ArduinoJson.h>
#include "NodePayload.h"
String NodePayload(uint32_t seq, uint32_t nodeMs, int heartRate, int8_t validHeartRate, int spo2, int8_t validSpo2, int gsr[], int gsrCount, float temperatureC,int8_t connectedMax30102, int8_t connectedGSR, int8_t connectedDs18b20)
{
    JsonDocument jsonDoc;

    jsonDoc["fw"] = PAYLOAD_FORMAT;
    jsonDoc["seq"] = seq;
    jsonDoc["node_ms"] = nodeMs;

    // TODO: NTP sync when gateway available
    JsonObject sensorData = jsonDoc["sensorData"].to<JsonObject>();
    sensorData["HeartRate"] = heartRate;
    sensorData["heartRateValid"] = validHeartRate;
    sensorData["SpO2"] = spo2;
    sensorData["Spo2Valid"] = validSpo2;
    JsonArray gsrArr = sensorData["GSR"].to<JsonArray>();
    for (int i = 0; i < gsrCount; i++)
    {
        gsrArr.add(gsr[i]);
    }
    sensorData["Temperature"] = temperatureC;
    JsonObject sensorsOk = jsonDoc["sensors_ok"].to<JsonObject>();
    sensorsOk["max"] = connectedMax30102;
    sensorsOk["gsr"] = connectedGSR;
    sensorsOk["temp"] = connectedDs18b20;
    String response;
    serializeJson(jsonDoc, response);

    return response;
}
