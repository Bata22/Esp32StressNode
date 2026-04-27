#include "Max30102.h"
#include "MAX30105.h"
#include "spo2_algorithm.h"
#include <Wire.h>
MAX30105 sensorLib;
HeartRateSensor sensor;
    uint32_t irBuffer[100];
    uint32_t redBuffer[100]; 

void initSensor(){
      // Inicialisation sensor
  if (!sensorLib.begin(Wire, I2C_SPEED_FAST)) // Use I2C port, f = 400kHz
  {
    Serial.println("MAX30102 nije pronađen. Proverite žice / napajanje.");
    while (1);
  }
 

  sensorLib.setup(); 
  sensorLib.setPulseAmplitudeRed(0x0A); 
  sensorLib.setPulseAmplitudeGreen(0); 
  sensorLib.enableDIETEMPRDY();
  

}   
HeartRateSensor heart_and_spo2_sensor(){
    for (byte i = 0; i < 100; i++){
        while (sensorLib.available() == false)
            sensorLib.check(); // Proveri senzor za nove podatke

        redBuffer[i] = sensorLib.getRed();
        irBuffer[i] = sensorLib.getIR();
        sensorLib.nextSample();
    }

    maxim_heart_rate_and_oxygen_saturation(irBuffer, 100, redBuffer, &sensor.spo2, &sensor.validSpo2, &sensor.heartRate, &sensor.validHeartRate);
    return sensor;
}

