#include <Arduino.h>
#include <Wifi.h>
#include "Credentials.h"
#include "WifiMine.h"
IPAddress staticIP(IPADDRESS);
IPAddress gateway(GATEWAY);
IPAddress subnet(SUBNET);

void setup_wifi()
{
    delay(10);
    Serial.println("Povezivanje na wifi... ");
    if (WiFi.config(staticIP,gateway,subnet) == false)
    {
        Serial.println("Configuration failed.");
    }

    delay(1);
    WiFi.mode(WIFI_STA);
    WiFi.begin(SSID, PASS);

    while (WiFi.status() != WL_CONNECTED)
    {
        delay(500);
        Serial.print(".");
        // Serial.println(WiFi.status()); 
        // Serial.print(WiFi.RSSI());  Cheks signals
    }
    Serial.println(WiFi.status());
    Serial.println("\nWifi povezan!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
}
