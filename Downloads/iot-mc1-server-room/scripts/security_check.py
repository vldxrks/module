#!/usr/bin/env python3
"""Реальні негативні перевірки брокера. Exit 1, якщо захист не підтверджено."""
import os
import socket
import threading
import time
from mqtt_common import close, connect


def main():
    host = os.getenv("MQTT_HOST", "mosquitto")
    port = int(os.getenv("MQTT_PORT", "8883"))
    client, reason = connect(authenticated=False)
    try:
        assert reason.is_failure, "Анонімний клієнт був допущений"
        assert reason.value in (134, 135), f"Інша причина відмови: {reason}"
        print(f"PASS без пароля: CONNACK {reason}")
    finally:
        close(client)

    with socket.socket() as sock:
        sock.settimeout(3)
        assert sock.connect_ex((host, 1883)) != 0, "1883 доступний"
    print("PASS порт 1883 закритий")

    # Коректний plaintext MQTT 3.1.1 CONNECT надсилаємо на TLS-listener.
    packet = bytes.fromhex('101000044d5154540402000a000474657374')
    with socket.create_connection((host, port), timeout=5) as sock:
        sock.settimeout(3)
        sock.sendall(packet)
        try:
            response = sock.recv(4)
        except (ConnectionResetError, socket.timeout):
            response = b''
        assert not response.startswith(b'\x20'), "Отримано plaintext CONNACK"
    print("PASS без TLS: MQTT-з'єднання не встановлено")

    client, reason = connect(user="cold")
    try:
        assert not reason.is_failure, f"cold не автентифіковано: {reason}"
        published = threading.Event()
        results = []

        def on_publish(client, userdata, mid, reason, properties):
            results.append(reason)
            published.set()

        client.on_publish = on_publish
        # MQTT 5 повертає негативний PUBACK, на відміну від MQTT 3.1.1.
        client.publish('office/server/ac/set', '{"state":"ON"}', qos=1, retain=False)
        assert published.wait(5), "Немає PUBACK, ACL ще не підтверджено"
        assert results[0].value == 135, f"Очікували Not authorized, отримали {results[0]}"
        print(f"PASS чужий топік: PUBACK {results[0]}")
    finally:
        close(client)
    print("Усі перевірки безпеки пройдено. Перегляньте docker compose logs mosquitto.")


if __name__ == '__main__':
    main()
