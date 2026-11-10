# FRIDAY-RELEASE-V3 — единая точка входа для Сола (2026-11-10)

**Настоящий файл — единственная актуальная точка входа.** Он заменяет
`DSH-RESUME-2026-11-09.md` и `DSH-RESUME-2026-11-08.md` как рабочую инструкцию.
Оба старых файла сохранены как история; их инструкции по выбору home, переносу
данных и повторной подготовке профилей **не действуют**.

Дата: 2026-11-10, МСК. Передача: DSH-сессия → Сол (временное принятие лидерства).

## Действующее продолжение Сола — 10.11.2026, 14:26 МСК

Сол — временный lead/координатор/интегратор; разработка, необходимые проверки,
штатная установка и публикация в существующий main разрешены владельцем.
Выбор решений и нового изолированного варианта P04 отдельно делегирован владельцем:
[решение](evidence/sol-20261110/owner-autonomy-and-p04-variant.json).
Вечерняя передача Астре — только по отдельной команде; лидерство не завершает проект.

Новый **native goal** `FRIDAY-RELEASE-V3-CONTINUATION-2026-11-10` создан
09:04:04 МСК. Идентификатор API `threadId`:
**`01a1c407-7f0e-7273-9fd0-6bd9dc09ce18`**; отдельного UUID API не возвращает.
Свежий `get_goal` после восстановления вернул **active**, без собственного лимита.
Точный неизменённый objective/критерии:
[SOL-GOAL-CONTINUATION-2026-11-10.json](SOL-GOAL-CONTINUATION-2026-11-10.json).
Исторический DSH predecessor `goal-62933237-0a12-4223-a0ab-ebcaa126db76`
и snapshot сохранены, не возобновлялись. Полные **170 кейсов/120 расширений**, B00,
операции/варианты/последовательности/допустимые повторы/регрессия/восстановление
остаются обязательными. Записи реестров не подменяют исполнения.

**Git и принадлежность.** Последний опубликованный и удалённо сверенный
`main = ac8bbcb960f7edfe2fcbbc2f0858d7028c5b8685`; исходный снимок продолжения
`585f9cb9790a6182908db9ccdde263176ae39969` не откатывался. Checkpoint190/RTFrecall+edit/archivecollision/sourcecandidates опубликован
и удалённо сверён; все289 checksum entries
проверены из точных Git-байтов. Следующая дельта остаётся отдельно от опубликованного SHA.
Три чужих изменения §1 сохраняются и исключаются. Хеш текущего коммита внутрь самого
себя не записывается; точный финальный SHA сообщается по факту после commit/push.

**Todo / фактические результаты:**

- [x] Приёмка площадки и native goal; никакого повторного переезда home.
- [x] Admission: независимый SHA/size stdout, deterministic legacy exists/write race,
 63 контроля; далее точный ordered predecessor с реальным Root review/run custody,
 расширенная регрессия143. Исторические0664 reviews не chmod ради PASS.
- [x] Sidecar штатно добавлен как187-й слой без переигрывания186 прежних;57 offline
 composition/rollback controls и11 installed checks. Узкая live квалификация R71 —
 [PASS](evidence/sol-20261110/sidecar-live-root-review.json): реальный reboot/resume,
 compaction, два защищённых user-anchor с различными собственными sidecars,
 admitted main streaming guard, верный ответ. Interrupted retry не выполнен; на
 реальных metadata старый matcher тоже уникален, live red→green не заявляется.
- [x] После отключения питания сохранённые результаты приняты без повторов.
 Boot `d518758e-bce0-4bd5-89a1-fc4e113f0623`; primary и embeddings реально вычислены
 на настроенных endpoints. Postpower компрессор503 локализован до Guard status-fetch,
 причина транспорта UNKNOWN; отдельный ранее выполненный synthetic200 сохранён.
- [x] P04 guidance/OCR-warning source fix независимо reviewed; штатно добавлен только
 новый188-й слой,3 postimage.70 publication controls; receipt/marker/stamp согласованы,
 [установка](evidence/sol-20261110/p04-installed.json), свежий gateway61925/start493738.
 Установку не повторять. Восемь conflicts воспроизводятся именно на старом frozen installed-input;
 [текущий canonical граф восстановлен](evidence/sol-20261110/rebuild-graph-root-review.json)
 всеми188 реальными git-check/apply и совпадением17 888 SHA/size/mode. Receipt/input
 не переписаны; полная fresh-export CLI/новая установка этим не приняты.
- [x] R70: первая отдельная F01 TSV read/tail, sent2630→reply2632;
 [Root content/custody PASS](evidence/sol-20261110/tsv-read-root-review.json).
 R71: ordinary recall того же файла в той же беседе, sent2633→reply2635,
 [Root content/custody PASS](evidence/sol-20261110/tsv-recall-root-review.json).
 Formal в обоих случаях NOT_ESTABLISHED/RECEIVED_UNGRADED; не пересылать ради grade.
- [x] P04 новый одобренный синтетический PDF `85947e75…e6d1`: **одна** отправка R72,
 sent2636→reply2638; [исходный narrow P04 oracle/custody PASS](evidence/sol-20261110/p04-live-root-review.json).
 Есть страница/строка, неопределённость и необходимый адресный вопрос, скрытая цифра
 не объявлена достоверной. Formal NOT_ESTABLISHED. Ошибки OCR V/Q обозначений и
 неполная строка суммы сохранены как отдельный fidelity gap; не заявлять весь FXSCAN
 или все варианты принятыми. Старые C1/P04 FAIL не переписаны, sent2636 не повторять.
- [x] NJS status validation компрессора установлен отдельной ограниченной операцией:
 HTTP200 + строгие непустые string epochs, безопасная фазовая диагностика,
 UNKNOWN-once/deny сохранены.20 offline controls + independent source review;
 [source/worker deployment](evidence/sol-20261110/compression-status-deployed.json).
 Один graceful reload, новые workers2366/2367, старые822/823 вышли; master763,
 контейнеры/backend/Guard/config/ACL/identity сохранены. Старый timeout UNKNOWN
 не объяснён и не очищен; inference ради PASS не повторялся.
- [x] Архивы:18 actual workspace consumer controls,17 checker-only controls отдельно,
 3 новых genuine LHA6/LHA7/RAR4 expanded-limit refusals.195 модулей и6 core hashes
 неизменны на188; [reuse независимо подтверждён](evidence/sol-20261110/archive-final188-root-review.json),
 без повторов. Saved R34 7z оценён без пересоздания;8 codec controls отдельно.
 Затем5 новых RAR5/LHA byte-limit controls,8 ZIP/TAR entry/depth controls и
 LHA7 actual-child output-phase cancellation + pre-stopped refusal приняты отдельно:
 [5](evidence/sol-20261110/archive-new-boundaries-root-review.json),
 [8](evidence/sol-20261110/archive-entry-depth-root-review.json),
 [native cut](evidence/sol-20261110/archive-native-cancel-root-review.json).
 Cancelled child дал QUIESCENT, обаPID исчезли, публикации нет. RARcancel ungraded,
 CPU-loop interruption не доказан; оставшиеся format/link gaps не скрыты.
 A13/A14 исходно OFFLINE; gateway/live stop остаётся отдельной межсценарной областью,
 не выдавать его за проверенный и не добавлять без основания как новый oracle A14.
- [x] Saved D07: все8 seeded изменений/добавление/удаление и boilerplate подтверждены;
 формальная шкала не заменена.
- [x] M11 saved sent1909→reply1911: [custody/семантика4/4](evidence/sol-20261110/m11-saved-root-review.json)
 подтверждены по62pins и историческому compaction/security evidence. PARTIAL/full180=false/
 NOT_ESTABLISHED сохранены; это не весь M11 и не188 regression. Повтора не было.
- [x] [A03 saved](evidence/sol-20261110/a03-saved-roundtrip-root-review.json): подлинный
 source107 ZIP→7z→ZIP1846→1849/1850,16 точных payload/path,67 custody refs. R68
 отдельно PARTIAL:7z2622 новый, ZIP2623 прежний после document_already_exists.
 Неверная датировка5November и false success prose сохранены/исправлены в текущем
 narrative; весь A03/current188 не принят. Не перепаковывать/пересылать ради grade.
- [x] [M04 saved](evidence/sol-20261110/m04-saved-root-review.json): исходный Mayak
 39644bytes/a9b0… совпадает с доставленным1768, отличается от Mayak2/a72e…;
 проект/версия/identity верны, narrow raw/ACK/task/receipt custody PASS. Полный
 legacy continuation verifier остановлен отсутствующим старым UNBOUND.json;
 оригинал не реконструировался, formal UNBOUND/NOT_ESTABLISHED сохранён.
- [x] Typed archive-convert failure provenance установлен как **единственный новый189-й слой**:
 [точные5файлов/review](evidence/sol-20261110/archive-provenance-source-root-review.json),
 [18actual offline controls](evidence/sol-20261110/archive-provenance-offline-controls.json),
 [73publication/rollback controls](evidence/sol-20261110/archive-provenance-publication-offline.json),
 [реальная установка/bootstrap](evidence/sol-20261110/archive-provenance-installed.json).
 Существующий ZIP после document_already_exists не может выдаваться за новый результат;
 остаются только выбранные подтверждённые текущие артефакты, после hooks/cache/streaming.
 Отрицание bind-probe до syscall сохранено: zero attempts не заявляется. Все188старых
 слоёв/456пинов сохранены, плюс новаяпара;3БД неизменны и quick_checkOK до/после.
 Один stop/install/freshstart; текущий136726/start1051826. Специфическая live квалификация R76 теперь отдельно выполнена:
 [Rootreview](evidence/sol-20261110/archive-provenance-live-root-review.json),
 sent2648→text2652/new7z2653/alternateZIP2654, closed13:58:03. Native5228typed
 document_already_exists и durable5237projection реально достигнуты; старый ZIP
 не изменён/не выдан за новый, оба новых архива дают точные4имени/payload. Узкий
 provenance/delivery PASS; итоговый текстPARTIAL — не названы отказавшийtarget и
 успешные/запаснойимена. Следующее исправление только отчёта; R68/R76 не повторять.
- [x] ARJ genuine Unix symlink/hardlink: [4actual scoped consumer observations](evidence/sol-20261110/arj-genuine-links-root-review.json).
 DOSpositive и3refusals;214Bhardlink сначала masked ошибкой Unixregular,144Bновый
 genuine-onlylink добрался до ID55gate. Outside-hardlink target этим не доказан.
- [x] Source-only ARJ Unix attribute repair готов и независимо принят:
 [сводка](evidence/sol-20261110/arj-unix-mode-source-root-review.json).
 Baseline2genuine regular/dir RED, candidate33consumer controlsPASS; независимые
 1536type/permissions+6profile controls. Один codec; собственные ARJ0x1000/0x2000
 вместоPOSIX stat.S_IFMT; specials/permissions/CRC/quotas/path gates сохранены.
 Теперь отдельно установлен190: [публикация76controls](evidence/sol-20261110/arj190-publication-offline.json),
 [фактические receipt/marker/stamp/freshgateway/3DB](evidence/sol-20261110/arj190-installed.json).
 Сохранены189oldlayers и весь nontargetinventory; один codec11493B/29803028…75ae.
 Первый publisherentry отказал transaction_environment_required доclock/intent/изменений:
 Root пропустил HERMES_HOME.4fixedpins совпали, transaction отсутствовал; исправлено
 окружение, затемодна настоящая публикация, один freshstart. Ошибка и логи сохранены.
 Новаяgateway176791/start1388904 active/connected; wholeA13/A14 иARJuserlive ещё не приняты.
- [x] Новый read_file argumentguard подготовлен, независимо reviewed + Rootfinalprose
 [source-onlyreview](evidence/sol-20261110/read-mutation-argument-source-root-review.json):
 baseline2 воспроизводят dropcontent/format,30controls PASS; все223importedmodule
 bytes прежние на190, target6a209… неизменён. Не установлен; отдельный guarded
 increment после текущей ARJqualification. Публикуемый кандидат вsource-candidates,
 не подключён вLAYER_NAMES/установленный граф. R75/егоартефакт не повторять.
- [ ] Первая genuinely missing ARJ extraction/read черезпользовательскийпуть190;
 затем argumentguard и именованный truthfularchive status после отдельнойприёмки.
 Исходные170/120, прочие format/link gaps, regression/recovery и неизвестные
 эффекты остаются вscope, отдельные scopedPASS не закрываютwholecases.

**Живые операции и дети на срезе:** Root/Sol — единственный владелец общих
runtime/admissions/live effects и интеграции. R73 firstREAD завершён12:43:49,
exit0, sent2639→reply2641, [Rootsemantic/custodyPASS](evidence/sol-20261110/rtf-read-root-review.json),
все3абзаца/tail«готово»/№3 верны. В review добавлен тот же настоящий top-level scenarioSHA
для unchanged consumer; исходные байты preserved, ни run/grade/send не менялись.
R74 `f01-rtf-ordinary-recall-01-20261110` однократно завершён13:41:06,
sent2642→reply2644, [имя/tail и fullcustodyPASS](evidence/sol-20261110/rtf-recall-root-review.json),
native5168–5169; formalNOT_ESTABLISHED. R75 `f03-rtf-edit-preserve-01-20261110`
однократно завершён13:46:06, sent2645→nativeRTF2647,268bytes/8c3ff6df…d32e2;
[факт/оформление/исходники/custodyPASS](evidence/sol-20261110/rtf-edit-root-review.json).
Только версия1→2, все невыбранные байты и Arial11 сохранены; новаякомпактификация
реально произошла, всеphysical5170–5211 сохранены. Лишние ошибочные read_file с
write-onlycontent/format перед единственным успешным write_file сохранены как
отдельный efficiencygap, не скрыты. Пересылок ради grade нет. Активных RTFobserver нет,
gatewayactive_agents0. `rtf_continuation_preparation` завершён/принят127controls+43review.
`arj_unix_mode_repair`/`arj190_publication_preparation` и их independentreviews
завершены/приняты; actual190 установлен14:02, freshbootstrap14:03:55. `archive_collision_packet`
завершён/принят78controls+Rootreview; R76observer закрыт, узкаяnativeprovenancePASS,
wholeuserreportPARTIAL, новыеартефакты/oldtargetсохранены. `read_mutation_argument_repair`
завершён/принят, Rootпроверил финальнуюhintдельту и223unchangeddeps на190; не установлен.
`arj_first_user_preparation` завершён: unboundпакет первого genuinelymissingARJextract/read,
89scopedcontrols иactual190readonlygate; R77 CLOSED14:19:53, exit0: `a02-arj-native-content-read-extract-01-20261110`,
sent2655→regular.txt2657,17bytes/e90c743d…3aead;
[Rootpayload/nativeextract/read/delivery/fullcustodyPASS](evidence/sol-20261110/arj-first-user-root-review.json).
Source152Bfa39…69e0 сохранён; новаяпапка0700/file0600/nlink1. Native5242–5261
включают genuinecompaction5243/usercopy5251 и старыеR76toolcopies5248–5250;
они точно совпадают с5235–5237/callids/content, не являются новымwriteeffect.
Authority63571479…b536a, boundactualv425f730c52…3072e, scenario9bbefbd7…a8824.
FormalNOTESTсохранён; ни ARJCREATE/edit, ни fullmixedA02/F01recall этим не приняты.
`archive_named_status_repair`/reviewer завершены и Rootприняты source-only:
[one-methodreview](evidence/sol-20261110/archive-named-status-source-root-review.json),
5focused190controls и20indepdisplayprobes. Отказавшиеworkspace-relativetargets и
проверенныеуспехи названы изnativeledger; unsafeимена даютgenericfallback, неhostpath.
Кандидат отдельно вsource-candidates, не установлен. `two_fix_publication_preparation`
завершён/Rootпринят: [97actualcombinedpublisher controls+independentreview](evidence/sol-20261110/two-fix-publication-offline.json).
Rootподключил ровнооба sourceслоя и exact97-testedchecker bytes врабочемдереве,
новыйproject464/inputb508cc9f…9479d; actualruntime190 остаётсянеизменён.
Это ещё не192установка/сервис/пользовательскаяквалификация.
`arj_ordinary_recall_preparation`/егоindependentreviewer — активныйunboundпакет
отдельного обязательногоF01recall послеR77PASS, безreupload/extract/новыхфайлов.
`saved_r75_compression_route` завершён/Rootпринят:
[действительный summary наconfigureddispatcher](evidence/sol-20261110/compression-saved-user-path-root-review.json).
R75actual13:44:11aux custom:friday-compression/dispatcher/.78:8001→native5185→
commit13:44:17/fallback_used=false; Rootrehash6sources/2configs/9loglines/7nativerowsPASS.
Физическийbackend/worker/HTTPstatus не установлены, причинастарого503/UNKNOWN
не выводится. Новыхmodel/network/productзапусков не было.
Попытка отдельногоreadonlyconditionalLHA/7zhardlinkcontractreview отклоненаnative
`agent thread limit reached`; ребёнок не создан, independentwork продолжается. Root только владеет admissions/live/runtime; на этомсрезе
активныхliveobserver сейчас нет, R77закрыт, runtime190 неизменён. NJSdeployment закрыт/rollbackbackup сохранён; старые
закрытые назначения не изображаютсяпродолжающимися.

R42/R43, UNKNOWN_SEND, неизвестные P01/Q02 и исторический S11 сохраняются.
Новый run-id/допуск/модель/исправление/перезапуск сами по себе повтора не разрешают.
Для каждой позиции отдельно: отправка/эффект, содержательный критерий, formal tester,
основание следующего действия. Сначала сохранённые материалы и штатная сверка.

Ближайшая исполнимая граница: принять unboundordinaryARJrecall, точный реальный
orderedR77Rootreview и freshcurrentcuts, затем отдельная первая shortrecall без
reupload/reextract в тойжеSID. ИсходR77 сохранён, не повторять2655радиgrade.
После knownrecallboundary — единая только-новая190→192публикация двух исправлений:
приватный пакет `/home/jericho/.cache/FRW-SOL-V3-TWO-FIX-PUBLISH-PREP-20261110`,
RESULTdf31480e…b65c9, currentinputb508cc9fde63187aedceee222c1f778004d62416323ff63ec7b28968cd79479d,
project464; все460oldpins/190oldlayers/15metadata-onlydifferences сохранены.
Rootгенерирует собственныйrequestнаактуальнойгранице и обязательно передаёт
HERMES_HOME вpublisher; childrequestcandidate не исполнять.97gate/reviewreuse
толькоприexactbytes. Freshprocess/data/source/installed/userfacts раздельны.
НикакихобещанийconcurrentCAS/powerlosscrashatomicity: доказаныstalerequestpreflight
и in-processrollback под solewriter/quiescenthome. Полные критерии goal неизменны;
get_goalactive14:08. Вечерняяпередача не начата; постоянныеproductservicesработают.

## 0. Состояние разработки

| Предмет | Факт |
|---|---|
| Репозиторий | `/home/jericho/jericho/Friday_rework`, ветка `main` |
| Исходный HEAD продолжения | `585f9cb9790a6182908db9ccdde263176ae39969` (сверка 10.11, 09:04 МСК); прежний `476496a` — исторический |
| Последний опубликованный HEAD/origin/main | `ac8bbcb960f7edfe2fcbbc2f0858d7028c5b8685`; следующая рабочая дельта указана выше |
| Последний независимо проверенный генератор | `585f9cb9790a6182908db9ccdde263176ae39969`: short write, write/fsync refusal, единственный победитель публикации; его прежние checker-остатки затем исправлены в32bfb815; новый ordered-predecessor pin в текущем срезе |

### Исторический проход DSH (476496a)

- **SHA256SUMS воспроизводима**: 224/224 записи совпадают с точными Git-байтами
  (`git show HEAD:…`), `FORMAT-COVERAGE-MAP.json` исключён (untracked).
- **Остаточные команды повтора S-11 отозваны** в `s04-s10-accepted-s11-open` и
  `new-defect-bounded-context-sidecar`; старое — `WITHDRAWN FORMULATION`, текущее —
  `AUTHORIZATION_BASIS_NOT_ESTABLISHED`; факты трёх побайтно идентичных отправок
  сохранены. Оба сегмента читаются отдельно, 0 непомеченных команд повтора.
- **Дубликаты run-id внутри package** обнаруживаются до построения словаря
  (`object_pairs_hook`), включая случай с правильным последним хешем.
- **Публикация допуска атомарна** через `os.link`: полная запись с обработкой
  коротких `os.write`, проверка размера перед публикацией, проверка опубликованных
  байтов, удаление temp в `finally`; гонка двух выпусков — один побеждает, второй
  отказывает.

### Исторические проверки DSH, реально выполненные, и на каких байтах

| Проверка | Байты | Результат |
|---|---|---|
| `check-fresh-admission-scope.py` (реальный код `issue-fresh-admission.py`) | рабочее дерево `476496a`+правки | **55/55 PASS** |
| `check-layer-publication-composition.py` | `476496a` | **20/20 PASS** |
| `check-bounded-resume-sidecar.py` против установленного модуля `1acfe925…b948` | установленный состав (186 слоёв) | 11 тестов, **1 ошибка** — `current user anchor is ambiguous` (дефект воспроизведён) |
| `check-bounded-resume-sidecar.py` против пропатченного стенда `1ae5254d…e50e` | стенд `bench-sidecar/hermes-agent/agent/bounded_context.py` | **11/11 OK** |
| SHA256SUMS vs Git-коммит | `476496a` | **224/224 воспроизводимы** |

**Ограничения покрытия** (отделены от результатов): sidecar-проверка вызывает реальные
модули продукта (`agent.bounded_context`, `agent.context_compressor`,
`agent.turn_request_assembly`, `run_agent.AIAgent`) на подготовленном стенде (фикстурные
строки в памяти, без сети) — это **не** сквозной запуск живого gateway. Вывод: guard-
логика идентификации текущего запроса корректна на подготовленных данных; полная
квалификация пользовательского пути остаётся за живым прогоном.

## 1. Рабочее дерево

**Исторические изменения DSH (закоммичены в `476496a`, затем `585f9cb`):** RESUME, отчёт, snapshot,
SHA256SUMS, `issue-fresh-admission.py`, `check-fresh-admission-scope.py`,
6 сегментов, 2 новых patch/manifest.

**Чужие незавершённые изменения (сохранены, в коммит НЕ включены):**

| Файл | Тип | Происхождение и назначение |
|---|---|---|
| `docs/foundation-status.md` | M (изменён) | Рабочие заметки другого исполнителя о состоянии foundation; содержит устаревшие даты (17.10.2026). Не трогать, не коммитить без разрешения владельца. |
| `docs/checkpoints/2026-11-07-v2-bounded-diagnostics/PROVIDER-SWITCH-TECHNICAL-NOTE-2026-11-07.md` | ?? (untracked) | Техническая заметка о переключении провайдера. Существовала до этого прохода. |
| `docs/checkpoints/2026-11-07-v3-original-context-repair/FORMAT-COVERAGE-MAP.json` | ?? (untracked) | Карта покрытия форматов. Не входит в Git-дерево; исключена из SHA256SUMS. |

## 2. Обслуживаемый runtime (сверка190, 10.11.2026 14:05 МСК)

| Предмет | Факт |
|---|---|
| Home | `/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032` |
| Состав | **190 слоёв**; к189 добавлен только `arj-unix-attribute-types-after-source189`. Receipt `e6a6f9a7…b7dcd`; input `a34a6714…c8bc7`; stamp/marker согласованы, upstream/base прежние |
| Gateway | `hermes-gateway-1b7e7667.service` active/running, **MainPID176791**, ExecMainStartTimestamp 2026-11-10 14:02:48 МСК, NRestarts 0 |
| Состояние gateway | `gateway_state.json`: pid176791, start_time **1388904**, `gateway_state: running`, Telegram `connected`, `served_profiles = [default, dest_telegram, telegram-bot-8812646969]`, active_agents 0 |
| Boot | `d518758e-bce0-4bd5-89a1-fc4e113f0623`, загрузка 2026-11-10 10:11:19 МСК; реальный power outage |
| Приёмников | **один** (процесс176791, проверено по фактическим cmdline) |
| Docker | В этом проходе контейнеры не запускались; прежний inactive-срез не выдаётся за новую проверку A0 |
| База `dest_telegram` | 196 сообщений / 2 сессии, `quick_check ok`, счётчики до/после установки сохранены |
| База `telegram-bot-8812646969` | 5241 сообщений / 5 сессий до/после установки190; `quick_check ok`, неизменны. R73–R76 отдельные сохранённые эффекты |
| Модельный путь | Фактический `http://192.168.1.195:30000/v1`: authenticated models и synthetic chat → 200, настроенная модель найдена |
| Диспетчер сжатия | `.78:8001/v1`: postpower503 до backend на status-fetch; отдельный synthetic200 сохранён. Новый NJS source/worker deployed, старый UNKNOWN не очищен; см. актуальные evidence выше |
| Эмбеддинги | Фактический `http://192.168.1.195:8002/v1`: authenticated models и embeddings → 200, qwen3-embedding-4b, один конечный 2560-мерный вектор |

### Известные проблемы доступности зависимостей

- Старый адрес эмбеддингов `.78:8002` не был фактической конфигурацией обслуживаемого
  home. Новый результат `.195:8002` подтверждает реальное вычисление, не только корень.
- R75обычныйпользовательскийconsumer реально прошёл configuredsummaryбезfallback:
  см. compression-saved-user-path-root-review.json. Исходный503/UNKNOWN сохранён;
  успешное последующееисполнение не устанавливает причину первогоотказа.
- Модельные synthetic health probes не являются пользовательскими Telegram-задачами;
  перед любой новой разрешённой живой отправкой всё равно нужен текущий адресный допуск.

## 3. Данные и доказательства

- **Приватные материалы**: `/home/jericho/.local/share/friday-telegram-bot-test/` (runs,
  downloads, closures). **Не чистить.** История доступа, исходные результаты и
  неопределённые эффекты сохраняются.
- **Выпущенные допуски**: `evidence/tester/INDEPENDENT-AUTHORITY-R54.json` … `R68.json`
  (в checkpoint) и `/home/jericho/.cache/FRW-KIMI-FMT-20261108/INDEPENDENT-AUTHORITY-R29…R76.json`.
  Выпущенные допуски **не переписываются**.
- **Незавершённые операции**: P-01 (неизвестный исход r57), Q-02 (неизвестный эффект r7),
  A-03 (round-trip-этап — имя `core_inputs_roundtrip.zip` занято), A0 (квалификация не
  выполнена), A-13/A-14 (только через настоящий архивный путь).
- **Неопределённые эффекты сохранены**: UNKNOWN_SEND (2 записи), TRANSPORT_OUTCOME_UNKNOWN
  (r57). Не переигрывать.

## 4. Ограничения повторов

**Четыре раздельные фиксации** для каждой попытки:
1. **Отправка и эффект** — была ли отправка, установлен или неизвестен эффект.
2. **Содержательная оценка** — оценка по критерию и фикстуре.
3. **Формальная приёмка тестером** — NOT_ESTABLISHED / RECEIVED_UNGRADED / UNBOUND_UNGRADED.
4. **Основание следующего действия** — что разрешает следующий шаг.

**Правило повторной отправки**: только по ранее действовавшему разрешению с указанным
источником и точным объёмом; иначе `AUTHORIZATION_BASIS_NOT_ESTABLISHED`.
**Не разрешают повтор**: отсутствие содержательного результата, отсутствие приёмки,
новый run-id, свежий допуск, перезапуск, новая модель, исправленная композиция.

**Действующие запреты**: R42 (неизвестный эффект, не переотправлять), R43 (не повторять),
UNKNOWN_SEND (2 записи, не переотправлять), G-06, M-10 (неизвестные эффекты). Исторические
прогоны с доставленными артефактами (A-03, M-04) не повторять — эффект существует.

**S-11**: три побайтно идентичные отправки (r59/r60/r61) — факт; `AUTHORIZATION_BASIS_NOT_ESTABLISHED`
для живого повтора; `the_regression_that_must_pass` — офлайн-проверка, живую отправку не
разрешает.

## 5. Оставшиеся технические шаги

### Публикация sidecar завершена 10.11, 09:22 МСК

`bounded-current-ask-identity` зарегистрирован в `LAYER_NAMES`. Builder поддерживает
явное `--layer` и точные input/candidate/output пути. Единственный новый слой уже
опубликован и установлен по запросу `dbffff0a…3152`. **Не устанавливать его повторно.**
Исторический default четырёх слоёв сохранён; новая операция его не использовала.
Точная предыдущая input SHA совпала с marker; текущий input добавил только новую пару
patch/manifest. Новый patch действительно опубликован через journal, не выдуман в baseline.

### Граница покрытия sidecar

- Исторический дефект `current user anchor is ambiguous` воспроизведён через реальный
  прежний модуль на **подготовленном стенде** (два user-anchor, sidecar_differs=True). Это **не** сквозной
  запуск живого gateway: реальный телеграф-проход и персистентность не воспроизводились.
- Фикс (собственный `api_content` каждой строки) проверен на стенде и после установки
  на точном модуле `1ae5254d…e50e` с фактическими зависимостями home: 11/11 OK.
- Узкий новый R71 resume/compaction квалифицирован, см. актуальный sidecar-live-root-review.
  Interrupted retry остаётся NOT_RUN, реальные native IDs не воспроизводят old matcher FAIL;
  эта запись не разрешает повтор S11 либо закрытого R71 ради расширения утверждения.

### Дальнейшие необходимые проверки

- Полная квалификация P-02/P-04/M-11/D-07 тестером (сейчас NOT_ESTABLISHED).
- A-03 round-trip: сначала сверить уже доставленные материалы и занятый путь;
  свободное имя само по себе не разрешает повтор.
- P-01: сначала сверить сохранённый неизвестный эффект r57 и приёмку без новой отправки.
  Прежняя формулировка о нужном тестеру прогоне отозвана как основание повтора.
- Для зависящих от длинного сжатия проверок подтвердить consumer path; embeddings уже
  вычислены на фактическом адресе (см. §2), старый адрес не использовать как основание.

## 6. Условия работы с ресурсами

- **Temp DSH**: `/home/jericho/.dsh/tmp` (ext4, `/dev/sda2`, без квот). Переменные
  `TMPDIR`, `TMP`, `TEMP` указывают туда.
- **`/tmp`**: tmpfs `size=50%` ОЗУ = **31 ГБ**. Заявленный лимит 4 ГБ **не подтверждён**
  (usrquota заявлена, но квоты не настроены; systemd/cgroup-лимиты не заданы). **Не
  использовать утверждение о 4 ГБ как гарантию.**
- **Стенды** (в `/home/jericho/.dsh/tmp`, на диске):
  - `bench-7z` (**13 ГБ**) — **полная копия runtime/home** (817 340 файлов), стенд
    публикации слоя `bounded-7z-codec-activation`, статус
    `SOURCE_COMPOSED_NOT_RUNTIME_ACCEPTED`. **Не удалять** — служит доказательством.
  - `bench-sidecar` (299 МБ) — частичный стенд композиции (`hermes-agent` 268 МБ +
    `preparation` 23 МБ); используется для проверки слоя sidecar. Содержит пропатченный
    `bounded_context.py` (sha256 `1ae5254d…e50e`).
  - `v3-bench` (299 МБ) — ранний раунд композиции V3.
  - `bench-sidecar3` **не существует** (описание в старом отчёте не подтверждается).
- **Не делать**: массовое удаление стендов, изменение монтирований, копирование целых
  runtime/home.
- **Новый candidate Сола**: `/home/jericho/.cache/FRW-SOL-V3-ASK-IDENTITY-20261110/project`,
  454 pinned файла / 36 863 427 байт, без копии runtime. Использован установкой и её
  `operator_entry`; сохраняется как действующая ссылка. Receipt-only тестовые стенды
  ребёнка удалены; старые доказательственные стенды и WAL/SHM не трогались.

## 7. Объём V3

Полный согласованный объём сохранён: **170 кейсов и 120 расширений форматов** с
согласованными операциями, вариантами, последовательностями и повторами. B00 — часть
объёма. **Объём не закрыт.** Реестры (`CASE-LEDGER.json`, `EXTENSION-OPERATION-LEDGER.json`)
не переписываются вместо исполнения.

## 8. Objective и критерий завершения

Objective **не меняется**: FRIDAY-RELEASE-V3 — довести установленную Friday до готовности
по согласованному V3. Критерий: на итоговом установленном составе подтверждены
обязательства V3, регрессия и восстановление и нет текущих обязательных
FAIL/BLOCKED/UNKNOWN/NOT_RUN. Исторические результаты сохраняются; необязательный
техдолг не добавляется.

Полномочия и решения владельца сохранены полностью. Новый бюджет ходов не назначался.
Исторический DSH goal **paused / disarmed**, rounds 0; сохранён без возобновления.
Новый native goal Сола **active** по директиве владельца от 10.11; readback и связь
с предшественником приведены в начале этого файла.

### Доказательства текущего продолжения

Каталог [`evidence/sol-20261110/`](evidence/sol-20261110/): `platform-admission.json`,
`dependency-probe.json`, `compression-diagnosis.json`, `admission-regression.json`,
`publication-offline.json`, `sidecar-installed.json`, `sidecar-installed-check.json`,
`saved-archive-assessment.json`, `retained-result-assessment.json`, `native-goal.json`.
В каждом различены source/install/runtime/user/формальный tester verdict и точные SHA.
Это текущий evidence overlay; старые runs, immutable ledgers и исторический goal snapshot
не переписывались. Полная приватная операция установки:
`/home/jericho/.cache/FRW-SOL-V3-ASK-IDENTITY-20261110/LIVE-OPERATION.json`.

Установка 09:20:16–09:22:09 МСК: запрос `dbffff0a…3152`, только один слой,
receipt `b93a34cf…fbf79`, source `1ae5254d…e50e`. Таймаут клиента `systemctl start`
45 секунд разрешён свежим readback active/running в том же запуске, без повторного start.
Реальный consumer завершился 0; deadline охватывает forward publication,
rollback не прерывается истечением бюджета. Счётчики двух профильных БД и quick_check
до/после совпали. Позднее узкая пользовательская квалификация
R71 завершена (см. актуальный срез и sidecar-live-root-review); старые187 install
факты относятся к09:22 и не выдаются за текущий188 receipt.

Текущие результаты добавлены в том же evidence overlay: TSV read/recall, P04 source/
publication/install/live, archive consumer/review/final188 reuse, post-power dependencies
и compression status deployment. Ближайший шаг указан в актуальном todo выше;
закрытые TSV/P04 запросы не повторять ради более удобной формальной оценки.

Полный объём и ближайшие безопасные работы разобраны в приватном
`/home/jericho/.dsh/tmp/sol-v3-obligations-20261110.md`: исходные 170/120, surviving
immutable ledgers и оригинальный reference ZIP. Отсутствующие cache-очереди не
восстанавливаются выдуманными sealed bytes; source-summary B253 не является dispatch grant.

## 9. Материалы

- `DSH-CORRECTION-REPORT-2026-11-10.md` — отчёт о коррекциях (a8bba32 → 7e219de → 476496a).
- `DSH-GOAL-SNAPSHOT-2026-11-10.json` — снимок goal с историей прежней цели.
- `SHA256SUMS` — контрольные суммы (224 записи, воспроизводимы из Git-коммита).
- `patches/hermes/bounded-current-ask-identity.patch` / `-manifest.json` — **новый слой**
  (preimage `1acfe925…b948` → after `1ae5254d…e50e`), готов к установке после регистрации
  в `LAYER_NAMES`.
- `check-fresh-admission-scope.py`, `check-layer-publication-composition.py`,
  `check-bounded-resume-sidecar.py` — проверочные скрипты.
- `DSH-RESUME-2026-11-09.md`, `DSH-RESUME-2026-11-08.md` — история, не рабочая инструкция.


<!-- Working continuation delta, not yet a new published commit: ARJ Unix-link genuine
producer source216files/2075319bytes fetched at pinned6af97465; every Git blob verified.
Private package FRW-SOL-V3-ARJ-LINKS-20261110. Two preparation-only failures preserved
(sandbox awk alternative, then make built-in cc); corrected explicit CC=gcc build-only
script after R73 ran prepare successfully, build missing generated msg_arj.h.
Explicit message generation succeeded; compile now stops on legacy implicit system_cmd
declaration. Logs/attempts1–4 preserved, all sandbox namespaces terminal. No ARJ fixture/
product call/system install yet. Stage/source in BUILD-STATE.json retained for next finite fix. -->
