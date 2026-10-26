# Справжні скріншоти перед здачею

Скріншоти живого openHAB не додані: JVM/UI тут не запускались. Вони мають відображати
ваш запуск, а не макет. Зробіть 3–5 кадрів; рекомендовано ці п'ять:

1. `01-normal.png` — усі сенсори, online-статуси та актуатори у Sitemap.
2. `02-temperature.png` — >40 °C, AC MAX, червона індикація й критичне повідомлення.
3. `03-water-ups.png` — combined із протіканням та повідомленням про ДБЖ.
4. `04-offline.png` — retained offline і «Немає даних» після >60 с.
5. `05-security-chart.png` — графік та успішні негативні security checks у терміналі.

Після збереження вставте ці файли в README через Markdown `![Опис](docs/screenshots/01-normal.png)`.
Для додавання у git зніміть правило `docs/screenshots/*.png` із .gitignore або виконайте
`git add -f docs/screenshots/*.png` після перевірки, що кадри не містять секретів.
