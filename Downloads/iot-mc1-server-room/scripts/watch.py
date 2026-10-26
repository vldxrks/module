#!/usr/bin/env python3
"""Безпечний аналог mosquitto_sub: паролі не передаються аргументами CLI."""
import signal
import threading
from mqtt_common import close, connect

client, reason = connect()
if reason.is_failure:
    close(client)
    raise SystemExit(str(reason))
stop = threading.Event()
signal.signal(signal.SIGINT, lambda *_: stop.set())
signal.signal(signal.SIGTERM, lambda *_: stop.set())
client.on_message = lambda c, u, m: print(m.topic, m.payload.decode(), flush=True)
client.subscribe('office/server/#', qos=1)
try:
    stop.wait()
finally:
    close(client)
