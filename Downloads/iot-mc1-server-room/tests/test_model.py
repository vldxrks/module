import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'simulator'))
from model import Model, SENSORS, apply_command, initial_state  # noqa: E402


class ModelTests(unittest.TestCase):
    def test_normal_ranges_and_smoothness(self):
        for device, bounds in [('cold', (20, 24)), ('hot', (27, 31)), ('humidity', (41, 49))]:
            model = Model(device, seed=7)
            values = [model.sample('normal', t)['value'] for t in range(0, 300, 2)]
            self.assertTrue(all(bounds[0] < v < bounds[1] for v in values))
            self.assertLess(max(abs(a-b) for a, b in zip(values, values[1:])), 1)

    def test_heat_scenarios_cross_real_thresholds(self):
        for scenario, minimum, maximum in [('hot', 35, 40), ('critical', 40, 45)]:
            model = Model('hot', seed=8)
            for t in range(0, 60, 2):
                value = model.sample(scenario, t)['value']
            self.assertGreater(value, minimum)
            self.assertLess(value, maximum)

    def test_all_sensor_payloads_are_json(self):
        for name in SENSORS:
            self.assertIsInstance(json.loads(json.dumps(Model(name).sample('normal', 0))), dict)

    def test_leak_ups_door_and_reset(self):
        self.assertEqual(Model('leak').sample('leak', 0)['value'], 'ON')
        self.assertEqual(Model('leak').sample('normal', 0)['value'], 'OFF')
        self.assertEqual(Model('door').sample('door', 0)['value'], 'OPEN')
        ups = Model('ups').sample('ups', 0)
        self.assertEqual(ups['mode'], 'BATTERY')
        self.assertLess(ups['battery'], 30)
        self.assertEqual(Model('ups').sample('normal', 0)['mode'], 'MAINS')

    def test_duplicate_commands_are_idempotent_and_partial(self):
        original = initial_state('ac')
        once = apply_command('ac', original, {'mode': 'MAX'})
        self.assertEqual(apply_command('ac', once, {'mode': 'MAX'}), once)
        self.assertEqual(once['state'], 'OFF')
        self.assertEqual(original, {'state': 'OFF', 'mode': 'NORMAL'})

    def test_invalid_commands_do_not_change_state(self):
        original = initial_state('siren')
        for command in [None, [], {}, {'state': True}, {'light': 'BLUE'},
                        {'state': 'ON', 'extra': 'x'}, {'state': ['ON']}]:
            with self.assertRaises(ValueError):
                apply_command('siren', original, command)
            self.assertEqual(original, {'state': 'OFF', 'light': 'GREEN'})


if __name__ == '__main__':
    unittest.main()
