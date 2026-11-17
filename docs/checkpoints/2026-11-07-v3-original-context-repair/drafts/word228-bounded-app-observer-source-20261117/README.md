# Ограниченное наблюдение модели Writer — Source, не App-приёмка

Два файла побайтово совпадают с независимым Source review 97efafa2 пакета Сола
66e79f75; frozen12 1418566b. Они не подключены к продукту и не запускали Office.

readonly_writer_cycle.py принимает настоящий Desktop/UNO от Root, загружает один
локальный ODT ReadOnly/Hidden с именованными NEVER_EXECUTE/NO_UPDATE, вызывает
observer и закрывает только полученный документ. writer_model_observer.py
наблюдает полный BODY/order/Unicode и header/footer по эффективному page style.
Ему не передаётся ожидаемый текст. Source проверки используют явные inert модели;
они не доказывают настоящую семантику PageStyleName/FollowStyle или UNO provider.
Отсутствующие/неподдержанные свойства дают UNASSESSED/refusal, без выбора произвольного
неиспользуемого или default стиля вместо эффективного.

Настоящие provider/API, default Office26.2.5.2, изоляция, права, custody входа,
общий slot, процессы/таймаут/cleanup остаются отдельными обязанностями Root.
document.close() не доказывает quiescence namespace. Launcher/provider и приватные
исходники/ODT/ожидаемые значения здесь не публикуются. Нет save/reopen/PDF/pixel цикла.

Исходный F04 требует направленных semantics/structure/declared loss и LIVE_BOT;
автоматический roundtrip или идеальное равенство всех свойств Office не добавлены.
Developerderived f807c54e и исторический received2830 различны: wholeFAIL2830
сохраняется, доставка/формальная приёмка этим Source не принимаются.

Решение Root: сохранить этот условный Source. Не строить новый UNO/provider как
предпосылку обычных документных путей; вернуться при конкретном обязательном App-пробеле
либо наличии уже пригодного provider. Ближайшая работа — настоящий недостающий
обычный Word/ODT результат по исходному направлению и ограничениям состоявшихся эффектов.
