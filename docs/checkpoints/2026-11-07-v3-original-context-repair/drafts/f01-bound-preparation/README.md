# F01 — проверенный preparatory delta

Патч относится к частному `package.py` существующего bound-tester рецепта; это не установленный код Friday и не отдельный grant. Исходный preparatory source `909bb74cc50fc22aed2b3af4536bb3545f6fdf746b4d25f5d305176440432a4f` сохранён в API-repair `package.py.before`, конечный SHA `86c86207e60b132a952050e6645cb754afe38c3b005a9ea15cd2fb52e8b9ba04`.

До создания run v42 custody reader получает обязательный no-op guard; actual sender сохраняет `self.guard(run)`. Authority-reference нормализуется к исходному порядку `path/bytes/sha256`, поэтому точный полный bound source восстанавливается после canonical JSON roundtrip. Сравнение полных байтов не ослаблено.

Первый отказ был до admission. Второй readback-отказ случился после выпуска R101/binding, до dispatch; существующие authority/binding/tester сохранены побайтно. Повторных issue/bind, смены run-id или сброса часов не было. После исправления выполнен тот же ещё не начатый ordinary MD read. API63 + прежние107 controls; ordering87 с independent review; это source-проверки, не число V3-кейсов.

Actual user outcome и границы приёмки: [MD read proof](../../evidence/astra-20261111/f01-md-v02-ordinary-read.json). Private raw source/input/oracles, canonical runs/downloads/closures не публикуются.
