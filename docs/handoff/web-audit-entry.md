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

На VM установлен **203 / project487 / native17891 / plugins52 / base17730**. На миграционной
границе gateway и Dashboard active/running, прежние PID/birth/InvocationID сохранены; миграция
не запускала продуктовые тесты и не перезапускала сервисы. Полный V3 не принят.

Ближайшая техническая зависимость core — настоящий переход 203→204→205 перед F06 successor.
Первая локальная попытка 204: publisher launch consumed, observer assertion, фактический exit
UNKNOWN; source-транзакция не началась, 203 полностью сохранён и проверен. Повтор старого once
запрещён. Отдельная безвредная real-unit проба обнаружила ещё один startup race observer;
R2 исправление прошло 74 детерминированных контроля, но Root review и новая ограниченная
real-unit квалификация ещё нужны. Затем — свежая подготовка действительно недостающей установки,
тот же сохранённый RTF consumer и настоящий checkpoint 204, а не выдуманный predecessor 205.

Текущий функциональный срез — F06 защищённые Office-файлы. Standard3.2, privacy и ODF изменения
приняты на уровне исходников, не установлены. Task23 Сола подготовил prospective normal205→206
и независимое source review; четыре полных source gates ещё NOT_RUN, ждут решения Астры по
конечным ресурсам. Шаблонный Office harness и узкий capture expected-refusal имеют независимые
source reviews; реальные App/ordinary admission и формальная приёмка из этого не следуют.

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
из одного source PASS. Часть новых R2/F06 пакетов ещё только в приватных source-копиях.
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
