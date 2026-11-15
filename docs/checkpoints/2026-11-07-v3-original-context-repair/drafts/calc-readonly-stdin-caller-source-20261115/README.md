# Calc observer: readonly stdin — проверенный SOURCE

LocalServices.spawn передавал subprocess.DEVNULL. В установленном Python3.14
_get_devnull открывает /dev/null как O_RDWR. Строгий helper guard требует O_RDONLY.
После закрытого Office отказа helper_parent_stdin_custody исправлен ближайший
вызывающий путь: explicit with open(os.devnull, 'rb') перед Popen.

839-байтный patch меняет только stdin leaf. Guard, stdout/stderr, argv/env,
start_new_session, close_fds, бюджеты, clocks, native/metric/close checks неизменны.
Независимые AST/mock проверки:76; parent descriptor закрывается после Popen или
при исключении. Actual same-namespace old/new tinyPython probe: fd0 access2→0,
оба /dev/null/EOF, parent FD counts stable, дети reaped/absent. Код Office/GDB
в этом leaf probe не запускался. Base namespace_entry.py находится в соседнем
calc-paper-helper-guard-source-20261115/candidate/outer; применить этот patch к
его точным before bytes. Это архив, не инструкция установки.

Следующий закрытый Office LOAD прошёл прежний stdin gate и отказал на inherited
environment equality в первом dash exec. Метод сравнивает parent /proc/environ
(initial memory) с helper exec environment. Отдельный controlled runtime mutation
показал механизм различия initial vs effective environment, но конкретные
изменённые LO keys не записаны. Готовится корректный bounded effective getter
и диагностика keys/value hashes, без silent subset/unknown-key whitelist.

Оба Office LOAD consumed/CLOSED_REFUSED, partial internal initialization не
исключена; completed model/native M/readonly-close acceptance не получены.
Canonical/source/copy/received/receipts/DB/WAL/SHM неизменны. Source delta PASS
не является whole F04/B00/V3 или installed feature acceptance. Installed224
unchanged; full170/120/B00 OPEN. Исторические effects/clocks не переписываются.
