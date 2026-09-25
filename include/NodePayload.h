#ifndef NODE_PAYLOAD_H
#define NODE_PAYLOAD_H
#define PAYLOAD_FORMAT 2
#include <Arduino.h>

//Time need to get from pi4
String NodePayload(uint32_t seq, uint32_t nodeMs, int heartRate, int8_t validHeartRate, int spo2, int8_t validSpo2, int gsr[], int gsrCount, float temperatureC,int8_t connectedMax30102, int8_t connectedGSR, int8_t connectedDs18b20);

#endif