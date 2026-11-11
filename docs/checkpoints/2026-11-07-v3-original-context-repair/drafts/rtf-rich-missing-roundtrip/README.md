# RTF rich: отсутствовавший save/close/reopen

Проверенный QA-source, фактическое приложение **NOT_RUN**. Не подключение к runtime и не разрешение на повтор R92.

Сол Task12: финальная кандидатура r4, freeze `14bd8ab0d9d9c457863230f00c7ecd681968f43e2a04eace7a766adee704269f`. Кодовый diff опубликован отдельно от приватных fixtures/oracles. Полная постановка и exact24pins — в связанном source-result. Root проверяет код/ресурсы/банк перед отдельным допуском.

[Полученный пакет](../../evidence/astra-20261111/rtf-rich-missing-roundtrip-sol-source-received.json). Исходные результаты и часы сохраняются.

Патчи с историческими whitespace/context bytes сохранены в `.patch.gz` без изменения распакованных байтов; SHA исходного текста указан в evidence. Распаковывать только для чтения/проверки в собственной копии.
