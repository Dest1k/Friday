# AA-001: карта ширины

Срез кода: `26217103b514a9523040868af2ed6933d031ceb7`. Это родитель документального коммита, не сертификат установленного runtime. Чтение: 2026-11-05T12:54:43Z–2026-11-05T13:02:36Z. Живой процесс не останавливался, F-03 не запускался, базы не открывались.

Сложность не локальна для тестера. Публичный plugin `friday_rework` — 44 модуля Python, 17094 строки; самые большие: `onboarding.py` 1355, `host_runtime.py` 1184, `host.py` 1100, `stopped_operator.py` 1011. Поверх Hermes лежит 184 файла патчей и живая квитанция состава на 180 слоёв / 17730 файлов со статусом `SOURCE_COMPOSED_NOT_RUNTIME_ACCEPTED`. Отдельная цена повторного `compile` из R4 относится к инженерному загрузчику тестера: в plugin этого имени нет.

Продуктовый worker сейчас по записи выключен, хотя процессы gateway и dashboard есть. `FRIDAY-INSTALL.json`: `state=INSTALLED_TEMPLATE_INCOMPLETE`, `runtime_ready=false`, `gateway_installed=false`, `worker_state=BOTH_WORKERS_PREPARATION_PENDING`, scope `TELEGRAM_RECEIVER_AND_AUTHENTICATED_ONBOARDING_ONLY`. `FRIDAY-PROFILE.json`: `ready=false`, `state=TEMPLATE_INCOMPLETE`. В живом `config.yaml` (3 382 001 байт, 25786 строк) три блока `runtime:` имеют `enabled: false`. Код `host.handle` отказывает `worker_not_admitted`, если `runtime.enabled is not True` (`host.py` около строк 410–412). Это согласованная запись «воркеры не допущены», а не доказательство, что разговорный Hermes не работает.

Документы отстают от этой записи. `sources.lock.json` датирован 2026-10-06 и сам говорит, что это не доказательство installed runtime; у Hermes там `AGENT_NOT_RUN`, у A0 и DSH `NOT_RUN`. README фиксирует снимок 22 октября 2026 и неуспешный старт. Зафиксированный `docs/foundation-status.md` начинается с 17 октября 2026, 01:12 MSK. В рабочем дереве Астры к этому файлу есть незакоммиченные 4 строки от 17 октября, 04:13 MSK; в публикацию они не входили. Ноябрьские checkpoint-ы в git в основном про source156 и тестер, не про свежую приёмку продукта.

Что уже видно по коду, без прогона:

- Загрузка plugin не стартует процесс: `__init__.py` регистрирует `friday_work`, `friday_result`, hook `post_gateway_admission` и middleware `tool_execution`.
- Повтор того же `friday_work` с тем же binding возвращает статус без нового schedule (`host.py` около 401–408). Ошибка staging/schedule не объявляет работу поставленной в очередь и оставляет частичный ряд без replay (около 536–549). Это чтение кода, не живой прогон.
- Состояние ассоциаций — Hermes PluginState плюс fsync каталога (`associations.py`, `Controller._save`). Отдельной очереди в plugin-границе нет: DSH уходит в `schedule_gateway_work`, CLI — в `run_cli_work`, A0 — в отдельный producer.
- Внешние web-плагины xai / openai / perplexity в просмотренных секциях выключены, `web/exa` и `friday_rework` включены. Это не проверка, какой именно документ config загрузил текущий процесс.
- В том же файле секции plugins повторяются и расходятся: в ранней секции `dashboard_auth/basic` включён, в двух поздних он в списке disabled. Какая секция действует у запущенного dashboard, не установлено. Секреты и значения ключей не читались.

Здоровое, что ломать не следует: явный локальный маршрут без cloud-fallback в контракте профиля; отказ воркера при `runtime.enabled: false`; разделение доставки и повторного исполнения в `host.handle`; честная пометка `sources.lock`, что pin не равен runtime.

План реализации ещё не написан. Следующая глубина: какой документ config загружен процессом; кто владеет Telegram offset и историей сессии; воспроизводится ли 180-слойный состав из публичного git; не попадает ли архив попыток тестера на обычный путь продукта. Внедрение по-прежнему за Астрой после B00.

Пробелы этого прохода: содержимое `state.db` и сессий не открывалось; восстановление не запускалось; cursor тестера не отождествлялся с продуктовым offset; полный разбор 25786 строк config не делался; живой Telegram и модели не вызывались.
