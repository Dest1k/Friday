# Codex: WebSocket и версия daemon, 15.11.2026

По поручению владельца обе Friday TUI выбирают штатный builtin `openai`.
Старый неиспользуемый alias `openai_https` у Астры теперь допускает WebSocket.
Изменены только transport-поля; приватные config и их резервные копии здесь
не публикуются. Модель, reasoning, Fast/Standard, credentials, thread identities
и учёт целей не менялись.

`LAUNCHER.patch` — точная небольшая дельта существующего runtime-запускателя
`/home/jericho/.jericho/runtime/sol-link-native-reconnect.py`. После штатного
выхода владельца из соответствующей TUI запускатель обновляет daemon, если его
бинарник отличается от установленного CLI. Для сброса уже сохранённого fallback
в этот раз требуется явный `friday-sol --reload` и `friday-astra --reload`.
Не запускать вторую TUI и не перезапускать выполняющееся назначение.

After SHA256 `af98cba9cca76582113c64056d63f5e9e738e789f84783ea302e548002d4b86e`.
Before представление `a06a0ca22447cfd1442be8b8310fb5523a21a087a53763dd7e9c617d66d67273`
восстановлено обратной точной дельтой после исходного чтения; это не отдельный
снимок filesystem до редактирования. Exact patch roundtrip проверен в своей
удалённой после проверки временной копии.

12 конечных проверок PASS; независимое полное source-review запускателя без
замечаний. Доказательства в `CHECKS.json` и `SOURCE-REVIEW.json`.

В Codex0.169 builtin OpenAI предпочитает WebSocket; штатный HTTPS fallback
нельзя отключить через поддерживаемую конфигурацию. Фактический новый WebSocket
не подтверждён: после owner exit/reload проверить реальный следующий запрос,
а не только config или prewarm дочерней модели. Старые WS feature flags removed,
новых flags/hooks/watchers/controllers не добавлено.

См. [точку входа](../../ASTRA-CURRENT.md). До команды владельца продолжить native
goal Астры остаётся paused; постоянные Friday gateway/Dashboard работают.
