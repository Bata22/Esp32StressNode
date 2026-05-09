#include <Arduino.h>
#include <time.h>

String NodePayload(time_t now, int heartRate, int spo2,int8_t validHeartRate, int8_t validSpo2, int8_t connectedMax30102, int gsr, int8_t connectedGSR, float temperatureC, int8_t connectedDs18b20);