# RTF и ODP — принятые исходники, не установленный слой

11.11.2026. Установленный native201 сохранён; эти два исходных diff сохранены отдельно.
Их конечная композиция подключена как source202, ещё не установлена.
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
[Единый core202/v4](../../evidence/astra-20261111/core202-final-source-connected.json)
подключён к LAYER_NAMES: точный actual201→202, 10nativefiles с двумя добавлениями.
Четыре final whole-consumer gates success/lateDEFAULTrollback:158/78/158/78;
pure45/publisher98 и настоящий readonly builder с explicit --layer PASS.
Это synthetic/source проверки, не native/runtime acceptance. Private operational/public
counterparts сохранены отдельно; private worker helper не публикуется.

Для pptx_odp подготовлен отдельный coherent b711+c459 bank с прямым exec-soffice.bin.
[Банк физически размещён и проверен](../../evidence/astra-20261111/office-bank-physically-placed-unselected.json),
но **unselected**, application qualification остаётся. Product freshprofile init/guards
прошли независимое review; Basic/macrosecurity в продукт не добавлены. Native202 не установлен.
[Новый private rich-RTF readonly batch](../../evidence/astra-20261111/rtf-rich-readonly-app-r3-partial.json)
закрыт PARTIAL по75s Main limit; stage и исходные часы сохранены. Сол разбирает результат
без повторного Office. ODP render recipe3 готов только как source; live grant не следует из README.

R92/g2/Gen4, исходные FAIL/PARTIAL/UNKNOWN, канонические документы и часы неизменны.
Отдельные новые readonly app/render рецепты требуют Root fresh admission; не запускать
по этому README. Оперативное состояние — [ASTRA-CURRENT](../../ASTRA-CURRENT.md).
