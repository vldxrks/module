"""Модель пристроїв без MQTT: її можна перевірити звичайним unittest."""
import math
import random

SENSORS = ("cold", "hot", "humidity", "leak", "door", "ups")
ACTUATORS = ("ac", "siren")
DEVICES = SENSORS + ACTUATORS
SCENARIOS = ("normal", "hot", "critical", "leak", "ups", "door", "combined",
             "offline-hot", "offline-cold", "silent-hot")


def initial_state(device):
    if device == "ac":
        return {"state": "OFF", "mode": "NORMAL"}
    if device == "siren":
        return {"state": "OFF", "light": "GREEN"}
    raise ValueError("Не актуатор")


def apply_command(device, current, command):
    """Часткові ON/OFF-команди ідемпотентні; невідомі поля відхиляються атомарно."""
    if not isinstance(command, dict) or not command:
        raise ValueError("Очікується непорожній JSON-об'єкт")
    allowed = {"state": {"ON", "OFF"}}
    if device == "ac":
        allowed["mode"] = {"NORMAL", "MAX"}
    elif device == "siren":
        allowed["light"] = {"GREEN", "YELLOW", "RED"}
    else:
        raise ValueError("Сенсор не приймає команд")
    for key, value in command.items():
        if key not in allowed or not isinstance(value, str) or value not in allowed[key]:
            raise ValueError("Невідоме поле або значення")
    return {**current, **command}


class Model:
    def __init__(self, device, seed=None):
        self.device = device
        self.rng = random.Random(seed)
        self.value = {"cold": 22.0, "hot": 29.0, "humidity": 45.0}.get(device, 0)

    def sample(self, scenario, elapsed):
        d = self.device
        abnormal = scenario in ("hot", "critical", "combined")
        if d in ("cold", "hot", "humidity"):
            base = {"cold": 22.0, "hot": 29.0, "humidity": 45.0}[d]
            if d == "hot" and abnormal:
                base = 37.2 if scenario == "hot" else 42.2
            amplitude = 0.35 if d != "humidity" else 1.2
            target = base + amplitude * math.sin(elapsed / 25)
            # Інерція датчика + обмежений шум; один крок кожні 2 с.
            self.value += 0.4 * (target - self.value) + self.rng.gauss(0, 0.04)
            return {"value": round(self.value, 2), "unit": "%" if d == "humidity" else "C"}
        if d == "leak":
            return {"value": "ON" if scenario in ("leak", "combined") else "OFF", "unit": "bool"}
        if d == "door":
            return {"value": "OPEN" if scenario == "door" else "CLOSED", "unit": "contact"}
        if d == "ups":
            battery = scenario in ("ups", "combined")
            return {"mode": "BATTERY" if battery else "MAINS", "battery": 24 if battery else 98, "unit": "%"}
        raise ValueError("Немає телеметрії для актуатора")
