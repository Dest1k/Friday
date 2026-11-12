# Friday — вход для веб-аудита

Актуально на **12.11.2026, МСК**. Canonical repository — **[Dest1k/Friday](https://github.com/Dest1k/Friday)**,
default branch — **main**. Публикация сюда разрешена владельцем; локальные установка и проверки
сохраняют независимость от доступности GitHub. Старое назначение `alinescafs3mp-afk/friday_rework`
больше не используется для fetch/push. Исторические ссылки и verdict не переписаны.

## С чего читать

1. [ASTRA-CURRENT.md](../checkpoints/2026-11-07-v3-original-context-repair/ASTRA-CURRENT.md) — короткий
   действующий состав, очередь, ограничения повторов и ссылки на доказательства.
2. [Рабочие правила](../WORKING-RULES.md), [продуктовый профиль](../product-profile.md),
   [установка](../native-installer.md), [web/admin](../mandatory-web-admin.md).
3. [V3 scope, раздел 7](../checkpoints/2026-11-07-v3-original-context-repair/DSH-RESUME-2026-11-10.md#7-объём-v3)
   и [дневная редакция goal](../checkpoints/2026-11-07-v3-original-context-repair/ASTRA-GOAL-REVISION-2026-11-12.json).
   Большой RESUME — подробная история; выполненную очередь из его старых фрагментов повторять нельзя.
4. [Миграционный checkpoint](../checkpoints/2026-11-07-v3-original-context-repair/evidence/astra-20261112/repository-migration.json)
   — факты переноса и границы опубликованного среза.

Отдельного действующего `roadmap.md` нет: ближайшая очередь находится в ASTRA-CURRENT,
исходные 170 кейсов / 120 расширений / B00 сохраняются по указанному scope и существующим ledgers.
Отслеживаемого `AGENTS.md` в данном checkout нет; инструкции команды и часть исходных контрактов
находятся в VM/TUI. Этот файл не заменяет их и не создаёт новый реестр приёмки.

## Цель и ближайший результат

Довести установленную Friday до полного согласованного V3. Порядок ресурсов всей команды:
**основные пользовательские пути Friday → DSH → A0**. Астра — sole lead/live-интегратор на Fast;
постоянный Сол — co-architect на Standard. Native goal Астры active в прежнем thread
`01a1c688-e36d-7021-8df4-9c5644a4d75b`; UUID, история и накопленный учёт не переносились вручную.

На VM установлен **206 / project493 / native17891 / plugins52 / base17730**. Нормальный205→206
завершён за134.77s: publisher0/freshDEFAULT0/fullnative/dataPASS; gateway/Dashboard постоянные,
Telegramconnected/3routes, actors/boundary/publisher закрыты. [Итог установки](../checkpoints/2026-11-07-v3-original-context-repair/evidence/astra-20261112/native206-installed-and-operation-closed.json),
[текущий readback](../checkpoints/2026-11-07-v3-original-context-repair/evidence/astra-20261112/native206-publication-observation.json),
[точный исходный frame/review](../checkpoints/2026-11-07-v3-original-context-repair/drafts/core206-installed-root-source-20261112/README.md).
Provenance localcommittedmain8d392 независим от публикации; первоначальная204 UNKNOWN не переписана.

Следующий ordinaryF06 singleton — ещё NOT_RUN: firstwrongread retainedStandard3.2DOCX,
normalindependentadmission/fullv42, max0docs/full180. R3freeze0a18e6b9 принят после stop/path/deadline
и reentrantsecond-signal fixes и независимой проверки reviewerdelta; свежие runtime/privacy/допуск впереди.
Старый installedtester неизменён; первой отправки ещё не было.

Отдельный normal206→207 modernODT codec прошёл source/gateprep review; четыре полных synthetic
gates исполняются последовательно, operational-success0/291 иrollback0/209assertions уже сохранены. Это не installed207,
не повторgenuine7 и не ordinary/App/formalF06PASS. Argon2id19/AES256GCM границы приведены
в [source codec](../checkpoints/2026-11-07-v3-original-context-repair/drafts/f06-modern-odt-source-20261112/README.md); в206 modernODF boundedunsupported.
Standard3.2 не даёт authenticatedMAC/data_integrity_verified.

Установленный RTF-helper прочитал теже10723B с16body/3stories/restoredfootnote; partial/layout/numbering
границы сохраняются. AppF06 template18 остаётся PARTIAL:12typedrefusals/6correctopen+семантика,
6getRequestSystemError доclassification/rawall_passfalse/client1. Actualpayload/causeUNKNOWN.
СолTask25 завершил [минимальный source-only frame](../checkpoints/2026-11-07-v3-original-context-repair/drafts/f06-one-template-diagnostic-frame-source-20261112/README.md)
для одной недостающей class-only readonlyOTT-пробы; Rootruntimegrant/новое наблюдение ещё впереди, не replay18.

[RuntimeWARN consumer](../checkpoints/2026-11-07-v3-original-context-repair/evidence/astra-20261112/runtime-warn-standalone-not-run.json) — NOT_RUN:
standaloneRoot import отказал штатным nativeoperatorentryguard доWARNcalls0, собственные процессы/PMlease закрыты.
Это не наблюдённыйbotfailure. СолTask26 в своей Standard TUI готовит минимальный puredependency cleanup
без ослабления productionadmission и без нового искусственного prerequisite для обычной Friday.
Астра сохраняет live-интеграцию; source readiness и пользовательская приёмка разделены.

## Что можно проверить из репозитория

- [plugins](../../plugins/), [patches](../../patches/), [scripts](../../scripts/),
  [tests](../../tests/), [validation](../../validation/) — опубликованные реализации и проверки.
- [checkpoints](../checkpoints/), [architecture-audit](../architecture-audit/),
  [analysis](../../analysis/) — датированные результаты, включая FAIL, UNKNOWN и NOT_RUN.
  Исторические суточные отчёты не являются действующим расписанием.
- Контрольные суммы текущего checkpoint: [SHA256SUMS](../checkpoints/2026-11-07-v3-original-context-repair/SHA256SUMS).

Исходники, установка, исполненный пользовательский путь, семантическая оценка и формальная
приёмка — разные факты. Приватные native receipts, БД/WAL/SHM, Telegram runs/downloads/closures,
оригиналы и Office-наблюдения остаются на VM; веб-чат не может независимо вывести их свежесть
из одного source PASS. Установленный206, source-onlycallbackframe и futuremodernODT207
имеют разные статусы; часть материалов остаётся только в приватных копиях.
Не запускать повторно producer/model/send ради удобного PASS. R83 UNKNOWN_SEND, исчерпанные
три C10 journey и остальные consumed/UNKNOWN ограничения приведены в ASTRA-CURRENT.

## Полнота переноса и ограничения окружения

Передано **118 проектных branches** с исходными object IDs и историей; tags — **0**.
Серверные refs сверены полностью. Базовый main переноса — `69dd9c3a68519fef96edb1993bcde95ed26ccd73`;
документация миграции добавлена следующим обычным коммитом. Итоговый SHA — содержащий этот
файл коммит, а не самоссылка внутри него. Shallow/partial clone, отсутствующих нужных объектов,
LFS pointers и submodules не обнаружено. Анонимные worktree HEAD/dangling objects не
публиковались как дополнительные ветки; сохранены локально и в защищённом bundle.

Три чужих рабочих изменения не включены в миграционный коммит: `docs/foundation-status.md`,
v2 `PROVIDER-SWITCH-TECHNICAL-NOTE-2026-11-07.md`, текущий `FORMAT-COVERAGE-MAP.json`.
Их байты и незавершённые пакеты Сола сохранены; опубликованная foundation-status может отставать.
Шесть отсутствующих detached worktrees не удалялись и не реконструировались.

**GitHub Actions отключён на уровне репозитория до первого push** и не включается миграцией.
Модельные, Telegram, GPU и другие продуктовые сценарии в GitHub не запускались. Перенос Git
не переносит issues/PR/discussions/comments, releases/assets, Actions history/artifacts/secrets,
webhooks/integrations, collaborators/deploy keys и protections/rulesets. Старый ограниченный
аккаунт не опрашивался; точный состав его метаданных не подтверждён и не реконструирован.

Новое расписание ежедневного веб-аудита здесь не создавалось: его задаст веб-Астра в другом
ChatGPT-аккаунте. Прежнее обязательное расписание публикаций 21:00–22:00 отменено владельцем;
обычные завершённые блоки Астра публикует в новый main. Ежедневная актуализация native goal
не является расписанием CI и не отменяет owner pause.
