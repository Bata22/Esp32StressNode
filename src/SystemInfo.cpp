#include "SystemInfo.h"
String getUniqeNodeId(){
    static String chachedID = "";
    
    if (chachedID == ""){
        uint64_t chipId = ESP.getEfuseMac();

        String highPart = String ((uint32_t)(chipId >> 32), HEX);
        highPart.toUpperCase();

        uint32_t lowerPart = (uint32_t)chipId;

        char buffer[9];
        sprintf(buffer, "%08X", lowerPart);

        chachedID = "ESP32_" + highPart + String(buffer);
    }

    return chachedID;
}

