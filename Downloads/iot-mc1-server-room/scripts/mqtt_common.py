"""Спільне підключення інструментів; секрети тільки зі змінних середовища."""
import os
import ssl
import threading
import uuid

import paho.mqtt.client as mqtt


def connect(user="admin", authenticated=True, timeout=10):
    ready = threading.Event()
    result = []
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                         client_id=f"check-{uuid.uuid4().hex[:10]}", protocol=mqtt.MQTTv5)
    if authenticated:
        client.username_pw_set(user, os.environ[f"MQTT_PASSWORD_{user.upper()}"])
    context = ssl.create_default_context(cafile=os.getenv("MQTT_CA", "/certs/ca.crt"))
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    client.tls_set_context(context)

    def on_connect(client, userdata, flags, reason, properties):
        result.append(reason)
        ready.set()

    client.on_connect = on_connect
    client.connect(os.getenv("MQTT_HOST", "mosquitto"), int(os.getenv("MQTT_PORT", "8883")), 10)
    client.loop_start()
    if not ready.wait(timeout):
        client.disconnect()
        client.loop_stop()
        raise TimeoutError("Немає CONNACK")
    return client, result[0]


def close(client):
    client.disconnect()
    client.loop_stop()
