# Rich ODS → generated XLSX: промежуточное наблюдение

SOURCE-only, **не готово к интеграции/установке**. Патч явно интерпретирует только false/0 у definedName function/vbProcedure. True/active/external/неизвестные свойства по-прежнему запрещены.24 source controls пройдены, окончательного независимого review этого code-патча нет.

На тех же сохранённых локальных XLSX bytes после патча отказ переходит к column defaults. Обязательная связная дельта также затрагивает scalar styles/metadata, print defaults, table и chart/cache semantics; неизменённая проверка column width отдельно возвращает FAIL. Не применять один этот патч к обслуживаемому home.

[Доказательства и восемь частей дефекта](../../evidence/astra-20261115/f04-rich-destination-one-offline-render-defect-matrix-source-only.json). Единственный отдельный offline render завершён/очищен; дальше pure checks уже сохранённых bytes. Они не являются received-артефактом ordinary2793 и не меняют его NO_RESPONSE/stopUNKNOWN/часы. Новый renderer/model/send/App ради PASS не разрешён. Оригинальные source/received/receipt/история сохраняются.
