# F07 ordinary/current209 — проверенные исходники

Архив точных байтов phase-preparer, current-checker/caller и отдельной config-bound дельты. Исходный checker сохранён; для следующего действия выбран config-bound checker24215d1f, caller8c936fe0.

Source-only проверки: исходные66, current114+independent33, delta44+independent30. Реальные readonly ordinary/history и native/current проверки Root выполнены отдельно; пользовательские четырефазы пока NOT_RUN. Архив не устанавливается в продукт. Все live/current/authority/proof/once привязки остаются у Root; legacy continuation не исполнялся.

ARCHIVE-MANIFEST.json связывает байты с приватным origin. Ссылки внутри оригинальных файлов сохранены как provenance; приватные fixtures, каноническая история, конфиги, БД, токен и полный current snapshot в архив не включены.

Дополнен finite Root caller f4798ee4:50 source+19 independent controls. Только exact explicit Root input разрешает один owned consumer; default UNBOUND, без retry/resume/автоматического successor. Actual выполнение и его исход учитываются отдельно. Aggregate disk accounting — sampled scoped growth, не hard filesystem quota.

Первый actual finite запуск отказал на `Runner.new` до canonicalsave/API/send и закрыт. Исторический `SOURCE_ONLY_READY_UNBOUND` не переписан; **этот архив не является допуском следующего запуска**. Выявлен неперенесённый accepted historical receipt/custody adapterset в глобальном cursor/pre-save пути. Исправленная композиция и реальная readonly проверка всего ближайшего пути требуются отдельно; старый driver/input/clock/claim не возобновлять. [Фактическая закрытая граница](../../evidence/astra-20261113/f07-first-phase-pre-save-refusal-and-closed-boundary.json).
