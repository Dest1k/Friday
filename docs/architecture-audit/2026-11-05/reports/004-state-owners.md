# AA-001: владельцы state.db

Поправка не меняет `reports/001-breadth.md`, `reports/002-config-provenance.md` и `reports/003-worker-chain-telegram-cold-boot.md`.

Наблюдение 2026-11-05T14:55:42Z. Три `state.db` открыты только для чтения, `PRAGMA query_only`. Тексты сообщений, `content`, prompt, `user_id`, `chat_id`, значения `state_meta` и тела onboarding не читались. Процессы не перезапускались. Воркеры не включались.

## Три хранилища одной схемы сессий

У корневого дома, у `dest_telegram` и у профиля с числовым именем в каталоге свой файл `state.db`, все mode 0600. Размеры: 872448, 839680 и 23056384 байт. У всех `schema_version` равен 31.

Именованные профили совпадают по составу `sqlite_master`: одинаковый sha256 схемы. Корень отличается ровно двумя объектами: таблица `delivery_obligations` и её первичный индекс. Других отличий имён объектов нет.

Общие таблицы сессий: `sessions`, `messages`, полнотекстовые `messages_fts` и `messages_fts_trigram`, `session_model_usage`, `system_prompts`, `state_meta`, `gateway_routing`, `gateway_heartbeats`, `conversation_generations`, `compression_locks`, `session_turn_leases`, `async_delegations`, `gateway_hygiene_state`. Полнотекстовые таблицы — вторая копия полей сообщения внутри того же файла. Их блоки не читались.

Это не общее хранилище на установку. Каждый дом владеет своими сессиями. Каталог durable state plugin `friday_rework` этим проходом не открывался. Он остаётся отдельным от этих трёх баз, как записано в отчёте 002.

## Что лежит в каждой базе

Счётчики строк, без содержимого:

- Корень. `sessions` 2, обе с `source=cli`. `messages` 30: user 11, assistant 13, tool 6. `gateway_routing` 2. `session_model_usage` 3. `system_prompts` 3. `state_meta` 8. `delivery_obligations` 171, все с platform `telegram` и state `delivered`.
- `dest_telegram`. `sessions` 1, `source=telegram`. `messages` 113: user 34, assistant 60, tool 19. `gateway_routing` 0. `session_model_usage` 3. `system_prompts` 2. `state_meta` 8. Таблицы `delivery_obligations` нет.
- Профиль с числовым именем. `sessions` 5, все `source=telegram`. `messages` 3735: user 432, assistant 1825, tool 1473, `session_meta` 5. `conversation_generations` 1. `gateway_routing` 0. `session_model_usage` 8. `system_prompts` 7. `state_meta` 8. Таблицы `delivery_obligations` нет.

`gateway_heartbeats`, `compression_locks`, `session_turn_leases`, `async_delegations` и `gateway_hygiene_state` пусты во всех трёх файлах.

Ключи `state_meta` у корня: `db_file_generation`, `fts_storage_version`, `ghost_session_prune_v1`, `last_auto_prune`, `message_uid_backfill`, `orphaned_compression_finalize_v1`, `store_created_at_utc`, `store_instance_id`. У обоих именованных профилей вместо двух ключей про prune стоят `friday.private_reply.latest` и `onboarding.seen.profile_build_offered`. Значения ключей не читались.

## Чего это не доказывает

171 строка `delivery_obligations` — журнал исходящей доставки в корневой базе, и все строки помечены `delivered`. Это не входящая очередь Bot API и не политика холодного старта из отчёта 003. Колонка `content` не читалась, поэтому пустота текста не утверждается.

Сессии Telegram живут в базах именованных профилей. Корневая база в этом срезе держит две CLI-сессии и журнал доставки. Какой дом был выбран contextvar в конкретном turn, по-прежнему не наблюдался.

Обоснованность 19 скаляров `custom:friday-local` вне шаблонов не оценивалась. Побайтовая пересборка 180 слоёв не делалась. Восстановление не прогонялось. План реализации для Астры не написан.
