'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const { Monitor } = require('../openhab/conf/automation/js/node_modules/server-policy');
function normal() {
  return { hot: 29, leak: 'OFF', upsMode: 'MAINS', battery: 98,
    coldStatus: 'online', hotStatus: 'online', humidityStatus: 'online',
    leakStatus: 'online', doorStatus: 'online', upsStatus: 'online' };
}
function monitor() {
  const m = new Monitor(0);
  for (const name of m.sensors) m.seen(name, 0);
  return m;
}

test('normal, strict 35/40 boundaries and AC hysteresis', () => {
  const m = monitor();
  const input = normal();
  assert.equal(m.evaluate(input, 0).alarm, false);
  assert.equal(m.evaluate({ ...input, hot: 35 }, 0).heat, false);
  let result = m.evaluate({ ...input, hot: 35.01 }, 0);
  assert.equal(result.light, 'YELLOW');
  assert.deepEqual(result.ac, { state: 'ON', mode: 'MAX' });
  assert.equal(m.evaluate({ ...input, hot: 40 }, 0).critical, false);
  assert.equal(m.evaluate({ ...input, hot: 40.01 }, 0).siren, 'ON');
  assert.equal(m.evaluate({ ...input, hot: 34 }, 0).ac, null);
  assert.equal(m.evaluate(input, 0).ac.state, 'OFF');
});
test('leak independently activates siren in normal room', () => {
  const r = monitor().evaluate({ ...normal(), leak: 'ON' }, 0);
  assert.equal(r.siren, 'ON');
  assert.match(r.message, /ПРОТІКАННЯ/);
});
test('UPS requires both BATTERY and strictly less than 30', () => {
  const m = monitor();
  assert.equal(m.evaluate({ ...normal(), battery: 20 }, 0).ups, false);
  assert.equal(m.evaluate({ ...normal(), upsMode: 'BATTERY', battery: 30 }, 0).ups, false);
  const r = m.evaluate({ ...normal(), upsMode: 'BATTERY', battery: 29 }, 0);
  assert.equal(r.ups, true);
  assert.match(r.message, /Підготувати сервери/);
});
test('clearing heat cannot silence an ongoing leak/UPS alarm', () => {
  const m = monitor();
  m.evaluate({ ...normal(), hot: 42, leak: 'ON' }, 0);
  assert.equal(m.evaluate({ ...normal(), hot: 29, leak: 'ON' }, 1).siren, 'ON');
  assert.equal(m.evaluate({ ...normal(), upsMode: 'BATTERY', battery: 24 }, 2).siren, 'ON');
  assert.equal(m.evaluate(normal(), 3).siren, 'OFF');
});
test('offline more than 60 seconds even with a recent stale value', () => {
  const m = monitor();
  const input = { ...normal(), hotStatus: 'offline' };
  m.evaluate(input, 0);
  for (const name of m.sensors) m.seen(name, 60000);
  assert.equal(m.evaluate(input, 60000).missing.length, 0);
  assert.deepEqual(m.evaluate(input, 60001).missing, ['hot']);
  m.seen('hot', 61000);
  assert.equal(m.evaluate(normal(), 61000).alarm, false);
});
test('online without new telemetry still alarms; all six sensors covered', () => {
  const m = monitor();
  for (const name of m.sensors.filter(x => x !== 'humidity')) m.seen(name, 61000);
  assert.deepEqual(m.evaluate(normal(), 61000).missing, ['humidity']);
  m.seen('humidity', 61001);
  assert.equal(m.evaluate(normal(), 61001).alarm, false);
});
test('NULL-like hot values never become a false temperature reading', () => {
  const r = monitor().evaluate({ ...normal(), hot: NaN, battery: NaN }, 0);
  assert.equal(r.heat, false);
  assert.equal(r.ac, null);
});
