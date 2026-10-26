#!/usr/bin/env python3
"""Інтеграція без Docker. Потрібні mosquitto 2.x, mosquitto_passwd і paho-mqtt.

MOSQUITTO_BIN=/path/mosquitto MOSQUITTO_PASSWD_BIN=/path/mosquitto_passwd \
  python3 tests/native_integration.py
Тест створює тимчасові секрети, запускає брокер на вільному локальному порту,
справжній supervisor із 8 пристроями, перевіряє ACL/TLS і LWT після SIGKILL.
"""
import json
import os
from pathlib import Path
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'simulator'))
sys.path.insert(0, str(ROOT / 'scripts'))
from model import DEVICES  # noqa: E402
from mqtt_common import close, connect  # noqa: E402


def wait_for(predicate, timeout=20):
    deadline = time.monotonic() + timeout
    tick = threading.Event()
    while time.monotonic() < deadline:
        if predicate():
            return
        tick.wait(0.1)
    raise AssertionError('Очікуваної події не отримано')


def main():
    broker_bin = os.getenv('MOSQUITTO_BIN') or shutil.which('mosquitto')
    passwd_bin = os.getenv('MOSQUITTO_PASSWD_BIN') or shutil.which('mosquitto_passwd')
    if not broker_bin or not passwd_bin:
        raise SystemExit('Потрібні mosquitto і mosquitto_passwd; Docker-тести описано в README.')
    broker = simulator = observer = None
    with tempfile.TemporaryDirectory(prefix='.native-check-', dir=ROOT) as directory:
        work = Path(directory)
        env = os.environ.copy()
        for name in (*DEVICES, 'admin', 'openhab'):
            env[f'MQTT_PASSWORD_{name.upper()}'] = secrets.token_hex(24)
        passwd = work / 'passwd'
        # Окремі нові файли не потребують системного /tmp.
        # -b лише для одноразових тестових секретів, не production bootstrap.
        hashes = []
        for name in (*DEVICES, 'admin', 'openhab'):
            part = work / f'passwd-{name}'
            completed = subprocess.run([passwd_bin, '-b', '-c', str(part), name,
                                        env[f'MQTT_PASSWORD_{name.upper()}']], capture_output=True)
            if completed.returncode:
                raise RuntimeError('mosquitto_passwd: ' + completed.stderr.decode())
            hashes.append(part.read_text())
            part.unlink()
        passwd.write_text(''.join(hashes))
        passwd.chmod(0o600)
        subprocess.run(['sh', str(ROOT / 'certs/generate.sh')], cwd=ROOT,
                       check=True, capture_output=True)
        with socket.socket() as port_sock:
            port_sock.bind(('127.0.0.1', 0))
            port = port_sock.getsockname()[1]
        env.update(MQTT_HOST='localhost', MQTT_PORT=str(port),
                   MQTT_CA=str(ROOT / '.runtime/certs/ca.crt'), CONTROL_DIR=str(work / 'control'))
        conf = (ROOT / 'mosquitto/config/mosquitto.conf').read_text()
        conf = conf.replace('listener 8883 0.0.0.0', f'listener {port} 127.0.0.1')
        conf = conf.replace('/mosquitto/config/passwd', str(passwd))
        conf = conf.replace('/mosquitto/config/acl', str(ROOT / 'mosquitto/config/acl'))
        conf = conf.replace('/mosquitto/certs', str(ROOT / '.runtime/certs'))
        conf = conf.replace('persistence true', 'persistence false')
        conf = conf.replace('persistence_location /mosquitto/data/', f'persistence_location {work}/')
        if hasattr(os, 'getuid') and os.getuid() == 0:
            conf += '\nuser root\n'  # Лише native-тест у root-контейнері.
        config = work / 'mosquitto.conf'
        config.write_text(conf)
        seen = {}
        events = []
        log_path = work / 'broker.log'
        try:
            with log_path.open('w') as log:
                broker = subprocess.Popen([broker_bin, '-c', str(config)], stdout=log, stderr=log)
            def listening():
                if broker.poll() is not None:
                    raise AssertionError(log_path.read_text())
                with socket.socket() as s:
                    s.settimeout(0.2)
                    return s.connect_ex(('127.0.0.1', port)) == 0
            wait_for(listening, 10)
            os.environ.update({k: v for k, v in env.items() if k.startswith('MQTT_')})
            observer, reason = connect()
            assert not reason.is_failure
            def receive(c, u, m):
                data = m.payload.decode()
                seen[m.topic] = data
                events.append((m.topic, data, m.retain))
            observer.on_message = receive
            observer.subscribe('office/server/#', qos=1)
            simulator = subprocess.Popen([sys.executable, str(ROOT / 'simulator/devices.py')],
                                         env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run([sys.executable, str(ROOT / 'scripts/smoke.py')], env=env, check=True)
            subprocess.run([sys.executable, str(ROOT / 'scripts/security_check.py')], env=env, check=True)
            def scenario(name):
                subprocess.run([sys.executable, str(ROOT / 'simulator/devices.py'), '--scenario', name],
                               env=env, check=True, capture_output=True)
            scenario('leak')
            wait_for(lambda: json.loads(seen.get('office/server/leak/telemetry', '{}')).get('value') == 'ON')
            print('PASS сценарій leak: телеметрія ON')
            scenario('ups')
            wait_for(lambda: json.loads(seen.get('office/server/ups/telemetry', '{}')).get('battery') == 24)
            print('PASS сценарій ups: заряд 24 %')
            scenario('critical')
            wait_for(lambda: json.loads(seen.get('office/server/hot/telemetry', '{}')).get('value', 0) > 40)
            print('PASS сценарій critical: температура > 40 °C')
            observer.publish('office/server/ac/set', '{"state":"ON","mode":"MAX"}', qos=1)
            wait_for(lambda: json.loads(seen.get('office/server/ac/state', '{}')).get('mode') == 'MAX')
            print('PASS актуатор застосував JSON-команду й підтвердив MAX')
            scenario('offline-hot')
            wait_for(lambda: seen.get('office/server/hot/status') == 'offline', 25)
            late, reason = connect()
            retained = []
            late.on_message = lambda c, u, m: retained.append((m.payload.decode(), m.retain))
            try:
                late.subscribe('office/server/hot/status', qos=1)
                wait_for(lambda: ('offline', True) in retained, 5)
            finally:
                close(late)
            print('PASS справжній LWT offline після SIGKILL; retain підтверджено новою підпискою')
            scenario('normal')
            wait_for(lambda: seen.get('office/server/hot/status') == 'online')
            print('PASS відновлення пристрою online')
            print('NATIVE INTEGRATION: PASS (openHAB JVM/UI тут не запускалися)')
        except BaseException:
            print(log_path.read_text()[-6000:] if log_path.exists() else 'Брокер ще не створено', file=sys.stderr)
            raise
        finally:
            if simulator:
                simulator.terminate()
                try:
                    simulator.wait(timeout=12)
                except subprocess.TimeoutExpired:
                    simulator.kill()
                    simulator.wait(timeout=3)
            if observer:
                close(observer)
            if broker:
                broker.terminate()
                broker.wait(timeout=5)


if __name__ == '__main__':
    main()
