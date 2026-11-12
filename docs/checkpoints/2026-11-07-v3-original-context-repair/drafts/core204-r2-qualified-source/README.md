# Core204/205 observer R2 и будущий frame — проверенный source

12.11.2026, МСК. Cumulative patches меняют только `publisher_terminal_proven` и `run_owned_publisher`;
204/205 функции симметричны. 74 детерминированных контроля и 8 независимых контролей (для каждого
варианта) прошли; source review без блокеров. Архивы содержат код/шаблоны для анализа, не live-допуск.

Новые два собственных harmless units дали реальные exit0/2, точную binding/cessation и отказ
terminal proof без предварительной привязки. Оба первых snapshot уже имели полный InvocationID:
**новая emptyID wait ветка не наблюдалась live**, её основание — source review и детерминированные
контроли. Старые product publisher и probe0 остаются consumed/UNKNOWN; не запускались повторно.
Постоянные сервисы и четыре canonical203 pins сохранены, slot освобождён. Это не установлен204.

`future-frame-source.tar.gz` — 26 frozen source files + manifest/result/review. Actor сохраняет R2
функции byteexactAST; меняет будущую unit и hash joins. Recovery задаёт настоящий HERMES_HOME,
сохраняет raw dashboard status до отказа и использует строгий R2 terminal proof. Builder/publisher
byteexact, default4 не расширен. Root принял source, 10 групп pure controls и независимое review.

**Полная цепочка исполнения ещё не готова:** нужен новый caller/boundary source, связывающий
свежие процессы после восстановления203 с неизменными исходными доказательствами203. Старый caller
запрещён: он привязан к прежним PID и уже потреблённым current outputs. Новая подготовка ведётся
отдельно; ни текущих request/readback/admission/qualification/once, ни установки архив не содержит.

При одинаковых настоящих input/history builder выдаёт прежний request SHA: новый путь/unit не salt.
Отсутствие текущего txdir/intent — наблюдение, не доказательство, что код никогда не исполнялся.
Допуск недостающей установки требует Root reconciliation текущего203/CAS/quiescence/tx absence,
сохранения старого consumed launch и свежего ограниченного исполнения; никаких UUID/guard bypass.
Извлечённые архивы не подставлять вместо canonical установленных receipt/действительных VM-путей.
