# RTF и ODP — принятые исходники, не установленный слой

11.11.2026. Установленный native201 сохранён; эти два diff не подключены к LAYER_NAMES.
RTF4 и ODP2 применяются к точным actual201 preimages; неизменённый generated-ODP3 diff
находится в [соседнем draft](../generated-odp-consumer/consumer-repair.patch).
Три проверенных patch вместе дают9непересекающихся nativefiles, patch apply/AST PASS.

- `rtf-rich-native-r4.patch`: отдельные inert header/footer/footnote stories, создание,
  чтение и body revision с сохранением unselected wire, реальные tool/schema metadata и
  read checkpoint. Сложные stories/endnotes/comments/visual/reference numbering не закрыты.
  Review исправил пересечение ignored/hidden destinations и потерянный read checkpoint;
  предыдущие наблюдения/версии не переписаны.
- `odp-passive-text-source.patch`: существующий presentation_text_edit на ограниченном
  пассивном ODP с пустым office:scripts и одним leaf text:span, без generated marker.
  Реальные source identity/CAS/изоляция/повторная правка возвращённой копии проверены
  через настоящие wrappers с явно synthetic authority. General import/convert/table edits
  и сложные spans этим diff не добавлены. Directory payload/nested-span дефекты исправлены.

Это source/offline приёмка, не installed/runtime/live/formal tester/V3 PASS.
Готовится единый core202 со следующим точным actual201→202 переходом; старыйv3helper
не поддерживает четвёртую связь. Новыйv4source/helper имеет pure45/parser76, финальные
четыре whole-consumer gates ждут resolvedv2состава. Частные operational/public counterparts
сохранены отдельно; private worker helper не публикуется.

Для ODP producer нужен версионированный coherent b711+c459 bank, только для pptx_odp.
Предложение прямого document entry выявило обязательную freshprofile инициализацию:
старый холодный directcall давал81; oosplash способен повторять argv. Новая правка
сначала реально инициализирует документ-free профиль, проверяет setup/buildid/пустые
repositories/activation maps и затем допускает один directdocument call. Она ещё
проходит независимое review. Basic/macrosecurity механизма в продукт не добавляет.
Ни новый bank, ни202не установлены; новых Office/producer/model/send вызовов нет.

R92/g2/Gen4, исходные FAIL/PARTIAL/UNKNOWN, канонические документы и часы неизменны.
Отдельные новые readonly app/render рецепты требуют Root fresh admission; не запускать
по этому README. Оперативное состояние — [ASTRA-CURRENT](../../ASTRA-CURRENT.md).
