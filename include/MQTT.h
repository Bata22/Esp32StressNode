#include <Arduino.h>
void initMqtt();
void connectMqtt();
void reconnectMqtt();
void publishNode(String nodePayload);