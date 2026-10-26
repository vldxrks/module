# Фактична перевірка — 26.10.2026

## Виконано

| Перевірка | Результат | Що підтверджує |
|---|---|---|
| unittest, Python 3.12.14 | 6/6 PASS | Діапазони/плавність, сценарії, JSON, валідація й ідемпотентність команд |
| Node.js test runner | 8/8 PASS | Пороги, гістерезис, протікання, ДБЖ, відсутність/відновлення даних, одночасні аварії |
| Виконання справжнього server.js із тестовими Items | PASS, входить до 8 Node tests | Реєстрація 4 JSRule, відповідність назв Items, спільне керування сиреною |
| Статична перевірка конфігів | PASS | Compose YAML, 19 унікальних MQTT-каналів, усі посилання Items/Sitemap, JSON command format |
| compileall та sh -n | PASS | Синтаксис усіх Python-файлів і сертифікатного shell-скрипту |
| openssl verify + hostname | PASS | CA-підпис і DNS mosquitto/localhost у SAN |
| Native Mosquitto 2.0.21 + paho-mqtt 2.1.0 | PASS | Реальні TLS MQTT-сеанси восьми пристроїв і всі 6 потоків телеметрії |
| Негативна автентифікація | PASS | CONNECT без пароля → Not authorized |
| Plaintext / порт 1883 | PASS | Без TLS немає MQTT CONNACK, 1883 закритий |
| Чужий топік від cold | PASS | MQTT 5 PUBACK Not authorized при записі в ac/set |
| leak / ups / critical | PASS | Телеметрія змінюється, температура реально перетинає 40 °C |
| Команда актуатору | PASS | ac отримує JSON і повертає state із mode MAX |
| SIGKILL і Last Will | PASS | Брокер сам публікує offline; нова підписка одержує retained offline |
| Відновлення | PASS | Після normal hot знову публікує online |

Для native-тесту брокер і mosquitto_passwd зібрані з офіційного вихідного архіву
Mosquitto 2.0.21. Дистрибутив/скомпільовані сторонні програми та тестові секрети
не включені до ZIP: вони не потрібні Docker-стенду. У native-тесті замінено лише
шляхи, локальний порт, вимкнено disk persistence та збережено поточного користувача;
правила ACL, TLS і Python-код пристроїв — ті самі, що в проєкті.

## Не запускалося в цьому середовищі

Docker Engine/Compose тут відсутні, тому **не виконувалися** `docker compose up`,
bootstrap із Docker helper-контейнерами, складання openHAB-образу, встановлення add-ons,
реальна JVM/GraalJS, відображення BasicUI та RRD4J-графіка. Node-тести не є перевіркою
роботи openHAB runtime. Ці частини звірено зі структурою офіційної документації гілки 4.3,
але їх потрібно перевірити після запуску на комп'ютері студента.

Немає заяви про створене відео, живий захист, справжні скріншоти UI або GitHub-коміти.
У README та AI_USAGE позначені персональні матеріали, які потрібно додати перед здачею.

## Повторити перевірку

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --test tests/*.test.js
python3 scripts/bootstrap.py
docker compose up -d
docker compose run --rm tools scripts/smoke.py
docker compose run --rm tools scripts/security_check.py
```

Native-варіант, якщо Mosquitto встановлений на хості:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r simulator/requirements.txt
python3 tests/native_integration.py
```

Тест автоматично створює тимчасові облікові дані, використовує вільний локальний порт,
прибирає процеси й видаляє тестовий каталог. Публічні CA/сертифікати й ключі залишаються
лише у виключеному з git `.runtime`, так само як після штатної генерації.
