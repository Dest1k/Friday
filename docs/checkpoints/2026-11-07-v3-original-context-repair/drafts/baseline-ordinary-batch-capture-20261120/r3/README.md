# Неопределённый исход чтения до записи пакета Telegram

На R2 синтетический пакет вернулся в момент 1002 при отсечке 1003. Наблюдатель остановился перед первой устойчивой записью пакета. После возобновления в момент 1004 финальное чтение вернуло те же обновления. R2 пометил их как поздние и выдал `EVIDENCE_READY` без наблюдений.

R3 сохраняет запись о попытке до вызова API в одном файле на наблюдение. Запись привязана к контексту, смещению и предыдущей записи приёма. Наблюдатель закрывает её при проверенном пустом ответе, известном первичном ограничении частоты, истечении бюджета до вызова или фиксации точного непустого пакета R2. Если процесс остановился между фиксацией пакета и закрытием записи, возобновление сверяет хеш и принадлежность пакета этой попытке.

В воспроизведении того же сбоя на R3 итог — `STOPPED` и `TRANSPORT_OUTCOME_UNKNOWN`. Флаг завершения окна отсутствует. После возобновления сетевых вызовов нет. Тестер сохраняет активную запись и блокирует обычное новое задание на том же курсоре. Остановка между записью намерения и сетевым вызовом также оставляет неопределённый исход.

Разрешённый повтор чтения остаётся на том же смещении. Ограничение частоты на таком повторе сохраняет неопределённость первого запроса. Подтверждённое первичное ограничение частоты сохраняет штатную паузу и возможность возобновления. Время записи вычитается из уже рассчитанного бюджета вызова. Если запись закончилась после отсечки, обычный вызов пропускается.

| Снимок | SHA-256 |
| --- | --- |
| Архивный снимок установленного тестера | `cc36c0933bd01cfa5c33a3fb1123fefd0345a2185fbcf7f70f5a3bc2f7c0905b` |
| Кандидат R1 | `002fdbcada5e3cb4c516e01807177a2cbb573f439f24a2491e370d611c48b4af` |
| Кандидат R2 | `2a328fb6763e638bc297502945b24aa595a1a76a54da21e06898912e098ceed2` |
| Кандидат R3 | `b2ff1b299d88531e9ac7d3573279a0c0a54810fc1d5e928713aba39514703bd6` |

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
  printf '%s  %s\n' cc36c0933bd01cfa5c33a3fb1123fefd0345a2185fbcf7f70f5a3bc2f7c0905b "$source" | sha256sum -c -
  cp "$source" "$candidate_dir/bot_tester.py"
  patch --batch --forward --fuzz=0 -d "$candidate_dir" -p1 < "$draft/ordinary-batch-capture.patch"
  cp "$candidate_dir/bot_tester.py" "$candidate_dir/bot_tester_r1.py"
  printf '%s  %s\n' 002fdbcada5e3cb4c516e01807177a2cbb573f439f24a2491e370d611c48b4af "$candidate_dir/bot_tester_r1.py" | sha256sum -c -
  patch --batch --forward --fuzz=0 -d "$candidate_dir" -p1 < "$draft/r2/ordinary-poll-witness.patch"
  cp "$candidate_dir/bot_tester.py" "$candidate_dir/bot_tester_r2.py"
  printf '%s  %s\n' 2a328fb6763e638bc297502945b24aa595a1a76a54da21e06898912e098ceed2 "$candidate_dir/bot_tester_r2.py" | sha256sum -c -
  patch --batch --forward --fuzz=0 -d "$candidate_dir" -p1 < "$draft/r3/ordinary-poll-intent.patch"
  printf '%s  %s\n' b2ff1b299d88531e9ac7d3573279a0c0a54810fc1d5e928713aba39514703bd6 "$candidate_dir/bot_tester.py" | sha256sum -c -
  python3 -I -B "$draft/r3/check_intent.py" "$candidate_dir/bot_tester.py" "$candidate_dir/bot_tester_r2.py" "$candidate_dir/bot_tester_r1.py" -v
)
```

Прошла 31 проверка с временным журналом, синтетическими часами и транспортом. В число проверок входят воспроизведение исхода R2, контроль неизменности его квитанций, согласование точного пакета после остановки, пустой ответ, исходные отсечка и бюджет, разрешённый повтор и оба варианта ограничения частоты. Продолжительность локальных записей на рабочем состоянии и живой Telegram не проверялись. Установка и рабочее состояние тестера не затронуты.
