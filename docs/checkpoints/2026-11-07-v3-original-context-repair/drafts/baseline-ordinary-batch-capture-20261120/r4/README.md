# Сверка намерения чтения с записью наблюдения

На R3 удаление активной записи `PENDING` или её замена предыдущей `EMPTY` с теми же смещением и записью приёма возвращали ложное `EVIDENCE_READY` после потери уже полученного своевременного пакета. Отдельно воспроизведён один обычный `getUpdates` после появления остановки наблюдателя между записью намерения и вызовом.

R4 сохраняет номер поколения и SHA-256 активной записи в существующей записи наблюдения. Поколение увеличивается при каждом обычном чтении, включая последовательные пустые ответы на том же смещении. Вызов возможен после обеих устойчивых записей. При пропаже активной записи, её замене или остановке между записями наблюдатель фиксирует неопределённый исход до сетевых запросов. Если точный пакет уже сохранился, он остаётся доступен для локальной оценки.

После записи намерения тестер повторно сверяет курсор и проверяет действующие ограничения, включая остановку и паузу. При известном отказе до API фиксирует `NOT_DISPATCHED`. Допуск к вызову использует меньший из свежего бюджета и исходного остатка. Проверка с исходным бюджетом 3 с, затратой 2 с на записи и свежим допуском 9 с передала API ровно 1 с.

| Снимок | SHA-256 |
| --- | --- |
| Архивный снимок установленного тестера | `cc36c0933bd01cfa5c33a3fb1123fefd0345a2185fbcf7f70f5a3bc2f7c0905b` |
| Кандидат R1 | `002fdbcada5e3cb4c516e01807177a2cbb573f439f24a2491e370d611c48b4af` |
| Кандидат R2 | `2a328fb6763e638bc297502945b24aa595a1a76a54da21e06898912e098ceed2` |
| Кандидат R3 | `b2ff1b299d88531e9ac7d3573279a0c0a54810fc1d5e928713aba39514703bd6` |
| Кандидат R4 | `ac1b13a1e3868098e39c8df7a6592da7a5c5d8765e8a0b8fedfc9167c57e8f7f` |

## Проверка без сети

Команда для запуска из корня Friday_rework.

```bash
(
  set -e
  checkpoint=docs/checkpoints/2026-11-07-v3-original-context-repair
  draft="$checkpoint/drafts/baseline-ordinary-batch-capture-20261120"
  candidate_dir=$(mktemp -d)
  trap 'rm -r -- "$candidate_dir"' EXIT
  source="$checkpoint/evidence/tester/bot_tester.installed.py"
  verify_sha() { printf '%s  %s\n' "$1" "$2" | sha256sum -c -; }
  verify_sha cc36c0933bd01cfa5c33a3fb1123fefd0345a2185fbcf7f70f5a3bc2f7c0905b "$source"
  cp "$source" "$candidate_dir/bot_tester.py"
  patch --batch --forward --fuzz=0 -d "$candidate_dir" -p1 < "$draft/ordinary-batch-capture.patch"
  cp "$candidate_dir/bot_tester.py" "$candidate_dir/bot_tester_r1.py"
  verify_sha 002fdbcada5e3cb4c516e01807177a2cbb573f439f24a2491e370d611c48b4af "$candidate_dir/bot_tester_r1.py"
  patch --batch --forward --fuzz=0 -d "$candidate_dir" -p1 < "$draft/r2/ordinary-poll-witness.patch"
  cp "$candidate_dir/bot_tester.py" "$candidate_dir/bot_tester_r2.py"
  verify_sha 2a328fb6763e638bc297502945b24aa595a1a76a54da21e06898912e098ceed2 "$candidate_dir/bot_tester_r2.py"
  patch --batch --forward --fuzz=0 -d "$candidate_dir" -p1 < "$draft/r3/ordinary-poll-intent.patch"
  cp "$candidate_dir/bot_tester.py" "$candidate_dir/bot_tester_r3.py"
  verify_sha b2ff1b299d88531e9ac7d3573279a0c0a54810fc1d5e928713aba39514703bd6 "$candidate_dir/bot_tester_r3.py"
  patch --batch --forward --fuzz=0 -d "$candidate_dir" -p1 < "$draft/r4/ordinary-poll-pin.patch"
  verify_sha ac1b13a1e3868098e39c8df7a6592da7a5c5d8765e8a0b8fedfc9167c57e8f7f "$candidate_dir/bot_tester.py"
  python3 -I -B "$draft/r4/check_pin.py" "$candidate_dir/bot_tester.py" \
    "$candidate_dir/bot_tester_r3.py" "$candidate_dir/bot_tester_r2.py" "$candidate_dir/bot_tester_r1.py"
)
```

Прошли 43 проверки. Использованы временный журнал, синтетический транспорт и управляемые часы. Проверены удаление и подмена намерения, остановка перед вызовом, обе точки расхождения записей, три обычных пустых чтения на одном смещении и возобновление после подтверждённого пустого ответа. Квитанции ранних версий проверяются без изменений. Действующий тестер, длительность проверок на его защищённом состоянии и Telegram в этом запуске не затронуты.
