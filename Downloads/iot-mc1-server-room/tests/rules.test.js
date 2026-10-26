'use strict';
// Виконує справжній server.js із підставленою шиною Items (не замінює openHAB).
const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
test('four registered rules use shared output arbitration and update real Item names', () => {
  const project = path.resolve(__dirname, '..');
  const names = [...fs.readFileSync(path.join(project, 'openhab/conf/items/server.items'), 'utf8')
    .matchAll(/^(?:Group|Number|Switch|Contact|String)\s+(\w+)/gm)].map(m => m[1]);
  const states = Object.fromEntries(names.map(n => [n, 'NULL']));
  Object.assign(states, { Hot_Temperature: '29', UPS_Mode: 'MAINS', UPS_Battery: '98', Leak: 'OFF' });
  for (const n of names.filter(n => n.endsWith('_Status'))) states[n] = 'online';
  const commands = [];
  const rules = [];
  const api = {
    items: { getItem(name) {
      assert.ok(name in states, 'Невідомий Item ' + name);
      return { get state() { return states[name]; },
        postUpdate(value) { states[name] = value; },
        sendCommand(value) { commands.push([name, value]); states[name] = value; } };
    } },
    rules: { JSRule: rule => rules.push(rule) },
    triggers: new Proxy({}, { get: (_, name) => (...args) => ({ name, args }) })
  };
  const context = { require: name => name === 'openhab' ? api :
    require(path.join(project, 'openhab/conf/automation/js/node_modules', name)), Date,
    console: { info() {} } };
  vm.runInNewContext(fs.readFileSync(path.join(project, 'openhab/conf/automation/js/server.js'), 'utf8'), context);
  assert.equal(rules.length, 4);
  states.Hot_Temperature = '42';
  states.Leak = 'ON';
  rules[0].execute({ itemName: 'Hot_Temperature' });
  assert.equal(states.Siren_Power, 'ON');
  assert.equal(states.AC_Mode, 'MAX');
  states.Hot_Temperature = '29';
  rules[0].execute({ itemName: 'Hot_Temperature' });
  assert.equal(states.Siren_Power, 'ON');
  states.Leak = 'OFF';
  rules[1].execute({ itemName: 'Leak' });
  assert.equal(states.Siren_Power, 'OFF');
  assert.ok(commands.length > 0);
});
