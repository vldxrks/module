#!/usr/bin/env python3
"""Перевірка всіх статусів/телеметрії та ACK актуатора через справжній брокер."""
import json
import sys
import threading
import time
from pathlib import Path
from mqtt_common import close, connect

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'simulator'))
from model import DEVICES, SENSORS  # noqa: E402


def main():
    client, reason = connect()
    assert not reason.is_failure, str(reason)
    seen = {}
    received = threading.Event()

    def on_message(client, userdata, message):
        seen[message.topic] = message.payload.decode()
        received.set()

    client.on_message = on_message
    try:
        client.subscribe('office/server/#', qos=1)
        end = time.monotonic() + 20
        while time.monotonic() < end:
            statuses = all(seen.get(f'office/server/{d}/status') == 'online' for d in DEVICES)
            telemetry = all(f'office/server/{d}/telemetry' in seen for d in SENSORS)
            states = all(f'office/server/{d}/state' in seen for d in ('ac', 'siren'))
            if statuses and telemetry and states:
                break
            received.wait(0.5)
            received.clear()
        else:
            raise AssertionError('Не всі пристрої online або немає даних; увімкніть normal')
        for name in SENSORS:
            payload = json.loads(seen[f'office/server/{name}/telemetry'])
            assert abs(time.time() - payload['ts']) < 20, f'Застаріла телеметрія {name}'
        print('PASS: 8 статусів online, 6 потоків телеметрії, 2 state')
        # Повторити поточну команду: без зміни стану установки.
        before = json.loads(seen['office/server/ac/state'])
        sent_at = int(time.time())
        client.publish('office/server/ac/set', json.dumps({'state': before['state']}), qos=1)
        end = time.monotonic() + 6
        while time.monotonic() < end:
            after = json.loads(seen['office/server/ac/state'])
            if after['ts'] >= sent_at and after['state'] == before['state']:
                print('PASS: актуатор підтвердив state')
                return
            received.wait(0.25)
            received.clear()
        raise AssertionError('Немає актуального state')
    finally:
        close(client)


if __name__ == '__main__':
    main()
