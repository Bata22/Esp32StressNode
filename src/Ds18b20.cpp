#include <OneWire.h>
#include <DallasTemperature.h>
#include "Ds18b20.h"
#define PIN 4

// GPIO where the DS18B20 is connected to
const int oneWireBus = PIN;

// Setup a oneWire instance to communicate with any OneWire devices
OneWire oneWire(oneWireBus);

// Pass our oneWire reference to Dallas Temperature sensor
DallasTemperature sensors(&oneWire);

void initDS18B20()
{   
    // Start the DS18B20 sensor
    sensors.begin();
}
float temperatureDS18B20()
{
    sensors.requestTemperatures();
    float temperatureC = sensors.getTempCByIndex(0);
    float temperatureF = sensors.getTempFByIndex(0);
    Serial.print(temperatureC);
    Serial.println("ºC");
    
    return temperatureC;
}