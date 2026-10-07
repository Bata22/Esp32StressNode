"""
Pi4 gateway - deo 1: prima telemetriju sa svih cvorova i snima u CSV.

Instalacija na Pi OS (Bookworm ne dozvoljava pip van virtuelnog okruzenja):
    python3 -m venv ~/stress-env
    source ~/stress-env/bin/activate
    pip install paho-mqtt

Pokretanje:
    python pi_subscriber.py
"""

import csv
import json
from datetime import datetime
from pathlib import Path

import paho.mqtt.client as mqtt

BROKER = "localhost"  # skripta radi na istom Pi-ju kao Mosquitto
TELEMETRY_TOPIC = "api/v1/esp32/+/telemetry"  # + = bilo koji ID cvora
STATUS_TOPIC = "api/v1/esp32/+/status"
LOG_DIR = Path("sessions")
LOG_DIR.mkdir(exist_ok=True)

# Jedan CSV po cvoru po danu, npr. sessions/ESP32_BCCB..._2026-06-10.csv
CSV_FIELDS = ["pi_time", "node_time", "heart_rate", "spo2", "gsr",
              "temperature", "error_message"]


def node_id_from_topic(topic: str) -> str:
    # "api/v1/esp32/ESP32_XXX/telemetry" -> deo sa indeksom 3
    return topic.split("/")[3]


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Povezan na broker (kod: {reason_code})")
    client.subscribe(TELEMETRY_TOPIC)
    client.subscribe(STATUS_TOPIC)


def on_message(client, userdata, msg):
    node_id = node_id_from_topic(msg.topic)
    text = msg.payload.decode()

    if msg.topic.endswith("/status"):
        print(f"[{node_id}] status: {text}")
        return

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        print(f"[{node_id}] neispravan JSON, preskacem: {text}")
        return

    sensors = data.get("sensorData", {})
    row = {
        # Vreme Pi-ja, ne cvora - ESP32 nema tacan sat bez NTP-a
        "pi_time": datetime.now().isoformat(timespec="seconds"),
        "node_time": data.get("TimeStamp"),
        "heart_rate": sensors.get("HeartRate"),
        "spo2": sensors.get("SpO2"),
        "gsr": sensors.get("GSR"),
        "temperature": sensors.get("Temperature"),
        "error_message": data.get("ErrorMessage"),
    }

    csv_path = LOG_DIR / f"{node_id}_{datetime.now().date()}.csv"
    is_new = not csv_path.exists()
    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow(row)

    print(f"[{node_id}] HR={row['heart_rate']} SpO2={row['spo2']} "
          f"GSR={row['gsr']} T={row['temperature']}")


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, 1883)
client.loop_forever()
