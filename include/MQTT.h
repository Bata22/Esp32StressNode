#include <Arduino.h>
void initMqtt();
bool mqttLoop();
void connectMqtt();
void reconnectMqtt();
void publishNode(String nodePayload);