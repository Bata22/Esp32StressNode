#include <WiFi.h>
#include <PubSubClient.h>
#include "Credentials.h"
#include "MQTT.h"
WiFiClient espClient;
PubSubClient client(espClient);

const char *mqtt_server = MQTTSERVER;
const uint16_t mqtt_port = MQTTPORT;

unsigned long lastAttempt = 0;

void initMqtt()
{
    client.setServer(mqtt_server, mqtt_port);
}

void connectMqtt()
{
    if (!client.connected())
    {
        reconnectMqtt();
    }
    client.loop();
}
void reconnectMqtt()
{
    while (!client.connected())
    {
        Serial.print("Pokusaj za MQTT povezivanjem...");
        if (client.connect("ESP32_KAPIJA"))
        {
            Serial.println("Povezan!");
        }
        else
        {
            Serial.print("Ne uspesno, rc=");
            Serial.print(client.state());
            Serial.println(" pokusava ponovo...");
            if (millis() - lastAttempt > 3000)
            {
                lastAttempt = millis();
            }
        }
    }
}
// NAJVISE MI MIRISE DA OVO JEBE PROGRAM
void publishNode(String nodePayload)
{
    client.publish("api/V1/esp32/node", nodePayload.c_str());
    if (!client.publish("api/V1/esp32/node", nodePayload.c_str()))
    {
        Serial.println("Publish failed");
    }
}