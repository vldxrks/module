'use strict';
const { items, rules, triggers } = require('openhab');
const { Monitor } = require('server-policy');
const monitor = new Monitor(Date.now());

function state(name) { return items.getItem(name).state; }
function number(name) {
  const raw = state(name);
  return raw === 'NULL' || raw === 'UNDEF' ? NaN : Number(raw);
}
function update(name, value) {
  if (state(name) !== String(value)) items.getItem(name).postUpdate(String(value));
}
function command(name, value) {
  // autoupdate=false: порівнюємо зі state від реального актуатора.
  if (state(name) !== value) items.getItem(name).sendCommand(value);
}

function reconcile(event) {
  const now = Date.now();
  const source = { Cold_Temperature: 'cold', Hot_Temperature: 'hot',
    Humidity: 'humidity', Leak: 'leak', Door: 'door', UPS_Battery: 'ups', UPS_Mode: 'ups' };
  if (event && source[event.itemName]) monitor.seen(source[event.itemName], now);
  const result = monitor.evaluate({
    hot: number('Hot_Temperature'), coldStatus: state('Cold_Status'),
    hotStatus: state('Hot_Status'), humidityStatus: state('Humidity_Status'),
    leakStatus: state('Leak_Status'), doorStatus: state('Door_Status'),
    upsStatus: state('UPS_Status'), leak: state('Leak'),
    upsMode: state('UPS_Mode'), battery: number('UPS_Battery')
  }, now);
  update('Heat_Warning', result.heat ? 'ON' : 'OFF');
  update('Critical_Alarm', result.critical ? 'ON' : 'OFF');
  update('Water_Alarm', result.water ? 'ON' : 'OFF');
  update('UPS_Alarm', result.ups ? 'ON' : 'OFF');
  update('Missing_Alarm', result.missing.length ? 'ON' : 'OFF');
  update('System_Alarm', result.alarm ? 'ON' : 'OFF');
  if (state('Alarm_Message') !== result.message) {
    console.info(result.message);
    update('Alarm_Message', result.message);
  }
  // Єдине місце керування сиреною: жодне правило не скасовує чужу тривогу.
  command('Siren_Power', result.siren);
  command('Siren_Light', result.light);
  if (result.ac) {
    command('AC_Mode', result.ac.mode);
    command('AC_Power', result.ac.state);
  }
}

rules.JSRule({
  id: 'server-temperature', name: '1. Перегрів гарячого коридору',
  description: '>35: MAX; >40: критична тривога; <33: скидання охолодження',
  triggers: [triggers.ItemStateUpdateTrigger('Hot_Temperature')],
  execute: reconcile
});
rules.JSRule({
  id: 'server-leak', name: '2. Протікання за будь-якого стану',
  triggers: [triggers.ItemStateUpdateTrigger('Leak')],
  execute: reconcile
});
rules.JSRule({
  id: 'server-ups', name: '3. ДБЖ: батарея менше 30 %',
  triggers: [triggers.ItemStateUpdateTrigger('UPS_Mode'),
             triggers.ItemStateUpdateTrigger('UPS_Battery')],
  execute: reconcile
});
rules.JSRule({
  id: 'server-watchdog', name: 'Контроль Last Will і свіжості даних',
  description: 'offline понад 60 с або немає вимірів понад 60 с: Немає даних',
  triggers: [triggers.ItemStateUpdateTrigger('Cold_Temperature'),
             triggers.ItemStateUpdateTrigger('Cold_Status'),
             triggers.ItemStateUpdateTrigger('Hot_Status'),
             triggers.ItemStateUpdateTrigger('Humidity'),
             triggers.ItemStateUpdateTrigger('Humidity_Status'),
             triggers.ItemStateUpdateTrigger('Leak_Status'),
             triggers.ItemStateUpdateTrigger('Door'),
             triggers.ItemStateUpdateTrigger('Door_Status'),
             triggers.ItemStateUpdateTrigger('UPS_Status'),
             triggers.SystemStartlevelTrigger(100),
             triggers.GenericCronTrigger('0/5 * * * * ?')],
  execute: reconcile
});
