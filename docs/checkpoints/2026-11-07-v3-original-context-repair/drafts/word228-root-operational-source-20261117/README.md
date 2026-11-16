# Архив проверенного Word228 Root Source

Только Code/Source ABI; запускать архив как установочную команду нельзя.
Приватныеinputs/descriptor/templates/current/authority/runtime records сюда не входят.
Фактические результаты и следующий шаг — [Source checkpoint](../../evidence/astra-20261117/word228-actual-builder-and-root-constructor.json).

# Word228: ограниченный операционный Source

Состояние: **Source UNBOUND; не полный operational frame, не install-ready**.
Действующий снимок — `word228-unbound-r5`. Ни main, ни prepare, ни once,
maintenance, сервисы, Office, модель или Telegram здесь не запускались.

`construct_word228_source.py` переиспользует ровно названные Python Code из
проверенного R2 и меняет выбранный слой на Word v6: два MOD, ноль ADD,
CAS8, retained17893; installed227/project535/native17895 сохраняются.
Предыдущие guards, бюджеты, CAS, rollback, история и clocks не пересоздаются.
R2 records, raw14/actual8 и работающие source roots не копировались.

Закрыты четыре обнаруженных пробела Source: перенесён байт-в-байт R5 observer
211f4e00; закреплены bank-manifest cf6db77f и command-prefix metadata;
новый manifest содержит оба `runtime_grant=False` и `execution_grant=False`.
Проверка frame дополнительно требует эти зависимости до once. Отдельный
readonly CLI теперь сначала проверяет Word UNBOUND и только затем читает файлы.

Старые `publication/*.py` содержат comm228 selectors и потому **не перенесены**.
Конструктор возьмёт точные финальные builder+consumer Source Сола по отдельным
refs. Это не реализация публикационного слоя и не зависимость от comm228.
До этих refs, helper/map pins и нового product commit готовность не заявляется.

## Точный интерфейс Root

`--source-selection <metadata.json>` требует ровно девять полей:

- `source_spec`: `{path, sha256}` финального Source-spec Сола.
- `source_spec_schema`: точная строка его schema.
- `private_helper_sha256`, `public_helper_sha256`: настоящие разные after pins,
  совпадающие с `spec.ordinary_helpers.{private,public}.after.sha256`.
- `after_project_map_sha256`: SHA точной private537 map.
- `product_source_commit`, `execution_commit`: два конкретных 40-символьных
  selectors своих ролей; product должен отличаться от установленного0f098 и
  от отложенного commc1cb.
- `publication_builder`, `publication_consumer`: `{path, sha256}` Source Сола.

Все refs — явно заданные cache Source. Constructor читает только spec и эти
два Code, проверяет Word2/0/CAS8/counts и копирует publication byte-exact;
`CONSUMER_SHA` получает настоящий pin. Неизвестные digest не подставляются.

`--root-bindings <metadata.json>` требует ровно три поля:
`selectors`, `source_refs`, `historical_refs`. `selectors` содержит ровно
`product_source_commit`, `execution_commit`, `new_request`, `private_input`,
`public_input`, `before_public_input`, `actual227_binding`,
`closed227_authentication`, `durable227_cutoff`; последние семь — `{path,sha256}`.
Source/historical maps — только path→SHA metadata. Constructor **не следует**
ссылкам raw14/actual8/current/history/authority. Проверка настоящих bytes остаётся
у Root. Новый Code или bank pin нельзя перекрыть через extra map.

`--destination` допускает только новый непосредственный sibling внутри данного
пакета. Переиспользование существующего output запрещено; предыдущий эффект
не возобновляется и clocks не переносятся. С флагами constructor создаёт только
Code и предварительный Source manifest, всё равно сообщает
`operational_complete=False` и `install_ready=False`.

## Остаток и ближайший шаг Root

1. Получить финальный Word Source-spec/публикационные Code/helper/map pins Сола
   и настоящий product/execution selectors; связать новый sibling constructor.
2. В своей области Root выпустить настоящий request/private537/public537,
   complete14 с неизменными13 значениями и actual227 eight binding/closure/cutoff.
   Создать descriptor `ROOT228-DATA-BINDINGS.json`, включая точные новые dependency
   hashes, private/public/previous inventories и два native-after refs. Не менять
   предыдущие input/history/receipt identity и не переименовывать effects.
3. Root связать семь существующих R2 `ROOT-228-*-TEMPLATE.json` только по их
   явным новым selectors/refs. Особые поля: Word native_pins, новый spec/input,
   новый code/frame refs, настоящий projected receipt SHA. Старые consumed
   records/clocks остаются историей; current/evidence/authority/once до своей
   фазы остаются UNBOUND. Эти шаблоны здесь намеренно не выдаются за связанные.
4. Root завершить Source-PINS точными metadata refs descriptor/templates/полных
   inventories/history и своего acceptance. Первичный manifest конструктора
   финальным freeze не является. Затем настоящий ближайший readonly caller
   `read_source_bound228.py` на полном input, независимое review финального
   frozen frame; только после этого current prepare и отдельное maintenance.

Будущие outputs не являются предусловиями: admission/anchor/qualification —
свои preoperation результаты Root; observer intent/output производятся внутри
owned stopped фазы; committed/receipt/postconsumer и service readback проверяются
после той же транзакции. Source acceptance требует postconsumer=NOT_RUN, а не
фиктивный pre-PASS. Подробная карта: `dependency-review/RESULT.json`.

`ROOT-SOURCE-CHECKS.json`: compile всех21 Source файлов и обратное применение
точного Word patch к двум настоящим Source-after файлами; оба before SHA и
байтовые размеры подтверждены. Это не текущие native observations и не runtime.
