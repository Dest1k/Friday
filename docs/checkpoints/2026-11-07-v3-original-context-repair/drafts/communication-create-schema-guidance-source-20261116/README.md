# Communication CREATE schema guidance — Source only

Наблюдённый EML CREATE2815→2818 остался FAIL: все попытки использовали to:string
при обязательном list[string]; файл не создан и не доставлен. ToolDescribe называл
ключи без типов, итоговый compact schema заменял прежнюю часть подсказки.
Связь неполной подсказки с выбором модели — inference; несовместимость типов
непосредственно подтверждена сохранёнными аргументами и native parser.

Два файла добавляют точный typed contract, escaped валидный пример EML,
ограничения и статические hints для create_schema. Native parser/schema,
изоляция/права/CAS/лимиты/отмена/atomic publication не ослаблены. Старые
error/reason/effect_disposition сохранены. Последовательная сборка настоящего
зарегистрированного schema и ToolDescribe query/paging проверены; registered
write route на изолированном стенде создал один инертный fixture, не артефакт
пользователя. Отрицательные старые shape-варианты и основные guards сохранены.

[Manifest/review pins](SOURCE-AND-REVIEW.json). Это неподключённый в установленную
версию Source; отдельный84e7 ICS/VCF serialization fix здесь не включён. Сол
собирает точныйafter227 приращение, Root ведёт установку. Sourcefixture/новая
редакция не разрешают переиграть закрытыйCREATE или подменить его приёмку.

Source file_tools.py сохраняет один прежний trailing-space в строке1927; before/after
строка побайтно одинакова. Исключение закреплено exact SHA в manifest, остальные
файлы проходят diff-check. Это не глобальное отключение проверки или правка parser.
