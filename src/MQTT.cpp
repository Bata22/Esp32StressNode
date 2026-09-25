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
    client.setBufferSize(512);
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
    Serial.printf("[DIAG] MQTT pao : state= %d wifi= %d rssi = %d dBm  heap = %d maxAllocHeap = %d\n", client.state(), WiFi.status(), WiFi.RSSI(), ESP.getFreeHeap(), ESP.getMaxAllocHeap());
    while (!client.connected())
    {
        myId = getUniqeNodeId(); // nodeId mac address
        Serial.print("Pokusaj za MQTT povezivanjem...");
        Serial.println(myId);

        String statusTopic = "api/v1/esp32/"+ myId + "/status";

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

void publishNode(String nodePayload)
{

    if (!client.connected()){
        return;
    }
    
    String dynamicTopic = "api/v1/esp32/" + myId + "/telemetry";
    bool success = client.publish(dynamicTopic.c_str(), nodePayload.c_str());
    if (!success)
    {
        Serial.print("Publish telemetry failed");
    }
}

void publishCalibrationGsr(int baseline)
{
    if (!client.connected()) return;
    String topic = "api/v1/esp32/"+myId+ "/calibration";
    String payload = "{\"gsr_baseline\":"+ String(baseline) + "}";
    client.publish(topic.c_str(), payload.c_str(), true); //ostaje uvek true
}