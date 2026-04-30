#include <WiFi.h>
#include <PubSubClient.h>
#include "Credentials.h"
#include "MQTT.h"
WiFiClient espClient;
PubSubClient client(espClient);

const char *mqtt_server = MQTTSERVER;
const uint16_t mqtt_port = MQTTPORT;

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
            delay(3000);
        }
    }
}

void publishNode(String nodePayload)
{
    client.publish("api/esp32/node", nodePayload.c_str());
    if (!client.publish("api/esp32/node", nodePayload.c_str())) {
    Serial.println("Publish failed");
}
}