# Calc: контракт ordinary `spreadsheet_convert` — source-only

Проверенная дельта для `tools/file_tools.py` установленного219. Это часть
будущего целого Calc220, отдельно не подключена и не установлена. Пять остальных
файлов библиотеки/CLI и реальная output-квалификация находятся у Сола74; этот
patch не является самостоятельным исправлением конвертера или новым слоем.

Before186098B/SHA `246bb05029881a002db7374f4452b0f196a8e56e2ca1cd5a63423fda532ad42f`;
after186414B/SHA `e46b3d015a4f3e7b17214d8ffe92c67e8a9417a9e93efb516223d209f6dbc13c`.
Изменены только два AST-узла: conversion guidance и его включение в конечное
компактное описание. Handlers, enum, остальные параметры и профили прежние.

Фактический registry сохраняет ссылку на schema; конечное описание заменяло
промежуточные длинные каталоги. Старый запрет rich-профилей не входил в конечную
схему: вызванного им отказа модели не наблюдали. Исправляется отсутствие точного
контракта bounded XLSX/ODS conversion и требования раскрывать все возвращённые
known losses и UNASSESSED аспекты. Финальный OpenAI envelope9056→10045B, +989B.

27 source-stand проверок охватывают фактическую registration/dispatch/metadata
цепочку с явно inert authority/CAS/render/publication leaves. Root независимо
проверила два AST-узла, финальную schema и exact patch apply/compile. Это не
обычный model-run, не реальный Sol74 final JSON, не Office/App, установка или
формальная приёмка. Кандидат целиком должен включать5modified+1added native files,
17893 total/17887retained, exact219 prefix и неизменные guards.

[Доказательства и ограничения](../../evidence/astra-20261114/calc-ordinary-tool-contract-source-qualified.json).
