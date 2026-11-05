# AA-001: цепочка worker map и холодный старт Telegram

Поправка к `reports/002-config-provenance.md`. Файлы `reports/001-breadth.md`, `reports/001-coverage.csv` и `reports/002-config-provenance.md` не переписывались.

Ревьюер прочитал пакет 002 и расшифровал его. Целостность подтверждена. Разбор конфигурации принят. Ограничение сохраняется: контекст конкретного живого обращения не наблюдался. Contextvar внутри процесса этим проходом тоже не наблюдался.

Срез публичного git для задания остаётся `26217103b514a9523040868af2ed6933d031ceb7`. Наблюдение файлов и кода потребителя: 2026-11-05T14:41:35Z. Процессы не перезапускались. Воркеры не включались. Продуктовые `load_config`, `load_config_readonly` и `check_runtime` не вызывались. Telegram и Bot API не вызывались. `state.db` не открывалась.

## Вывод о зависимости от истории тестера снят

Отчёт 002 оставил фразу: полный worker map есть только в конфиге одного обслуживаемого профиля, и это зависимость конфигурации этого профиля, а не import продукта; байты pin-ов с их sha не сверялись. Эта фраза больше не читается как зависимость продукта от истории тестера. Точная цепочка ниже заканчивается на продуктовом конфиге и продуктовом plugin.

### Map

Живой узел `plugins.entries.friday_rework.settings.runtime` со значением `enabled: true` и map `workers` есть только в `config.yaml` профиля, имя каталога которого содержит числовой идентификатор учётной записи. Строка 629: `enabled: true`, у `workers.dsh` и `workers.a0` тоже `enabled: true`. Строка 24126: `worker_requirements` ровно `['dsh', 'a0']`. Строка 24096 — вложенный pin `a0.runtime`, не флаг допуска. Подстановки `${...}` в этом узле нет.

Корневой файл, строка 25624, и `profiles/dest_telegram/config.yaml`, строка 580, остаются ровно `{enabled: false}`. Для них `host.handle` возвращает `worker_not_admitted` до claim. Это разделение профилей из отчёта 002 сохраняется.

### Файл, который читает потребитель

`collect_directory_manifests` сканирует bundled plugins, затем `HERMES_HOME/plugins`. Поздний источник с тем же именем побеждает. Каталог user plugin `plugins/friday_rework` в домашнем каталоге установки есть. Его `plugin.yaml`: `name: friday_rework`, `version: 0.1.0`, tool `friday_work`. Копии этого plugin в workspace известного окружения нет. `prepared_friday_plugin` добавляется только если scan не нашёл `friday_rework`. Для этого дома он не является путём загрузки.

Установленная копия и git checkout — разные файлы. `host.py` и `host_runtime.py` различаются. `__init__.py` побайтово совпадает, регистрация `friday_work` указывает на `host.handle` в обеих копиях. Потребитель обнаруженного plugin — установленная копия, не checkout.

### Потребитель

В установленной копии `host.handle` делает `configured = self.ctx.get_config("runtime")`. Если это не dict или `enabled is not True`, ответ `worker_not_admitted`. Иначе `check_runtime(select_runtime(configured, brief.worker), self.store)`. `select_runtime` и `check_runtime` — функции `host_runtime.py` той же копии. Отдельного процесса воркера нет. `get_config("runtime")` по-прежнему читает `plugins.entries.friday_rework.settings.runtime` дома, который выбран context-local override, иначе процессным `HERMES_HOME`. Какой дом был выбран в конкретном живом turn, не наблюдался.

### Кто записывает такую форму

В установленной копии `onboarding.qualify_workers` после `check_runtime` и `deployment_health` записывает `settings.runtime = {enabled: true, workers: runtimes}`. При attaching туда же пишется `worker_requirements = ['dsh', 'a0']`, затем файл пишется через `atomic_config_write`. Более ранний путь публикации нового профиля может записать один `worker_requirements`, пока профиль ещё не завершён. Этот ранний путь enabled map не пишет. Живая форма профиля с числовым именем совпадает с записью `qualify_workers`. Трасса вызова, которая доказала бы, что именно этот запуск записал текущий файл, не снималась.

У `dest_telegram` есть маркеры onboarding, `workers/attachment.json` и оба `runtime-input.json`. Квитанций runtime и каталога `workers/qualification` там нет, а `settings.runtime` остаётся `{enabled: false}`. У профиля с числовым именем есть маркеры, attachment, обе квитанции, оба `runtime-input.json` и каталог `workers/qualification`. Тела onboarding JSON не читались.

### Где цепочка обрывается

Маркеров `bot_tester`, `candidate-r15`, `engineering_regression_module` и `regression_attempt` нет в `host.py`, `host_runtime.py`, `__init__.py` и `onboarding.py` установленной копии. Контрольные pin-ы существуют и совпадают с объявленным sha256: у dsh это `bin.js`, `node`, `dsh-local.json` и `runtime-receipt.json`; у a0 это unit `friday-rework-docker.service`, `docker`, `launch.py`, `a0-policy.nft` и `a0_runtime.py`. Пути лежат в дереве runtime. Текст закреплённых `a0_runtime.py` и `launch.py` тех маркеров не содержит. Эти два файла не совпадают ни с одноимённым скриптом checkout, ни со скриптом workspace. Список `dsh.native_files` содержит 11687 путей. В путях маркеров тестера нет. Расширения в основном `.map`, `.js`, `.ts`. Байты этих 11687 файлов заново не хешировались.

Цепочка: map в файле одного профиля, файл установленного user plugin, потребитель `friday_work` → `host.handle` → `select_runtime` → `check_runtime`. До истории тестера она не доходит.

## Сохранённый `enabled: true` сейчас не проходит проверку загружаемого plugin

Это сравнение хешей на диске. `check_runtime` не вызывался: он читает все native pin-ы и, потому что каталог `workers/qualification` существует, вызывает `deployment_health`.

Обе квитанции имеют `ready: true`. Это сохранённое поле, не свежий допуск. Digest тот, который использует продукт: sha256 от `json.dumps(..., sort_keys=True, ensure_ascii=False, allow_nan=False)`.

DSH, схема `friday-rework.dsh-runtime.v1`, два evidence:

- `runtime_sha256` квитанции не совпадает с digest тела конфига без ключа `runtime_receipt`.
- Тело `runtime` в `workers/dsh/runtime-input.json` совпадает с этим телом конфига и не совпадает с квитанцией. Pin-ов 11694 и в конфиге, и во входе. Набор sha одинаковый, скалярных отличий нет.
- Evidence `runtime-input.json` не совпадает с объявленным sha. Evidence `observation.json` совпадает.
- `adapter_sha256` совпадает с `adapters/dsh.py` checkout и не совпадает с `adapters/dsh.py` загружаемого plugin. `check_runtime` хеширует sibling загруженного модуля. Против обнаруженного plugin этот предикат не проходит.
- `PinnedFile.read` загружаемой копии при несовпадении sha поднимает `AdapterError("host_input_changed")`. Для evidence `runtime-input.json` это уже так.
- Предикат web не закрывался. `worker_web.py` загружаемого plugin совпадает с pin квитанции. Какой `tools.web_profile` импортирует процесс и какой файл читает закреплённый `research_policy`, к живому импорту не привязаны. Для отказа dsh этот предикат не нужен: не сходятся `runtime_sha256`, evidence `runtime-input.json` и `adapter_sha256`.

A0, схема `friday-rework.a0-runtime.v2`, два evidence:

- `runtime_sha256` совпадает с телом конфига без `runtime_receipt`.
- Тело `runtime` в `workers/a0/runtime-input.json` не совпадает ни с квитанцией, ни с конфигом. Evidence `runtime-input.json` не совпадает с объявленным sha. Evidence `proof.json` совпадает.
- `source_pins` против загружаемого plugin: совпали `host_record.py`, `adapters/a0.py`, `adapters/a0_native.py`, `adapters/a0_config.py`, `adapters/a0_profile.py`, `adapters/a0_web.py`. Не совпали `host.py`, `host_runtime.py`, `associations.py`. Checkout совпал только по `adapters/a0.py` и `adapters/a0_profile.py`. Workspace-копии plugin нет. `check_runtime` сравнивает pin-ы с sibling загруженного `host_runtime.py`. Против обнаруженного plugin предикат `source_pins` не проходит.

Итог статической проверки: записанный допуск не является текущим прохождением `check_runtime` для plugin, который discovery загрузит из дома установки. Это не product PASS и не наблюдение живого turn.

## Фактическая политика накопившихся Telegram-сообщений

Кодовый default адаптера — сброс. Живой файл — сохранение. Действующая политика холодного старта этой установки — сохранить очередь Bot API и отдать её адаптеру.

В корневом `config.yaml`, строка 609, `platforms.telegram.extra.drop_pending_on_cold_boot` — boolean `false`. Секция включена. В `extra` только этот ключ и `unauthorized_dm_behavior: pair`. `webhook_url` и `webhook_secret` нет. В `profiles/dest_telegram/config.yaml` и в конфиге профиля с числовым именем верхнего ключа `platforms` нет, строки `drop_pending_on_cold_boot` нет. Два `gateway.profile_routes` корневого файла ведут на platform `telegram`, оба enabled, у обоих `bot_profile` — строка `default`, не null. Идентификаторы пользователей не публикуются.

Конструктор адаптера ставит `_drop_pending_on_cold_boot` через `_coerce_bool_extra("drop_pending_on_cold_boot", True)`. Явный boolean `false` побеждает default. Комментарий `run_adapters` про сброс на холодном старте описывает исторический default аргумента `is_reconnect`, не значение живого файла.

Первичный connect: `run_startup` вызывает `_connect_initial_adapter_with_timeout`, тот вызывает `_connect_adapter_with_timeout` с `initial=True` и без `is_reconnect`. Аргумент остаётся `False`. `connect(is_reconnect=False)` доходит до `_start_polling_mode`. `_cold_boot_drop_pending(is_reconnect=False)` возвращает флаг файла, то есть `False`. `start_polling` получает `drop_pending_updates=False`: очередь просят доставить, не отбросить. `delete_webhook` в этом пути тоже вызывается с `drop_pending_updates=False`.

Повтор watcher после холодного старта передаёт `is_reconnect=True`. `_cold_boot_drop_pending` тогда возвращает `False` независимо от флага. И успешный холодный путь, и последующий повтор сохраняют очередь. Таймаут или неуспех первичного connect сам по себе сброс не включает.

Если флаг был бы `true`, конфликт 409 повторял бы polling с `drop_pending_updates=True` и тем самым сбрасывал очередь. При живом `false` конфликт сразу фатален: код пишет, что остановка сделана, чтобы сохранить pending updates, и что retry и сброс очереди не пытались. Этот текст — ветка адаптера, не отдельно снятый живой инцидент.

`Application.builder()` в `connect` задаёт token, класс application, request и `concurrent_updates`. Аргумента Persistence в этой сборке нет. Локального файла offset этот проход не открывал. `state.db` не открывалась. Offset `getUpdates` для этой сборки — серверная сессия Telegram, не файл plugin.

Отдельный слой, не offset: завершённые update id пишутся в `telegram_update_receipts_<bot>.json` под Hermes home адаптера. Каталог берётся из `get_hermes_home()` в конструкторе. В памяти потолок 4096. С диска поднимаются только метки новее 24 часов. Комментарий продукта говорит, что Bot API держит неподтверждённый update не дольше 24 часов. Это утверждение кода, не отдельная проверка Bot API. Такой файл не отбрасывает ещё не виденный backlog. Он подавляет повторную доставку уже завершённых id.

На диске ровно один такой файл, в корневом доме: 1127 байт, mode 0664, ключ `update_ids`, 34 идентификатора. Самому старому 65.291 часа, самому новому 41.336 часа. Все старше окна 24 часов, поэтому холодный старт сейчас не засеял бы из этого файла ни одного id. В двух named profile таких файлов нет. Идентификатор бота и сами update id не публикуются.

`configuration_contract` обычного gateway требует на принимающем конфиге одновременно корневой `settings.runtime == {enabled: false}` и `drop_pending_on_cold_boot is False`. Живой корневой файл этому boolean соответствует. Сама функция этим проходом не исполнялась.

Предикат общего бота-сателлита требует маршрут с `bot_profile is None`. У обоих живых маршрутов `bot_profile` — строка `default`, поэтому этот предикат их сателлитами не считает. Живая карта адаптеров процесса не читалась. Какой дом был текущим в момент конструктора адаптера, не наблюдался. Файловая политика единственной секции Telegram — сохранение очереди.

## Что этим проходом не закрыто

Обоснованность 19 скаляров `custom:friday-local` вне шаблонов не оценивалась. `state.db` не открывалась. Побайтовая пересборка 180 слоёв не делалась. Восстановление не прогонялось. План реализации для Астры не написан. 11687 `native_files` классифицированы по пути и не перехешированы. Поиск одного дерева, в котором совпали бы все девять `source_pins` a0, отдельным результатом не оформлялся: для снятия тестерной зависимости он не потребовался.
