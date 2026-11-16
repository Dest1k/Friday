# Word output visibility — проверенный Source, не установлен

Root baseline `d3ce13030f9b889adfdf352371f5bef2bf078a70`; обслуживается227.
Это точный кандидат следующего приращения от227, а не ещё одна установка и
не приёмка исторической F04-операции2828→2830. Два MOD и ноль ADD в Hermes:
`tools/scoped_word_conversion.py`, `hermes_cli/friday_workspace_word_conversion.py`.
Manifest/patch лежат рядом и подключены в исходниках как `patches/hermes/`
для выбранного следующего Word-перехода227→228. Runtime пока227; Root bindings,
current и установка ещё не выполнены. Исторический default4 builder не меняется;
будущая операция только с явным `--layer`.

[Интеграция Source/остаток до установки](../../evidence/astra-20261117/word228-public-source-integrated-before-install.json).

Исходный whitelist `loext:opacity=0%` отклонён независимым review до установки.
В официальном LibreOffice26.2.5.2 это не доказанный neutral default: свойство
соответствует прозрачности. Кандидатv6 вместо такого допуска удаляет ровно
наблюдённые opacity0 в default-style paragraph/graphic/text-properties, сохраняя
остальные XML-байты и члены пакета. Новый source-bound фильтр проверяет все
w:rPr, включая неявные/невыбранные стили; theme/foreign semantic XML/атрибуты,
hidden declarations или атрибуты rPr исключают вывод новых байтов. Вход без
необходимости восстановления остаётся на прежнем validate-пути. Цвет/фон/размер
не являются обещанием pixel visibility; это не полная модель оформления Word.

Фактический wrapper сначала выполняет restore, затем полный validate_conversion.
Иной loext:opacity, неоднозначная позиция, hidden/неподдерживаемый source,
implicit drawing-page default, видимые объекты, URI, потеря BODY/колонтитулов
получают отказ. Standalone validator по унаследованной грамматике может принять
opacity в неиспользуемом nontext-style; новое обещание относится к реальному
restore+validate consumer, который этот пакет отвергает. Иные одиннадцать
фиксированных Writer scalar defaults допускаются только на native output.

Root55/independent94+lexical31 Source checks PASS; retained raw developer
Writer-output4f466156 → derivedf807c54e сохраняет5BODY, header/footer и XML Title16ptbold.
Это отдельный разработческий артефакт, не полученный пользователем2830.
Ordinary227 READ/odt_edit на тех же derivedbytes подтверждены: одна дата меняется,
остальные члены ZIP, стили и оба колонтитула сохраняются. Reader возвращает только
BODY; его чтение колонтитулов, rendering/App и wholeWord не подтверждены.

Далее Сол готовит минимальную композицию/настоящий predecessor/CAS/consumer/rollback
от227 без отложенного communication228. Root интегрирует после проверки пакета
и свежего current. Установка, runtime нового кода, App и формальная приёмка
NOT_RUN. Старый пользовательский F04 wholeFAIL, raw/source/receipt/clocks неизменны;
новая версия не разрешает повтор producer/model/send или самого journey.

Подробные pins и доказательства — [Source checkpoint](../../evidence/astra-20261117/word-output-visibility228-source-reviewed.json).
