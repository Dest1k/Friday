# Ordinary monitor: освобождение памяти сканирования

**Source-only; для будущего обоснованного исполнителя.** Точный патч к [публичному729 helper](../ordinary-disk-monitor-next-source-20261116/root_f07_once.py) восстанавливает reviewed f172/40278B; Root проверил patch→byte equality→compile в удалённом собственном временном каталоге. Diff с контекстными пробелами сохранён в deterministic gzip. Операционные bindings, исходные документы, authority, userdata и новые runtime-запуски не опубликованы.

Вложенная рекурсивная `entry` удерживала себя и `rows/visited` до cyclic GC. Единственная дельта — `finally: entry=None` после обхода. Возвращаемые rows остаются у caller; обход, ENOENT/identity/deadline/symlink/special-file guards, inode highwater, запись диагностики и owned stop/reap не меняются. Ни GCpolicy, ни конечные лимиты не ослаблены.

Native Python3.14.7, AS512MiB/CPU120: на260 реальных metadata scans/11565entries peakRSS original452861952B → fixed31629312B; fixed closures0. Original340 дошёл до492085248B, natural GC сработал и точный MemoryError НЕ воспроизведён. Это доказательство удержания/избыточного давления памяти, не доказанная единственная причина порога конкретной живой операции.16 общих/17fixed Source controls и независимое review; probe children reaped/synthetic trees removed.

Новый F01 действительно записал MemoryError; исторический F03 остаётся UNKNOWN. Не менять729/consumed callers, не повторять model/send/capture/stop/Office. Новый caller должен выбрать точный f172 ref, проверить свою изменённую дельту и актуальные предпосылки до собственного ещё не выполненного действия. Исторический live не переносится на Source-патч; никакой новой установки Friday этим архивом нет.
