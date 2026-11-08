# FRIDAY-RELEASE-V3 — вход для нового руководящего исполнителя (DSH)

Дата: 2026-11-08, МСК. Составил: Kimi Code (предыдущий лид/интегратор).
Назначение: самостоятельная точка входа для исполнителя, который не видел переписку
предыдущей сессии. Содержит факты, решения, состояние операций и ссылки на первичные
материалы. Ничего не переписывает в истории.

## 0. Порядок чтения

1. Этот файл — целиком.
2. `docs/checkpoints/2026-11-07-v3-original-context-repair/RESUME-HERE-2026-11-08.json` —
   подробный технический checkpoint (обновлён под передачу).
3. `docs/checkpoints/2026-11-07-v3-original-context-repair/B00-REMAINDER-HANDOFF-2026-11-08.json` —
   учёт B00-подвыборки и форматов (исторический, но факты верны).
4. `/home/jericho/jericho/friday_v3_autonomy_directive.txt` — действующие полномочия владельца.
5. Исходные реестры: `/home/jericho/.jericho/team/kimi/assignments/KIMI-B253-B00-FINAL-PHASE-QUEUE-INTEGRATION/CURRENT86-IMMUTABLE-SNAPSHOTS/CASE-LEDGER.json`
   и `EXTENSION-OPERATION-LEDGER.json` в том же каталоге.

`docs/FRIDAY_FINITE_REPAIR_AND_VALIDATION_RU_2026-11-07.md` — исторический V2-регламент.
Читать можно, но его требования «остановиться на READY_FOR_FULL и ждать разрешения на FULL»
ОТМЕНЕНЫ. Методика (разделение причины и статуса, запрет слепых повторов, сохранение UNKNOWN
и исходных сроков, переиспользование пригодных доказательств) действует.

## 1. Objective (последняя принятая редакция)

FRIDAY-RELEASE-V3 — довести установленную Friday до готовности по V3: согласованный
функционал и покрытие, исправленные дефекты, регрессия, сохранность данных и проверенное
восстановление. Исполнитель — единственный лид и интегратор.

Объём: **170 кейсов, 120 расширений форматов**, предусмотренные операции, варианты,
последовательности и предписанные повторы. TIFF — P-06, приоритет P1. B00 — часть этого
объёма, не отдельная цель. Обязательства: ассистент, документы, память, контекст, изоляция
пользователей, веб, админка, DSH/A0.

## 2. Критерий завершения

На итоговом установленном составе подтверждены все обязательства V3, предписанные повторы,
регрессия и восстановление; **нет текущих обязательных FAIL/BLOCKED/UNKNOWN/NOT_RUN**.
Исторические неудачи и действительно внешний остаток отражены честно. Отложенные идеи и
необязательный техдолг в релиз не добавляются.

Патч, установка, READY_FOR_FULL, B00, отдельная волна или отчёт сами по себе goal не завершают.

## 3. Действующие решения владельца (2026-11-08)

- Пользовательский общий бюджет goal **отменён**. Числа 3, 600, 664 и остаток 525
  действующими ограничениями не являются, переносить их нельзя. Собственный лимит DSH
  в рамках передачи не настраивается.
- Требование остановки на READY_FOR_FULL и отдельного согласования FULL — отменено.
- Внешняя «Root-власть» для выдачи допусков тестеру **не требуется**: допуск выпускается
  штатно самим исполнителем (см. §8). Утверждения о недоступной внешней authority опровергнуты.
- Смена управляющего клиента сохраняет полномочия и критерии приёмки. Новый исполнитель
  принимает роль единственного лида; сессия Kimi Code после передачи остаётся paused.
- Установку и настройку DSH выполняет Грок, не новый исполнитель.

## 4. Полномочия и ограничения

Разрешено без согласования каждой операции: адресная диагностика; исправления продукта и
данных бандла; проверка на изолированной копии; подготовка установочного кандидата;
корректная установка, переключение и восстановление; регрессия; адаптация существующего
тестера; адресная доработка установки/обновления, если это нужно для текущего перехода;
короткие управляемые остановки и перезапуски сервисов Friday на безопасной границе.

Не разрешено/не входит: перезагрузка хоста; вмешательство в чужие сервисы; новые внешние
права; новый общий updater, новый тестовый фреймворк, глобальная архитектурная уборка,
новые продуктовые возможности; изменение модели, весов, endpoint и существенных настроек;
увеличение параллелизма; автономное подключение Грока и запуск Qwen baseline; любые действия,
затрагивающие личный разговор владельца.

Обязательно сохранять: проверки полномочий и состава, данные, историю, UNKNOWN, исходные
сроки, одного receiver и согласованный cursor. Секреты и приватные материалы — не в чат,
не в документы, не в Git. Исторические квитанции не переписывать. Повтор неизвестного
внешнего эффекта запрещён; новый run-id такого права не даёт.

## 5. Фактическое состояние на момент передачи (2026-11-08 10:5x МСК)

### Репозиторий
- Проект: `/home/jericho/jericho/Friday_rework`, ветка `main`, **HEAD `53c3577`**
  (`checkpoint: handoff ready for a new Kimi control session`).
- Рабочие изменения, НЕ относящиеся к передаче (сохранить, не включать в коммит передачи):
  - `M docs/foundation-status.md` — посторонняя правка, существовала до этой работы;
  - `?? docs/checkpoints/2026-11-07-v2-bounded-diagnostics/PROVIDER-SWITCH-TECHNICAL-NOTE-2026-11-07.md` — untracked.
- Remote: `origin https://github.com/alinescafs3mp-afk/friday_rework.git`.

### Установленный состав
- Runtime-home: `/home/jericho/jericho/Friday_rework/.runtime/friday-184-20261108`
  (184 overlay, 17888 файлов).
- `hermes-agent/tools/file_tools.py` sha256
  `6a20973d38e90aae2b66a07d714200b10dbe3f1f5e3b4a18c1ce2b44873e1161`
  (guard `write_file` для неподдерживаемого format).
- `FRIDAY-INSTALL.json`: `state=INSTALLED_TEMPLATE_INCOMPLETE`,
  `worker_state=BOTH_DEPLOYMENTS_QUALIFIED`.
- Install input: `/home/jericho/.cache/FRW-KIMI-INPUT-NEWHOME-20261108.json`
  sha256 `a98ccd54a4940dbb92a1322144d3b7edfac6aaf8a00db49009864c7539235321`.
- PM-окружение: `.runtime/friday-184-20261108/installs/be596ce02c5f6cde/environments/ffe0d97db6f3453eac3437e83399c554`.

### Сервисы и receiver
- `hermes-gateway-1e9db5b2.service` — **active**, MainPID 1281305,
  start_time 14163437, запущен 2026-11-08 09:20:25 MSK. Работает из нового home,
  Telegram polling подключён 09:21:38.
- `hermes-gateway-1b7e7667.service` (старый home) — **inactive**.
- Старый home `.runtime/friday-normal-both-workers-frw032` сохранён, gateway остановлен,
  данные (профили, state.db, сессии, Store) на месте — это путь восстановления.
- Dashboard не запущен: продуктовый bind 192.168.12.128:9119 требует auth provider.
- Второго receiver нет. Эта сессия Kimi Code после передачи — paused, новых отправок не делает.

### Тестер
- Бинарник: `/home/jericho/.local/lib/friday-telegram-bot-test/bot_tester.py`.
- State-dir: `/home/jericho/.local/share/friday-telegram-bot-test` (443 run-записи).
- Идентичности: TESTER=8812646969 («Jarvis», отправитель), PEER=8751854128
  (@jerichodevbot, продуктовый бот).
- Статусы run-записей: EVIDENCE_READY 342, STOPPED 61, OBSERVING 25,
  PRE_REQUEST_REFUSED 11, **UNKNOWN_SEND 2**, RECOVERED_PARTIAL_CAPTURE 1, PREPARED 1.
  40 незавершённых исторических записей блокируют новую работу без адресного допуска
  (gate: `bot_tester.py:11640-11642`).
- Две записи `UNKNOWN_SEND` — неизвестные эффекты. Повторять их запрещено.

## 6. Подтверждённые результаты (что уже сделано)

- Кандидат 184 слоя собран, установлен в новый home и квалифицирован дважды
  (`DEPLOYMENTS_QUALIFIED`, `BOTH_DEPLOYMENTS_QUALIFIED`).
- A0-квалификация пройдена; цепочка причин и ремонтов зафиксирована в RESUME-HERE
  (`a0_probe_*`, `a0_policy_*`, коммиты `61d539d`, `a2b35df`, `f06720d`, `3cf82b7`,
  `03f58f4`, `492d8e9`, `0b7aa0d`, `ae7591e`, `6ff5da6`, `b80eae3`).
- Выполнен drain-and-replace: новый gateway активен, старый остановлен, старый home сохранён.
- Живая проверка установленных байтов инструментального слоя (до передачи):
  неверный format → точная ошибка `unsupported_format` со списком допустимых;
  обычная запись → `bytes_written 5`, `verified true`; `/etc/...` →
  `Refusing to write to sensitive system path`.
- Форматы (прямой вызов установленного слоя, PM venv, HERMES_HOME=new home): csv PASS;
  docx/xlsx/zip/7z → `document_creation_requires_user_scope` (нужен user-scope контекст,
  прямой вызов его не даёт). Это не покрытие — через живой путь не прогонялось.
- Форматная волна прошлых циклов (create): docx, odt, rtf, txt, xlsx, ods, csv, tsv, pdf,
  zip — PASS по содержимому; 7z — PASS по структуре, содержимое не проверено.
  Extract: docx, pdf, csv — PASS. Детали и sha256 артефактов — в B00-REMAINDER-HANDOFF.
- B00-учёт: 30/62 шагов отправлено, 33/62 встречается в run-записях, 19–20 content-pass,
  2 honest partial. **B00 не принят.** 31/170 — состав подвыборки, не число принятых кейсов.

## 7. Установленная причина отсутствия ответа на D-12 (r42)

Наблюдение (первичные материалы):
- `runs/root-b00-d12-long-1-physical-01-r42.json`: `status=EVIDENCE_READY`,
  `send_state=sent`, `send_attempts=1`, `message_ids=[]`, `seen=[]`, `observations=[]`,
  `acceptance=NOT_ESTABLISHED`, `scenario_sha256=474a829bc05a7e28b2c1bf71652e94354bfb14694e2c3c502882cf1aa71d8b55`,
  `deadline=1794121752.2980897`, `capture_until=1794121455.5519319`.
- Продукт: `telegram_update_receipts_8751854128.json` содержит
  `{"update_ids":{"102501098":1794120856.0171278}}` (09:54:16).
- `logs/gateway.log` последняя строка:
  `2026-11-08 09:54:16,006 INFO ... [Telegram] Cached user document at
  .../.runtime/friday-184-20261108/cache/documents/doc_b80b04ae369f_recipients5.csv (text/csv)`
  — и после неё ничего: ни диспатча хода, ни строки отказа.
- `logs/agent.log`, `logs/errors.log` после 09:54:16 содержат только служебные
  `FRW_SOURCE_GUARD_V1` строки.

Установленная причина (подтверждена кодом и состоянием, не гипотеза):
в новом home отсутствует слой допуска пользователей, поэтому входящее сообщение
отбрасывается молча до создания хода. Конкретно:
- `plugin-data/agent-plugin-friday_rework-877e6505/` содержит только `.state.json.lock`,
  файла `state.json` нет → хранилище `product_access.v1` пустое.
  `hermes_cli/friday_product_access.py: gateway_allowed()` на пустом сторе возвращает False.
- `platforms/pairing/` пуст → нет native-гранта (`PairingStore.is_approved('telegram', 8812646969)`).
- `plugins.entries.friday_rework.settings.product_access.accounts[0].runtime_profiles`
  = `["default"]` (в старом home было `["default","dest_telegram","telegram-bot-8812646969"]`).
- `user_isolation` в конфиге нового home отсутствует; каталога `profiles/` нет.
- `platforms.telegram` содержит только `enabled: true`; в старом home было
  `extra = {"drop_pending_on_cold_boot": false, "unauthorized_dm_behavior": "pair"}`.

Порядок проверок в продукте (`gateway/authz_mixin.py`, `_native_principal_authorized`):
`friday_product_access.gateway_allowed()` → `friday_ordinary_gateway.receiving_pairing_store().is_approved()`
→ затем `friday_user_scope.admit_source()`. Первый же шаг на пустом сторе даёт отказ.

Как это выглядело в старом home (для сравнения, первичные материалы):
- `gateway_state.json`: `served_profiles: ["default","dest_telegram","telegram-bot-8812646969"]`;
  `channel_directory.json`: DM `467035772 Rinat`, `8812646969 Jarvis`.
- `plugin-data/.../state.json` → `product_access.v1.users`: ключ
  `b21d67fc1b4ccce97241421bf86e3bc7416064133f7afd0822e6734ac6d5eef5` (8812646969,
  enabled, role user, generation 2) и ключ
  `3f2592fa5fb114a4f8f65e64edeb1234a0e2274d5a2e297253fa0fdfe41314cc` (467035772,
  enabled, role user, generation 1).
- `platforms/pairing/telegram-approved.json`: `467035772 Rinat`,
  `8812646969 Jarvis approved_at 1792211701.8982375`.
- `user_isolation.bindings`: 467035772 → `dest_telegram`, 8812646969 → `telegram-bot-8812646969`.
- Профили `profiles/telegram-bot-8812646969` и `profiles/dest_telegram` с
  `.friday-onboarding.json` (template `friday-ordinary-local`, `authorization_home` = старый root),
  `.friday-user-scope.json`, своим `.env`, `config.yaml`, `sessions/`, `state.db`, `workspace/`.

## 8. Восстановление Jarvis: состояние и найденный штатный путь

**Что уже восстановлено в новом home: ничего.** Записи состояния не создавались:
вся работа остановилась на разборе пути, до первого write. Проверок, изменивших продукт,
не было.

Что требуется восстановить (область Jarvis `telegram-bot-8812646969`):
привязку (binding), авторизацию (pairing-грант + product access), сессии и данные, —
сохранив прежние права владельца (467035772) и не затрагивая его личный разговор.

Найденный штатный путь (все элементы —API самого продукта):
- `plugins/friday_rework/admin.py`: `users()`, `set_user(profile, **values)`,
  `pairing(profile)`, `approve(profile, platform, transport_profile, account_id, request_id)`,
  `onboarding_*`.
- `plugins/friday_rework/access.py: ProductAccess.set_user(*, platform, transport_profile,
  account_id, user_id, enabled, role)` — писатель хранилища с generation; проверяет
  `access_policy()` и `require_transport()`.
- `gateway/pairing.py: PairingStore.generate_code(...)` / `approve_request(platform, request_id)`
  / `is_approved(...)`; CLI `hermes pairing list|approve <platform> <request-id|code>|revoke`.
- Онбординг пользовательского home: `plugins/friday_rework/onboarding.py`
  (`prepare → credentials → prepare_worker → activate`). `activate()` требует:
  подписанную квитанцию `.friday-onboarding.json`, привязанную к **новому** root;
  scoped-секреты в `.env` профиля; native pairing-грант; при `runtime.enabled` —
  квалифицированные воркеры dsh+a0; затем пишет `friday.user-home.v1` MARKER и
  строку доступа.
- Операторский контур: `plugins/friday_rework/operator_metadata.py` требует dashboard
  auth provider и операторскую сессию. В новом home `admin.operators` =
  `[{"provider":"basic","user_id":"dest"}]`, dashboard не запущен. `require_operator_write()`
  вне активного read-запроса — no-op, поэтому писатели продукта вызываемы в процессе.

На каком действии остановились: перед вызовом `ProductAccess.set_user(...)` для
8812646969 (и следом 467035772), с намерением затем проверить причину «прохождением
запроса». Решение о том, восстанавливать ли сразу runtime-профиль
(`user_isolation` + `profiles/telegram-bot-8812646969`), осталось открытым; см. §9.

## 9. Важное следствие для форматов и изоляции

`hermes-agent/tools/file_tools.py:1069-1070`:
`if format != "text": return document_creation_requires_user_scope` — документальная
запись не-text формата проходит только при активном user-scope (`scoped_file(...)`
возвращает результат). Слой user-scope включается наличием `user_isolation` в конфиге.
Отсюда: обязательства по 120 форматам (и, возможно, часть D-12) требуют восстановления
user-scope/профиля, а не только строк доступа. Это установленное следствие кода,
но в живом прогоне ещё не проверено.

## 10. Состояние R42 и ограничения на повтор

- Run `root-b00-d12-long-1-physical-01-r42` закрыт: `EVIDENCE_READY`,
  `acceptance=NOT_ESTABLISHED`, `seen=0`, `message_ids=0`, `observations=0`.
  Итог: **FAIL «ответ не найден»** (не отказ продукта в явном виде).
- Продукт получил и закэшировал документ (update 102501098, 09:54:16), ход не создан.
- Позднего ответа нет: `gateway.log` после 09:54:16 молчит, `seen=[]`.
- **Повторно эту отправку не выполнять.** Она сохраняется как отрицательный результат
  с исходными сроками (`deadline`, `capture_until` не переписывать).
- Новая регрессия D-12 допускается только: (а) новым run-id, (б) после восстановления
  допуска, (в) с адресным независимым допуском, покрывающим новый run-id и актуальную
  историю, (г) с сохранением старой записи без изменений.

## 11. Работа с допуском и тестером (как есть сейчас)

- В `bot_tester.py` сейчас зашиты три точки под R42:
  `ORDINARY_INDEPENDENT_SCENARIOS = {"root-b00-d12-long-1-physical-01-r42": "474a829b..."}`;
  `ORDINARY_INDEPENDENT_AUTHORITY = {path:'/home/jericho/.cache/FRW-KIMI-FMT-20261108/INDEPENDENT-AUTHORITY-R42.json',
  bytes:15747, sha256:'814010c88cb32e31aef46c83afc47e0adb6bea7ce6e39326efa7209faa4a1a6f'}`;
  строковый `authority_id` = `ordinary-independent-b00-fmt-wave-20261108-r42`.
- Выпуск нового допуска (методика, подтверждённая в этом цикле): новый
  `INDEPENDENT-AUTHORITY-Rnn.json` в форме `encoded()` тестера
  (`json.dumps(ensure_ascii=True, sort_keys=True)` + `\n`), копия 40 проверенных
  history-строк, привязка gateway pid/start_time/state_path; затем **три перепина**
  в `bot_tester.py`. «Root» — декларативное поле оператора, выпуск выполняет сам лид.
  Держать снапшот `bot_tester.vNN.py` на каждую волну.
- Адресный допуск должен быть привязан к фактическому gateway: pid 1281305,
  start_time 14163437, state_path нового home (при перезапуске gateway привязку обновить).
- Снапшоты: `/home/jericho/.cache/FRW-KIMI-FMT-20261108/INDEPENDENT-AUTHORITY-R29..R42.json`,
  `bot_tester.v25.py`.
- Первичные доказательства по переключению: `/home/jericho/.cache/FRW-KIMI-SWITCH-20261108`;
  по A0: `/home/jericho/.cache/FRW-A0-HOST-RECONCILE-20261108`.

## 12. Входы и материалы для контекстных последовательностей

- Сценарии и фикстуры B00: реестр `CASE-LEDGER.json` и `EXTENSION-OPERATION-LEDGER.json`
  (путь в §0). D-03 inputs: `FRW-USER-JOURNEY-ADOPTION-PREPARE/package/fixtures`
  (все три входа существуют, хэши совпадают).
- Рабочие артефакты форматов и прошлых волн — в
  `docs/checkpoints/2026-11-07-v3-original-context-repair/` (волны 1–28, `*-RESULT.json`,
  `B00-COVERAGE-MAP.json`, `COMPOSITION.json`).
- Принятые байты документов прошлых волн лежат в профиле старого home
  `.runtime/friday-normal-both-workers-frw032/profiles/telegram-bot-8812646969/workspace/`
  (в т.ч. `received/`).
- Пользовательские данные и личный разговор владельца — в старом home
  (`profiles/dest_telegram`, сессии/Store). Не трогать; при переключении переносить
  только штатным путём и без потери.

## 13. Открытые дефекты продукта (не закрыты)

1. `friday_start.launch`: `custody.run(gateway install/start)` падает внутри bwrap
   (`systemctl --user`); запуск с хоста работает — так gateway и был поднят.
2. Dashboard на non-loopback bind `192.168.12.128:9119` требует auth provider — не запущен.
3. Не-text форматы через прямой вызов установленного слоя требуют user-scope (§9).
4. TIFF-приём (P-06, P1): файл доставляется, но в workspace не появляется; гейт
   `gateway/run_inbound_media.py` молчит. Диагноз не завершён, ремонт не сделан.
5. `write_file` loop из D-12 (невалидный format → серия `product_user_scope_refused` →
   жёсткая остановка): фикс готовился, откатан; в установленном составе есть только guard
   на неверный format.

## 14. Ближайший конкретный шаг

1. В новом home (`HERMES_HOME=.runtime/friday-184-20261108`) восстановить допуск штатными
   писателями продукта:
   `PairingStore.generate_code('telegram','8812646969','Jarvis')` → `approve_request(...)`;
   то же для `467035772` (Rinat); затем
   `ProductAccess(PluginState('friday_rework')).set_user(platform='telegram',
   transport_profile='default', account_id='8751854128', user_id=..., enabled=True, role='user')`
   для обеих идентичностей. Ничего не писать в `state.json` руками, `.env` не читать.
2. Проверить причину **прохождением запроса**: `gateway_allowed()` и `is_approved()` для
   источника 8812646969 должны давать True; затем одна контролируемая отправка от тестера
   (не replay r42) должна создать ход — подтверждение искать в `logs/agent.log`/`gateway.log`
   и в сессии продукта.
3. Решить и выполнить восстановление runtime-профиля Jarvis (`user_isolation` binding +
   `profiles/telegram-bot-8812646969` с сессиями/данными) через `onboarding_*`, с квитанцией,
   привязанной к новому root. Без этого документальные форматы, вероятно, останутся
   scope-refused (§9).
4. После этого выпустить адресный допуск под новый run-id (три перепина) и провести
   отдельную регрессию D-12; оценить доставленный ответ и байты результата.
5. Живая регрессия: неверный format (точная ошибка), допустимая запись, отказ вне области.
6. Далее — остаток V3: 170 кейсов, 120 форматов (TIFF P1), повторы, восстановление,
   дефекты §13.

## 15. Что нельзя повторять

- Отправку r42 и любые blind resend неизвестных эффектов (2 записи `UNKNOWN_SEND`).
- Повторные прогоны ради счётчика; переписывание исторических квитанций и сроков.
- Повторное доказательство того, что прямое редактирование закреплённых файлов не проходит.
- Попытки выдать допуск через внешнюю «Root»-власть — такого требования нет.
- Новый тестовый фреймворк, новый updater, глобальную уборку.
