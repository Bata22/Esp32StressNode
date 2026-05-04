#include <Arduino.h>
#include <time.h>

String NodePayload(time_t now, int heartRate, int spo2, int gsr, float temperatureC);