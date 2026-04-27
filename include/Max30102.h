
#include <stdint.h>


struct HeartRateSensor {
    int32_t heartRate; 
    int8_t validHeartRate; 
    int32_t spo2; 
    int8_t validSpo2;
};

HeartRateSensor heart_and_spo2_sensor();
void initSensor();
 

