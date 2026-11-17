# Общая инструкция документов и пересчёта XLSX — Source-кандидат

Схема инструмента теряла ранние инструкции после финального compact-description override. Кандидат сохраняет Word conversion, docx_fill с полной картой полей и видимыми неизвестными значениями, затем добавляет existing XLSX edit → отдельный xlsx_recalculate → возврат пересчитанной копии. Backend и проверки не меняются.

Патч и manifest здесь — архив Source, **не LAYER_NAMES и не установка231**. Native230 сохраняется. До интеграции обязательны финальное независимое review пакета F05 Сола и точный successor/consumer/rollback на настоящем230. Отдельная установка старого7b1 не нужна.

[Точные pins и границы](SOURCE-CHECKPOINT.json). Word7b1/reviewae3bedc3 переиспользованы без изменений. XLSX append:29pure-контролей, Root-проверка только трёх description paths; actual provider envelope/tokens не наблюдались. S08 остаётся PARTIAL.
