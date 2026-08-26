#include <WiFi.h>
#include <PubSubClient.h>
#include "Credentials.h"
#include "MQTT.h"
#include "SystemInfo.h"
//TODO: ADD account and ttl encripiton for comunication
WiFiClient espClient;
PubSubClient client(espClient);

String myId = "";
const char *mqtt_server = MQTTSERVER;
const uint16_t mqtt_port = MQTTPORT;

unsigned long lastAttempt = 0;

void initMqtt()
{
    client.setServer(mqtt_server, mqtt_port);
}
bool mqttLoop()
{
    return client.loop();
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
        myId = getUniqeNodeId(); // nodeId mac address
        Serial.print("Pokusaj za MQTT povezivanjem...");
        Serial.println(myId);

        String statusTopic = "api/v1/esp32"+ myId + "/status";

        if (client.connect(myId.c_str(), statusTopic.c_str(), 0, true, "offline"))
        {
            Serial.println("Povezan!");
            client.publish(statusTopic.c_str(), "online", true);
        }
        else
        {
            Serial.print("Ne uspesno, rc=");
            Serial.print(client.state());
            Serial.println(" pokusava ponovo...");
            if (millis() - lastAttempt > 3000)
            {
                lastAttempt = millis();
                // client.connect("ESP32_KAPIJA");
            }
        }
    }
}
// NAJVISE MI MIRISE DA OVO JEBE PROGRAM
void publishNode(String nodePayload)
{

    if (!client.connected()){
        return;
    }
    
    String dynamicTopic = "api/v1/esp32" + myId + "/telemetry";
    bool success = client.publish(dynamicTopic.c_str(), nodePayload.c_str());
    if (!success)
    {
        Serial.print("Publish telemetry failed");
    }
}