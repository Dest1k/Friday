# F06: process-local PyUNO args compatibility — source only

СолTask27 завершён; [Root source acceptance](../../evidence/astra-20261112/sol-task27-root-source-acceptance.json).
Freeze305d1659, finalRESULTfe3fc0e3/review9abefe7d/parent66da67af. Два client library файла меняются,
три ближайших caller/observer/adapter byteexact. Нет delta в Friday-native или общем/private Office bank.
Только exact6 generated exceptions и reserved builtin-str args/exact tuple/exactreceiver используют
BaseException descriptor; остальные поля/receivers делегируются оригиналу. Per-step/final identity/CAS,
owned-only best-effort rollback и immediateprivateclientexit при ошибке; не hostile/concurrent atomicity.

Source48initial/25reviewer/23changed/12protocol/36composition относятся к своим различным scopes,
не суммируются в приёмку. Reviewer-fix отдельно проверен другим участником; исходные ошибочные
проверяющие/первоначальный draft сохранены. Ни PyUNO bridge, ни новая Office-проба не выполнялись.

[Actualclass1](../../evidence/astra-20261112/f06-ott-one-class-diagnostic-partial.json) остаётся TERMINAL_STOP,
normalpayload/causeUNKNOWN; старый18AppPARTIAL не повторялся. Следующий возможный Root шаг — отдельный
coherent copiedframe с новой sourcequalification/assignment/once/freshcustody для одного недостающего
post-change readonly observation. Этот source archive не даёт такого допуска, не standalone installer
и не обязательная зависимость обычного userF06. Абсолютные VM dependencies оставлены для provenance.
