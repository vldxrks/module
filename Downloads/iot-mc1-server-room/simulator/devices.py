#!/usr/bin/env python3
"""Вісім незалежних процесів / MQTT-сесій, кожна зі своїм користувачем і LWT."""
import argparse
import json
import logging
import multiprocessing as mp
import os
from pathlib import Path
import signal
import ssl
import threading
import time

import paho.mqtt.client as mqtt

from model import ACTUATORS, DEVICES, SCENARIOS, Model, apply_command, initial_state

LOG = logging.getLogger("simulator")
BASE = "office/server"


def control_path():
    return Path(os.getenv("CONTROL_DIR", ".runtime/control")) / "scenario.json"


def read_scenario():
    try:
        name = json.loads(control_path().read_text())["scenario"]
        return name if name in SCENARIOS else "normal"
    except (OSError, ValueError, KeyError, TypeError):
        return "normal"


def write_scenario(name):
    path = control_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps({"scenario": name}), encoding="utf-8")
    tmp.replace(path)
    print(f"Сценарій: {name}")


class Device:
    def __init__(self, name):
        self.name = name
        self.root = f"{BASE}/{name}"
        self.stop = threading.Event()
        self.lock = threading.Lock()
        self.state = initial_state(name) if name in ACTUATORS else None
        self.model = Model(name)
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                                  client_id=f"device-{name}", protocol=mqtt.MQTTv5)
        self.client.username_pw_set(name, os.environ[f"MQTT_PASSWORD_{name.upper()}"])
        ctx = ssl.create_default_context(cafile=os.getenv("MQTT_CA", "/certs/ca.crt"))
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        self.client.tls_set_context(ctx)
        self.client.will_set(f"{self.root}/status", "offline", qos=1, retain=True)
        self.client.reconnect_delay_set(min_delay=1, max_delay=15)
        self.client.max_queued_messages_set(50)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def publish_state(self):
        with self.lock:
            payload = {**self.state, "ts": int(time.time())}
        return self.client.publish(f"{self.root}/state", json.dumps(payload), qos=1, retain=True)

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            LOG.error("%s: з'єднання відхилене: %s", self.name, reason_code)
            return
        client.publish(f"{self.root}/status", "online", qos=1, retain=True)
        if self.state is not None:
            client.subscribe(f"{self.root}/set", qos=1)
            self.publish_state()
        LOG.info("%s online", self.name)

    def on_message(self, client, userdata, message):
        if self.state is None or message.topic != f"{self.root}/set":
            return
        try:
            if len(message.payload) > 512:
                raise ValueError("Завелика команда")
            command = json.loads(message.payload.decode("utf-8"))
            with self.lock:
                self.state = apply_command(self.name, self.state, command)
            self.publish_state()
            LOG.info("%s: команду застосовано", self.name)
        except (ValueError, UnicodeError):
            LOG.warning("%s: некоректну команду відхилено", self.name)

    def run(self):
        signal.signal(signal.SIGTERM, lambda *_: self.stop.set())
        signal.signal(signal.SIGINT, lambda *_: self.stop.set())
        self.client.connect_async(os.getenv("MQTT_HOST", "mosquitto"),
                                  int(os.getenv("MQTT_PORT", "8883")), keepalive=10)
        self.client.loop_start()
        started = time.monotonic()
        try:
            while not self.stop.is_set():
                scenario = read_scenario()
                if self.client.is_connected():
                    if self.state is not None:
                        # Повторення state дозволяє виявляти/відновлювати стан актуаторів.
                        self.publish_state()
                    elif not (scenario == "silent-hot" and self.name == "hot"):
                        payload = self.model.sample(scenario, time.monotonic() - started)
                        payload["ts"] = int(time.time())
                        self.client.publish(f"{self.root}/telemetry", json.dumps(payload),
                                            qos=1, retain=False)
                self.stop.wait(2)
        finally:
            if self.client.is_connected():
                self.client.publish(f"{self.root}/status", "offline", qos=1,
                                    retain=True).wait_for_publish(timeout=3)
            self.client.disconnect()
            self.client.loop_stop()


def run_device(name):
    Device(name).run()


def supervise():
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    children = {}
    try:
        while not stop.is_set():
            scenario = read_scenario()
            for name in DEVICES:
                child = children.get(name)
                if scenario == f"offline-{name}":
                    if child and child.is_alive():
                        # SIGKILL: без DISCONNECT, брокер сам надсилає Last Will.
                        child.kill()
                        child.join(timeout=3)
                        LOG.warning("%s: аварійне завершення для перевірки LWT", name)
                    continue
                if child is None or not child.is_alive():
                    if child is not None:
                        child.join(timeout=1)
                    child = mp.Process(target=run_device, args=(name,), name=name)
                    child.start()
                    children[name] = child
            stop.wait(1)
    finally:
        for child in children.values():
            if child.is_alive():
                child.terminate()
        for child in children.values():
            child.join(timeout=6)
            if child.is_alive():
                child.kill()
                child.join(timeout=2)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=SCENARIOS, help="Змінити сценарій працюючої системи")
    parser.add_argument("--device", choices=DEVICES, help="Запустити лише один пристрій")
    args = parser.parse_args()
    if args.scenario:
        write_scenario(args.scenario)
    elif args.device:
        run_device(args.device)
    else:
        supervise()
