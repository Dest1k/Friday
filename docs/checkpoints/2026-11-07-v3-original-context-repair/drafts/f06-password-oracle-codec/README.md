# F06 — исправление локального Python/UNO проверяющего

PyUNO exception-as-data передавал args через UNO-поля, что ломало getRequest до
первого старого eventappend. Сохранён processlocalfix только пяти точных классов:
четыре passwordrequest и ErrorCodeRequest2. Глобальные UNO helpers/Officebank не менялись.
Все не-args поля делегируются прежнему setter; перед заменой проверяются все классы.

Negative evidence: OOXML требует completedtypedMSPasswordAbort; ODF требует
completedtypedDocumentPasswordAbort → exactErrorCodeRequest2.ErrCode283Abort.
Другие классы/коды/порядок/ошибки callback отвергаются. Сама цепочка доказывает
password-gated cancellation, а не автономное отсутствие corrupt/IO: необходимы
те же хеши и правильное открытие с требуемым содержимым. Один None, ErrorCode
или IllegalArgumentException не принимаются. Для последнего OOXML нужен Position1
после typedsequence, в дополнение к положительной проверке того же файла.

69 затронутых purecontrols и независимое source-review PASS. Root подтвердил
4negative/2positive на samebyte DOCX/ODT; это не оценка остальных5профилей.
Actual g6 all_pass=false и три диагностических среза сохранены. Следующий этап —
verify-inputs-only7/21probe/0store с новым свежим CAS/допуском, без пересоздания файлов.
Эти исходники не установлены, не дают nativeGRANT/F06/релизной приёмки.
