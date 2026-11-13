# R02 — проверенная исходниковая и изолированная подготовка

Сол Task40 завершён; Root проверил57 записей private freeze и15 прямых refs. Здесь выборка исходников, изолированных наблюдений и review, побайтово сохранённая по ARCHIVE-MANIFEST. Private transport/queue/session records не публикуются; их отсутствие не означает отсутствие истории.

**Установка/обычный Telegram runtime/controlled live cut/remote ACK reconciliation/формальная приёмка R02 не выполнены. Продуктового патча нет.**

Настоящий text caller→SQLite→startup в собственном стенде:65 assertions, четыре process-cut точки. Lost ACK приводит к marked resend fake provider1→2: это контрпример критерию отсутствия дублирования, а не PASS R02. Managed file:21 checks/23 собственных процесса подтверждают UNKNOWN и immutable-history fence; это не remote receipt reconciliation. Независимое review и два настоящих отрицательных history probes приняты в своих пределах.

Первоначальные60 наблюдений и три перезаписанные linked-ref версии M1 не реконструировались; их старые байты UNAVAILABLE, erratum сохранён. Изменённые65 исходники/наблюдения имеют отдельные точные хеши. Первые отказы собственного file harness сохранены отдельно. Process crash после fsync не доказывает powerloss-атомарность; DELETE fixture не равен installed WAL. Две настоящие power recovery остаются доказательствами сохранности/возврата сервиса.

Не запускать этот архив как допуск к live: пути/authority/once/cut/реальный ACK остаются UNBOUND. Для повторения source-проверки нужна собственная изолированная копия и действительные входы; пригодные неизменные наблюдения переиспользуются. Дальше — отдельный минимальный source-кандидат безопасного восстановления обычного Telegram текста, затем Root integration/runtime/controlled-live по исходному CASE147. Старые эффекты не переигрываются.
