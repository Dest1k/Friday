# Штатные локальные установки204/205 без GitHub

Owner12.11 явно поручил не связывать локальную работу с доступностью GitHub.
Исправлена исполнительная обвязка Root: выбранный local-committed-main проверяет
настоящий HEAD==main, raw Git-объекты, ancestry, исторический published48,489
public/private source entries,28 сохранённых различий и5 текущих reviewed blobs
с рабочими файлами. Remote observation=None/DEFERRED_NOT_VERIFIED. Tracking-ref
не становится свежим remote; published-remote не получает fallback при сбое сети.

Пятнадцать canonical private-файлов обновлены Root по before-CAS с сохранением
всех beforeimages. Transitive metadata/actor/wrapper/template pins согласованы;
реальные предшественники203→204→205, source inventory, CAS, stop/rollback/данные,
общий slot и конечные бюджеты остаются. Product updater эти remote-запросы не
требовал: устранена зависимость двух подготовленных Root execution frames.

39 исходных offline controls с настоящим Git и13 независимых delta controls
приняты; Root дополнительно проверил60 связей/AST-условий,92 canonical refs и
обе реальные canonical metadata-функции на текущем репозитории без сети.
Это source-интеграция, не состоявшаяся установка. Actual mutable admission и
normal maintenance отдельно, после нового exact committed main и readback.
Исторические403/часы/эффекты/UNKNOWN не изменены. Не выдавать журналируемое
per-file обновление за атомарность при отключении питания. Raw diff сохранён
точно с обязательными пробельными context lines; содержимое не нормализовано.
