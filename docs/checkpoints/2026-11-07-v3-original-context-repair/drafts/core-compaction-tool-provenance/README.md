# Исторические tools после сжатия

Source-only исправление одного `agent/context_compressor.py`, не подключено/не установлено.
Выбран только prefix-only SOURCE.patch; переходный marker-кандидат отвергнут. Прежние cache/preflight/canonical/API sidecars не меняются.

Фактический R104 содержит корректные факты и ложный claim нового чтения. Свежие DB row-id/timestamps после archive_and_compact не означают исполнения: call-id/байты прежние. Оба active-prefix больше не объявляют любые tools после summary текущей работой; старые shipped prefixes остаются распознаваемыми. 52tests+28subtests и independent source-review PASS.

Это устраняет конфликт инструкций, не гарантирует отсутствие всех вымышленных claims. Установкой старый summary/ответ не переписываются. R104 не повторять. Новая композиция/установка/семантическая приёмка отдельно.
