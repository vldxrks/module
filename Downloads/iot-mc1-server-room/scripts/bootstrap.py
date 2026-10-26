#!/usr/bin/env python3
"""Одна підготовча команда: секрети, CA, password_file і відтворюваний openHAB conf."""
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "simulator"))
from model import DEVICES  # noqa: E402


def read_env(path):
    result = {}
    if path.exists():
        for line in path.read_text().splitlines():
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                result[key] = value
    return result


def main():
    os.chdir(ROOT)
    for executable in ("docker", "openssl", "sh"):
        if not shutil.which(executable):
            raise SystemExit(f"Потрібен {executable}. Див. README.md.")
    subprocess.run(["docker", "compose", "version"], check=True)
    os.umask(0o077)
    runtime = ROOT / ".runtime"
    runtime.mkdir(exist_ok=True, mode=0o700)
    for name in ("mosquitto", "control"):
        (runtime / name).mkdir(exist_ok=True)
    users = (*DEVICES, "openhab", "admin")
    env = read_env(ROOT / ".env")
    for user in users:
        key = f"MQTT_PASSWORD_{user.upper()}"
        env.setdefault(key, secrets.token_hex(24))
        # Значення вставляються в .things та passwd: дозволено лише hex.
        if len(env[key]) < 32 or any(ch not in "0123456789abcdef" for ch in env[key]):
            raise SystemExit(f"{key}: очікується не менше 32 hex-символів.")
    common = {"MQTT_HOST": "mosquitto", "MQTT_PORT": "8883", "MQTT_CA": "/certs/ca.crt"}
    env.update(common)
    env["TZ"] = "Europe/Kyiv"

    def write_env(path, selected):
        path.write_text("".join(f"{key}={value}\n" for key, value in selected.items()))
        path.chmod(0o600)

    write_env(ROOT / ".env", env)
    write_env(runtime / "simulator.env", {**common, **{
        f"MQTT_PASSWORD_{u.upper()}": env[f"MQTT_PASSWORD_{u.upper()}"] for u in DEVICES}})
    write_env(runtime / "tools.env", {**common, **{
        f"MQTT_PASSWORD_{u.upper()}": env[f"MQTT_PASSWORD_{u.upper()}"] for u in ("admin", "cold")}})
    passwd = runtime / "mosquitto/passwd"
    passwd.unlink(missing_ok=True)  # Попередній файл може належати UID 1883.
    passwd.write_text("".join(f"{u}:{env[f'MQTT_PASSWORD_{u.upper()}']}\n" for u in users))
    try:
        subprocess.run(["docker", "run", "--rm", "--user", "0:0", "--entrypoint",
                        "mosquitto_passwd", "-v", f"{runtime / 'mosquitto'}:/work",
                        "eclipse-mosquitto:2.0.21", "-U", "/work/passwd"], check=True)
    except BaseException:
        passwd.unlink(missing_ok=True)  # Не залишати незахешований password_file.
        raise
    subprocess.run(["sh", "certs/generate.sh"], check=True)
    conf = runtime / "openhab-conf"
    if conf.exists():
        # openHAB entrypoint може змінити власника bind mount на UID 9001.
        host_uid = os.getuid() if hasattr(os, "getuid") else 1000
        host_gid = os.getgid() if hasattr(os, "getgid") else 1000
        subprocess.run(["docker", "run", "--rm", "--user", "0:0", "--entrypoint", "sh",
                        "-v", f"{conf}:/work", "eclipse-mosquitto:2.0.21", "-ec",
                        f"chown -R {host_uid}:{host_gid} /work"], check=True)
    shutil.copytree(ROOT / "openhab/conf", conf, dirs_exist_ok=True)
    for directory, dirs, files in os.walk(conf):
        Path(directory).chmod(0o755)
        for name in files:
            (Path(directory) / name).chmod(0o644)
    template = conf / "things/server.things.template"
    (conf / "things/server.things").write_text(template.read_text().replace(
        "__OPENHAB_PASSWORD__", env["MQTT_PASSWORD_OPENHAB"]))
    (conf / "things/server.things").chmod(0o644)
    template.unlink()
    if not (runtime / "control/scenario.json").exists():
        (runtime / "control/scenario.json").write_text('{"scenario":"normal"}\n')
    # Контейнер бачить лише змонтовані підкаталоги, а не .runtime/private/ca.key.
    subprocess.run(["docker", "run", "--rm", "--user", "0:0", "--entrypoint", "sh",
                    "-v", f"{runtime}:/work", "eclipse-mosquitto:2.0.21", "-ec",
                    "chown 1883:1883 /work/mosquitto/passwd /work/certs/server.key; "
                    "chmod 640 /work/mosquitto/passwd /work/certs/server.key; "
                    "chmod 755 /work/certs"], check=True)
    print("Підготовку завершено. Запуск: docker compose up -d")


if __name__ == "__main__":
    main()
