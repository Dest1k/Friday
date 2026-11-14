# Обычный finite-parent: source-кандидат после v02

Статус: **SOURCE/OFFLINE, независимо проверено; не подключено к продукту и не является допуском к операции**.

Точная общая дельта [generic-parent.diff](generic-parent.diff) привязывает no-follow FD-обход к исходным inode/lineage, заменяет рекурсию итерацией, ограничивает lifetime positive-inode highwater без вытеснения charges, сохраняет эскалацию и reap при ошибке сигнала и явно сообщает STOP_UNCONFIRMED. Диагностика сохраняет до двух enum phase/class/place без exception text, путей или содержимого; её отказ не опережает cleanup. Исходные clocks и единственный actor сохраняются.

База общего helper: `e40343ca212f551d62e842879485f039fbfc6bfb0d9e6777b64776e9eb832ce0` (34852B); проверенный результат: `2c24ce5363472e6295eeba1561c0084c452d2e3df1986090a3473dd881fbc73f` (40533B). Публикуется точная функциональная дельта без закрытых Root bindings; полный wrapper/его источники и свидетельства сохранены защищённо. Финальный wrapper: `8ce4cc41d23f748569d30db9491c55ba74630a7a7458b744cc7089a9daeca93d`.

Автор выполнил35 offline checks на связанном Word.execute→helper пути и адресных scanner/cleanup сценариях. Независимый review закрыл R1–R4: ancestor/swap, signal-cleanup, highwater и глубину; реальные локальные children reaped. Сохраняются sampled-growth ограничения, это не hard filesystem quota и не доказательство power-loss atomicity.

Для применения нужна отдельная ещё не состоявшаяся операция с действительным источником/областью/правами/отменой/бюджетом и точными helper/wrapper SHA. Причина исторического v02 `AGGREGATE_DISK_MONITOR_REFUSED` остаётся UNKNOWN; его51.013667s/full180/once/model/send/Office не переигрываются. Другие прежние consumers автоматически не заменяются.
