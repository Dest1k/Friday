# D6 — internal metric context, SOURCE only

Пакет продолжает CASE165/F04 ODS→XLSX: старый generated-rich candidate закрывает
D1–D5/D7–D8, этот diff добавляет условную producer-token relation для D6.
**Не установлен, не integration-ready; actual M/provider/historical applicability
UNBOUND. Сохранённая a2e→b93 не принята; исходный отказ не переписан.**

Внутренний immutable context проходит через render, validate_destination,
compare_rich, declared_losses и fidelity_report. Его type/fields/hashes лишь
связывают уже проверенные факты; они не аутентифицируют producer/font/reference
или историческую применимость. User/JSON loader отсутствует. Обычный
execute_conversion оставляет context=None и прежний строгий путь.

Отдельные exact source rational lengths + исходные lexemes и destination Decimal
width tokens сравниваются по source-derived forward rule с независимо полученным
raw M. Ширины не заменяются source values; scope/overlap/coverage/hidden/style/
graph/scalar/formula/cache и raw same-format guards сохраняются. Quantization
many-to-one; physical fidelity UNASSESSED. M здесь raw current-reference logical
scalar, без присвоенной физической единицы.

Независимое review обнаружило и закрыло два дефекта: near-half XML parsing и
зависимость Decimal construction от ambient precision. Лексические binary64
uncertainty bounds дают только refusal, не tolerance для target equality;
неоднозначные XML/SaveXml решения остаются OPEN. Integer conversion half-up
сохраняется. Это не universal C++ parser и не сокращение V3 обязательств.

35consumer +25generic/namespace методов, retained4/profile/bound pair и10native
semantic controls прошли. Положительные M128/другие примеры синтетические;
они не доказывают actual M/runtime/случай. Неизменные graph/style/chart/source
review переиспользованы; final numeric delta проверена отдельно.

Следующий реальный provider должен получить проверенный context **после
_read_output и до validate_destination**. Опциональный render keyword полезен
для уже известных retained bytes, но сам будущий output не наблюдает.
Сравнивающая функция не запускает Office/observer. Root отдельно заканчивает
current metric observation и ограниченную applicability bridge, затем связывает
producer факты с точными bytes. Готовый carrier этого не заменяет.

Здесь CODE/patch/контракт и тесты; приватных документов, runtime grants/once,
сырых traces/logs и payload oracle нет. Operator cache paths в тестах исходные;
архив предназначен для review, не turnkey запуска без входов.

[Evidence](../../evidence/astra-20261115/calc-d6-context-source-and-prelaunch-inspection.json).
Original2793/full180NO_RESPONSE/0received/stopUNKNOWN и один b93 render CLOSED;
новый source не разрешает их повтор. Source83/App NOT_RUN_NO_RECEIVED_ARTIFACT.
Full170/120/B00 OPEN; core → DSH → A0.
