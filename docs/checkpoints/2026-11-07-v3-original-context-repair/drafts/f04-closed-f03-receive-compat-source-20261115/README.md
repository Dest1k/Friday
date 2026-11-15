# F04: совместимость чтения закрытых квитанций F03

SOURCE-only снимок: установленная Friday223 не изменена. Полный V3/B00 остаётся OPEN.

Обычный v42 потерял `first_send_phase/original_deadline/effective deadline`, которыми
аутентичный producer завершённого F03 связал22 immutable receipts. Новый F04 отказал
в `Runner.new → cursor_offsets → receive_inventory` до создания run/SDK/send.
Исходные квитанции и все часы сохранены.

[source_adapter.py](source_adapter.py) сохраняет три исходных admission-seam и
добавляет только reader-совместимость точного закрытого F03. Читаемая копия
добавляемого блока — [closed_f03_receive_compat.py](closed_f03_receive_compat.py).
Три метода взяты из аутентичного producer; helper52d48 используется только в
неизменной read-only dependency closure. Другие phase-bearing или незакрытые
строки отказывают; остальные строки используют исходные методы. `entry/send/ACK`
старого F03 не подключаются, старый grant не возобновляется.

69 локализованных инертных контролей и independent review ACCEPT. Root отдельно
проверил все настоящие522run/473offsets и ближайший `Runner.new` до перехваченной
первой записи. В этих проверках не было token/SDK/send/canonical writes; это не
пользовательская или формальная приёмка. Реальные operator bindings и исторические
контракты остаются приватными; этот снимок не является командой на запуск.

[Manifest](SOURCE-MANIFEST.json), [текущая граница R3](../../evidence/astra-20261115/f04-r3-closed-root-review-input-schema-and-source-ready.json).
