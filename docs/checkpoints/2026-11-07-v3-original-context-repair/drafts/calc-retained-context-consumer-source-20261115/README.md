# Сравнение retained bytes: SOURCE only

Минимальный Root-only helper связывает уже имеющийся внутренний metric context с
существующими consumer API. Исходник и add-file patch сохранены побайтово.
Зависимости описаны в [публичном D6-пакете](../calc-d6-internal-metric-context-source-20261115/README.md)
и его [манифесте](../calc-d6-internal-metric-context-source-20261115/MANIFEST.json);
[canonical metric class](../calc-d6-internal-metric-context-source-20261115/scoped_spreadsheet_calc_metric.py)
повторно не копируется. Полная цепочка source pins приведена в MANIFEST.json.
Зависимости и приватные fixtures здесь не собраны, поэтому архив не является
самостоятельно запускаемым пакетом.

Контракт импорта: Root использует свежий изолированный Python с `-I -B -S`,
проверяет принятые pins helper и всей source-цепочки до импорта и точные
`module.__file__`/SHA после него. Наличие заранее загруженных `tools`/`tools.*`
требует отказа; подмена или удаление модулей ради совпадения identity недопустимы.
Helper и один проверенный package `tools` импортируются канонически. Root
передаёт независимо проверенные факты через тот же точный
`CalcReferenceMetricContext`, который экспортирует `retained_compare`;
другой класс/алиас, subclass, dict/JSON и context по умолчанию не принимаются.
Тип и SHA/размер пары связывают входы, но не подтверждают истинность фактов.

API: `compare_retained(source_bytes, destination_bytes, ctx=None, *, checkpoint=None)`.
Входы — явные immutable `bytes`. `inventory(..., 'ods')` не имеет context keyword;
один и тот же `ctx` передаётся в `validate_destination(..., 'xlsx')` и
`fidelity_report`. Требуется native imported-rich metric profile. Возвращаются
исходные inventories и неизменённый fidelity report; ошибки consumer проходят
наружу без fallback, замены ширин или фильтрации отчёта.

Root принял только source и проверенную synthetic-цепочку: 6/6 изменённых native
byte controls и 10/10 дополнительных controls, с независимым review. Использован
заранее заданный вымышленный M128 и новые приватные копии с сохранённым пассивным
происхождением; оригинальная retained-пара с вымышленным M не сравнивалась.
Fixtures, их builder, исходные документы и приватные metadata в публикацию не
входят. При подготовке архива тесты и алгоритмы повторно не запускались.

Genuine current M не установлен; historical applicability UNBOUND, сравнение
реальной retained-пары и пользовательский результат не приняты, physical
fidelity UNASSESSED. Обычный provider отсутствует/не принят; установка и runtime
не выполнены. Архив не добавляет полномочий и не является admission. SOURCE-STATUS.json
сохраняет эти пределы и исходные evidence hashes без частных абсолютных путей.
