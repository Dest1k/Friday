# AA-001: происхождение конфигурации

Срез публичного git для задания остаётся `26217103b514a9523040868af2ed6933d031ceb7`. Этот отчёт его не заменяет. Наблюдение живых файлов и процессов: 2026-11-05T13:43:23Z. Процессы не останавливались, воркеры не включались, авторизация не менялась, `state.db` не открывалась, продуктовый `load_config` не вызывался: он умеет писать резервную копию.

Поправка к карте ширины. Числа строк, файлов и слоёв остаются наблюдением размера. Сами по себе они не доказывают, что сложность избыточна. Фраза карты ширины про «сложность не локальна для тестера» этой поправкой ограничена, файл `reports/001-breadth.md` не переписывался.

## Какой файл читает процесс

Оба живых процесса держат один и тот же `HERMES_HOME`: домашний каталог установки, не каталог named profile. Gateway запущен как supervised `gateway run` без флага профиля, поэтому sticky `active_profile` он не читает; такого файла нет. Dashboard запущен как `-p default` на непетлевом адресе. Для `default` резолвер профиля возвращает тот же домашний каталог. Значит процессный `get_config_path()` у обоих — корневой `config.yaml` этой установки.

`ctx.get_config("runtime")` не читает верхний ключ `runtime`. Он читает `plugins.entries.<plugin_id>.settings.runtime`, а при отсутствии ключа в `settings` — старое поддерево `config`. Идентификатор plugin — `friday_rework`. Вызов идёт в `load_config_readonly()`: разбор файла дома, который сейчас выбран context-local override, иначе процессным `HERMES_HOME`. Отдельного процесса воркера нет. Воркерный путь — это `host.handle` в том процессе gateway, в области того профиля, которую turn скопировал через `set_hermes_home_override`.

Текущий contextvar внутри процесса снаружи не наблюдался. Наблюдены дом процесса, argv, запись `served_profiles` и байты файлов.

## Парсер и повторные ключи

Боевой разбор — `hermes_yaml.safe_load` (ruamel 0.18.16, YAML 1.1). Повтор ключа на одном уровне даёт `DuplicateKeyError`. Второй документ тем же вызовом не принимается. Все три живых `config.yaml` и пять корневых `backups/config/config.yaml.good.*` этим парсером приняты как один mapping. Маркеров `---` в них нет. Реальных повторных ключей на одном уровне нет.

Повторы `runtime:` — разные пути:

- корневой файл, строка 25624: живой `plugins.entries.friday_rework.settings.runtime`;
- тот же файл, строки 1234 и 25441: тот же ключ внутри двух шаблонов onboarding, не второй документ и не второй верхний `plugins`;
- тот же файл, строка 1432: вложенный pin `a0.runtime` с `path` и `sha256`, это не флаг допуска воркера;
- `profiles/dest_telegram/config.yaml`, строка 580: собственный живой `settings.runtime`;
- третий профиль, строка 629: собственный живой `settings.runtime`; строка 24096 там снова pin `a0.runtime`.

Корневой `config.yaml` побайтово совпадает с `backups/config/config.yaml.good.20261028-053647`. Более старые good-копии совпадают с каталогами preparation, не с текущим файлом. Это снимки, не действующий документ. `/etc/hermes` нет. `HERMES_MANAGED_DIR` у процессов не задан. Для этой установки `managed()` истинен из-за маркеров Friday и `hermes-agent.source.json`, поэтому `get_managed_dir()` возвращает пусто и managed overlay не накладывается. В `settings` plugin нет строк `${...}`, так что env-подстановка этот узел не меняет. `DEFAULT_CONFIG` ключа `friday_rework` не содержит.

`plugins.enabled` корневого файла: `web/exa`, `friday_rework`, `dashboard_auth/basic`. `friday_rework` не в `plugins.disabled`. Это user-plugin, не bundled: в загрузку его пускает allow-list, а не автозагрузка backend. В обоих named profile allow-list короче: `web/exa` и `friday_rework`; `dashboard_auth/basic` у них в deny-list.

## Значение, которое получит ctx.get_config("runtime")

У корневого дома и у `dest_telegram` живой узел одинаковый: ровно `{enabled: false}`. Старого поддерева `config.runtime` нет. `host.handle` при `enabled is not True` возвращает `worker_not_admitted` до claim. Dashboard как процесс `-p default` читает корневой дом, то есть тоже `{enabled: false}`.

У профиля, имя каталога которого содержит числовой идентификатор учётной записи, живой узел другой: `enabled: true` и map `workers` с обоими видами, `dsh` и `a0`, у каждого `enabled: true`. Pin `a0.runtime` внутри этого узла указывает на файл с базовым именем `scripts/a0_runtime.py`. Это уже записанное значение. Данный проход его не создавал и воркеры не запускал.

Gateway записал `served_profiles`: `default`, `dest_telegram` и этот третий профиль. `gateway.multiplex_profiles` в корневом файле — `true` (строка 537). `multiplex_standalone_reason` пуст, `gateway_state` — `running`. Turn третьего профиля читает его файл, не корневой `{enabled: false}`. Turn `default` и `dest_telegram` читают отказ.

Квитанция установки этому не противоречит и этого не отменяет: `INSTALLED_TEMPLATE_INCOMPLETE`, `runtime_ready=false`, `worker_state=BOTH_WORKERS_PREPARATION_PENDING`. Квитанция лежит в корневом доме. Допуск в конфиге третьего профиля — другая запись.

## Авторизация не менялась

У корневого дома `dashboard.require_auth` — boolean `true` (строка 508). Dashboard слушает непетлевой адрес; для такого bind код включает gate и без этого флага. `dashboard_auth/basic` в корневом allow-list; `nous`, `self_hosted` и `drain` в deny-list. Оба named profile кладут `dashboard_auth/basic` в deny-list и не имеют секции `dashboard`. Запущенный dashboard — это `-p default`, то есть корневой файл. Секции не переписывались.

Расхождение «basic включён / basic выключен», отмеченное в карте ширины, — не два верхних ключа одного документа. Парсер отверг бы такой повтор. В корневом документе allow-list один. Отличающиеся списки лежат в файлах named profile и во вложенных шаблонах onboarding.

Скаляров `custom:friday-local` в корневом файле 57: 19 вне шаблонов onboarding и 38 внутри них. Это не 57 повторов одного ключа. Обоснованность самих 19 маршрутов этим проходом не оценивалась.

## Состав, состояние, тестер

`gateway_state.json` записывает `code_sha` `781334eea4b9225a3e194faf0c241d9afe218634` и `code_version` `unknown`. Этот sha совпадает с Hermes pin из октябрьского `sources.lock`. Квитанция состава по-прежнему `SOURCE_COMPOSED_NOT_RUNTIME_ACCEPTED`: 180 слоёв, 17730 файлов, `services_started=false`. Совпадение sha — запись процесса, не побайтовая пересборка 180 слоёв из публичного git. Такая пересборка не делалась. `sources.lock` от 2026-10-06 по-прежнему сам не является доказательством installed runtime.

Владельцы состояния, без открытия баз:

- сессии gateway: свой `state.db` у корневого дома (872448 байт), у `dest_telegram` (839680) и у третьего профиля (23056384), все mode 0600;
- durable state plugin: каталог `plugin-data/agent-plugin-friday_rework-877e6505` в каждом из трёх домов; `PluginState.data_dir` следует текущему `get_hermes_home()`;
- каталоги `sessions/` есть, содержимое не читалось;
- Telegram offset не хранит plugin. Адаптер строит PTB `Application` без `Persistence`. Холодный старт по умолчанию делает `drop_pending_updates`. Offset живёт в памяти updater до рестарта. Файл offset не найден и в `state.db` не искался.

Зависимость продукта от истории тестера разрезана так. В Python plugin `friday_rework`, в `hermes_cli` и в `gateway` нет строк `engineering_regression_module`, `bot_tester`, `candidate-r15`. Обычный путь `default` и `dest_telegram` на `get_config("runtime")` получает отказ воркера. Полный worker map есть только в конфиге профиля с числовым идентификатором в имени. Это зависимость конфигурации одного обслуживаемого профиля, не import продукта. Байты pin-ов с их sha не сверялись. Воркеры не включались.

План реализации для Астры всё ещё не написан. Не сделано: открытие `state.db`, сверка pin-ов, прогон восстановления, побайтовая сборка 180 слоёв, оценка обоснованности 19 локальных маршрутов вне шаблонов.
