# FRIDAY-RELEASE-V3 — единая точка входа для Сола (2026-11-10)

**Настоящий файл — единственная актуальная точка входа.** Он заменяет
`DSH-RESUME-2026-11-09.md` и `DSH-RESUME-2026-11-08.md` как рабочую инструкцию.
Оба старых файла сохранены как история; их инструкции по выбору home, переносу
данных и повторной подготовке профилей **не действуют**.

Дата: 2026-11-10, МСК. Передача: DSH-сессия → Сол (временное принятие лидерства).

## Действующее продолжение Сола — 10.11.2026, 17:28 МСК

Сол — временный lead/координатор/интегратор. Владелец разрешил разработку,
проверки, штатную установку и публикацию в существующий main, затем делегировал
выбор решений: [действующее решение](evidence/sol-20261110/owner-autonomy-and-p04-variant.json).
Вечерняя передача Астре — только по отдельной команде; её пока не было.

**Native goal** `FRIDAY-RELEASE-V3-CONTINUATION-2026-11-10` создан 09:04:04 МСК;
API `threadId` **`01a1c407-7f0e-7273-9fd0-6bd9dc09ce18`**, отдельный UUID API
не возвращает. Свежий `get_goal` на этом срезе подтвердил **active**, без собственного
лимита. Неизменённые objective/критерии и predecessor:
[SOL-GOAL-CONTINUATION-2026-11-10.json](SOL-GOAL-CONTINUATION-2026-11-10.json).
Старый DSH `goal-62933237-0a12-4223-a0ab-ebcaa126db76` и snapshot — история,
не возобновлялись. Полные **170 кейсов/120 расширений**, B00, операции, варианты,
последовательности, допустимые повторы, регрессия и восстановление обязательны.
Текущие обязательные FAIL/BLOCKED/UNKNOWN/NOT_RUN разрешаются по исходным критериям;
переписывание реестров не является исполнением. Различать отправку/эффект,
семантическую оценку, formal tester acceptance и основание следующего действия.

**Git / принадлежность.** Последний опубликованный и удалённо сверенный
`main = b856e9692ddfdd7e4d1faa14c3518c12babeb940`; 305 checksum entries проверены
по точным Git-байтам. Исходный `585f9cb9790a6182908db9ccdde263176ae39969`
не откатывался. Текущая следующая дельта описана здесь отдельно; точный SHA её
коммита сообщается после commit/push, без записи хеша коммита внутрь самого себя.
Три чужих изменения §1 сохранены и в собственные коммиты не включаются.

**Runtime сейчас: 193 слоя**, home из §2; единственный gateway
**280113/start2351085**, boot `d518758e-bce0-4bd5-89a1-fc4e113f0623`.
К сохранённым192 добавлен только `ordinary-direct-plain-cancel-after-source192`:
[установка193/receipt/marker/stamp/3DB/freshprocess](evidence/sol-20261110/c10-source193-installed.json),
SHA `b1b56ece9f3b1221f9ea168cce39a5eb5d20ab319c2cc9fd5d38b58da450bd84`.
Receipt `5b3df307158a944ba171e8e10cd26af48ecbbb1debf7be2d90e5919a00191978`,
input `3e5997f45c7286352a1f34f36e5330e28421126e30fa82a30a4593336847473a`.
Один stop192 → один publisher → freshstart193 в16:43:09 МСК; старые192 и все
17888 nontarget inventory entries сохранены, project466/15historical metadata differences.
До/после установки quick_checkOK и одинаковые счётчики: default30/2, dest196/2,
tester5350/5. Последующие R85/R86 — отдельные эффекты, не часть install proof.
Исторический marker.post_install_source_input остаётся прежним по его контракту;
текущие marker.input/receipt/stamp193 согласованы. Первоначальные ошибки Root-readback
(layername/историческийpointer/processcensus) сохранены, corrected reviewer того же
установленного результата принят без переустановки. История192:
[two-fix-installed](evidence/sol-20261110/two-fix-installed.json).

**Todo / завершённые содержательные обязательства:**

- [x] Площадка/nativegoal; повторного переезда нет. Admission generator585f9cb
  сохранён: независимые stdoutSHA/size, deterministic legacy two-exists race,
  63контроля; ordered actual predecessor+durable custody расширены до143.
- [x] Sidecar187 подключён и установлен единственным приращением:57publication
  и11installed controls; [R71 narrow live PASS](evidence/sol-20261110/sidecar-live-root-review.json).
  Reboot/resume/compaction/twoanchors/admittedstream guard реальны. Interruptedretry
  не выполнен; старый matcher тоже уникален на фактических metadata, red→green не заявлен.
- [x] После poweroutage сохранённые результаты приняты без повторов. Primary
  `.195:30000` и embeddings `.195:8002` authenticated200 и реальное вычисление,
  вектор2560; endpoints/models/config не менялись. Старый compressor503/status-fetch
  UNKNOWN сохранён. [NJSstatusfix установлен](evidence/sol-20261110/compression-status-deployed.json),
  [R75 настоящий configuredsummary безfallback](evidence/sol-20261110/compression-saved-user-path-root-review.json)
  подтверждён по сохранённым фактам; physicalbackend/HTTPstatus/причина503 не установлены.
- [x] P04 guidance188 установлен/граф188 реально reconstructed17 888SHA/size/mode.
  Новый одобренный PDF R72 sent2636→2638:
  [narrow original oracle/custodyPASS](evidence/sol-20261110/p04-live-root-review.json).
  OCR V/Q и неполнаясумма — отдельный fidelitygap; старыйFAIL не переписан.
- [x] TSV R70 firstREAD2630→2632 и R71 ordinaryRECALL2633→2635:
  [READ](evidence/sol-20261110/tsv-read-root-review.json),
  [RECALL](evidence/sol-20261110/tsv-recall-root-review.json) semantic/custodyPASS.
  Оба original63B источника сохранены; отдельная первая F03 теперь R79 ниже.
- [x] RTF R73 firstREAD2639→2641, R74 RECALL2642→2644, R75 firstEDIT2645→2647:
  [READ](evidence/sol-20261110/rtf-read-root-review.json),
  [RECALL](evidence/sol-20261110/rtf-recall-root-review.json),
  [EDIT](evidence/sol-20261110/rtf-edit-root-review.json) semantic/custodyPASS.
  Версия1→2, остальные байты/Arial11 сохранены; original261B/new268B8c3ff6df…d32e2.
  Лишние ошибочные read_file(content/format) сохранены, не скрыты и не повторены.
- [x] Guard таких write-only аргументов теперь установлен191:
  [source/review/baseline2+30controls](evidence/sol-20261110/read-mutation-argument-source-root-review.json).
  `tools/file_tools.py` postimage760a49c4…8237a; отказ до pathprobe/read,
  реальные validreadargs/writepath сохранены. R75 не повторять радиqualfix.
- [x] Archive failure provenance189 и R76 once2648→text2652/new7z2653/newalternateZIP2654:
  [narrow provenance/deliveryPASS, userreportPARTIAL](evidence/sol-20261110/archive-provenance-live-root-review.json).
  Native5228 real document_already_exists, oldZIP не выдан как новый; оба новых
  контейнера дают точные4payload. Не названы targets — это подтверждённый textgap.
- [x] Именованный truthfulstatus исправлен и установлен192:
  [one-method source/review](evidence/sol-20261110/archive-named-status-source-root-review.json),
  5actual190controls+20indepdisplayprobes; postimage9550e882…d961.
  Только authenticatedrelative target + selected verifiedcurrentartifacts; unsafe
  displaylabels genericfallback, без MEDIA/link directive. Live192ветка теперь отдельно
  квалифицирована R81 ниже; старый R76PARTIAL не переписан.
- [x] Combined190→192: [97actualpublisher/parser/negative/rollback controls](evidence/sol-20261110/two-fix-publication-offline.json),
  independentreviewPASS; project464/old460pins/190prefix/15metadata differences сохранены.
  Доказаны stale-requestpreflight и in-processrollback при solewriter/quiescenthome;
  concurrentCAS/perrename recheck/crash/powerlossatomicity не заявляются.
- [x] Genuine ARJ ID55 symlink/hardlink [4actual188observations](evidence/sol-20261110/arj-genuine-links-root-review.json).
  ARJ-native Unix types fix190: [2baselineRED/33controls/1536type+6profile](evidence/sol-20261110/arj-unix-mode-source-root-review.json),
  [76publication controls](evidence/sol-20261110/arj190-publication-offline.json),
  [190install history](evidence/sol-20261110/arj190-installed.json).
  Первый190publisherentry без HERMES_HOME отказал доclock/intent, затем ровноодна
  исправленнаяenvпубликация; исходнаяошибка/4fixedpins сохранены.
- [x] ARJ R77 firstEXTRACT/READ once2655→17Bregular.txt2657:
  [actualnativeextract/read/payload/fullcustodyPASS](evidence/sol-20261110/arj-first-user-root-review.json).
  GenuineUnix152Bfa39…69e0 неизменён, output0700/0600/nlink1; compaction5243 и
  R76toolcopies5248–5250 не новыеwriteeffects. R78 ordinaryRECALL once2658→2660,
  closed14:43:47: [имя/tail/no tools/fullcustodyPASS](evidence/sol-20261110/arj-ordinary-recall-root-review.json),
  native5262–5263. ARJCREATE/edit/fullmixedA02/A13A14 этим не приняты.
- [x] Archive scoped controls:18consumer+17checker; genuineLHA/RARexpandedlimits,
  RAR5/LHA bounds, ZIP/TAR128/129entries16/17depth, LHA7outputphase nativecancel и
  prestopnegative приняты отдельно, [финальный188reuse](evidence/sol-20261110/archive-final188-root-review.json),
  [bounds](evidence/sol-20261110/archive-new-boundaries-root-review.json),
  [entry/depth](evidence/sol-20261110/archive-entry-depth-root-review.json),
  [nativecut](evidence/sol-20261110/archive-native-cancel-root-review.json).
  [192two-regular-member7z](evidence/sol-20261110/seven-regularized-source-inputs-root-review.json)
  теперь actualPASS; это не genuineencodedhardlinknegative.
  [Сверка исходного conditionalcontract](evidence/sol-20261110/conditional-archive-links-root-review.json)
  принята только для reviewednative7z и UnixLHA0/1/2: документированного hardlinktarget
  в них нет; universalimpossibility/N_A/productPASS не выводятся. Два исходных
  finitecaseJSON отсутствуют, SHA/pointers сохранены, rows не реконструированы.
  A13/A14 исходноOFFLINE;
  wholecases, CPU-loop/gatewaycancel и другие unexecutedvariants не приняты.
- [x] Saved-only без пересылок: D07 все8изменений+boilerplate;
  [M11 четыре факта/custody](evidence/sol-20261110/m11-saved-root-review.json),
  [A03 source107 genuine16payloadroundtrip](evidence/sol-20261110/a03-saved-roundtrip-root-review.json),
  [M04 originalMayak/delivered1768](evidence/sol-20261110/m04-saved-root-review.json).
  M11PARTIAL/full180false и M04missingoldUNBOUND/fulllegacyverifier сохраняются.
- [x] TSV R79 firstF03 once2661→new63B2663, closed15:40:10:
  [exactonebyte1→2/allotherbytes/bothoriginals/nativefullread/write/readback/fullcustodyPASS](evidence/sol-20261110/tsv-edit-root-review.json).
  Один tool_call(text_edit) schema-refusal до invocation сохранён; затем actualgeneric
  UTF8newwrite, не специализированныйTSVeditor. WholeF03/complexfidelity не приняты.
- [x] ODS R80 firstF01 once2664→text2666, closed15:47:21:
  [actualnativeODSread/sixcells/sheet/tail/fullcustodyPASS](evidence/sol-20261110/ods-read-root-review.json).
  Реальные938B/R31source не пересозданы; actual5277→5278 nativecells6/partialfalse,
  tailДанные!A3:B3=Версия/1numeric, originalsunchanged. Layout/formulas/recall/edit
  не заявлены; ни новых артефактов, ни productwritecalls.
- [x] R81 новыйTAR FIRSTconversioncollision once2667→new7z2669, closed15:55:44:
  [actual192typedfailure/namedreport/currentartifact/fullcustodyPASS](evidence/sol-20261110/tar-first-collision-root-review.json).
  Native5295document_already_exists, old476B7z/coreZIP253028B fullidentity неизменны.
  Durable5298/actualcaption называет отказавшийtarget и новыйalternative273B84da6104…f6b4;
  systemlibarchive независимо в памяти проверил точные2пути/101Bpayload, без распаковки
  или пересоздания. Originalexacttarget честно REFUSED, wholeA03 не принят.
  Compaction5283/ODS5277–5279 copies5284–5286 и currentcopies5287–5289 коррелированы;
  это не повторныеисполнения.
- [x] ODT R82 firstF03 once2670→native1255B2672, closed16:09:48:
  [nativeone-date/sourcepreservation/fullcustodyPASS](evidence/sol-20261110/odt-edit-root-review.json).
  Срок22→23October, original1208Be1e22d35…2cd5 fullidentity неизменён;18paragraphs,
  17unselectedparagraphstructures/styles, всеXMLbytesвне selectedp и othermemberpayloads
  точны. 5single ODFtext:s заменяют эквивалентныепространства только selectedp; strict
  XMLliteralFAIL сохранён отдельно, originalF03nativefidelity принят Root ДО admission
  с independentchecker87d2f2f0…8fbc1. НикакойGUIrender/complexfidelity приёмки.
  Genuinecompaction5306/5301–5305 copies5307–5311, wrongcontenttype до invocation
  сохранены; модель сама сериализовалаJSON, actualwrite один5319.
- [ ] R83 firstCSVF03 завершён16:13:44 exit2 **UNKNOWN_SEND**, однаdispatch,
  TRANSPORT_URL_FAILURE/HTTP_REQUEST_OR_HEADERS, безACK/sentid:
  [исходныйUNKNOWN/сверка](evidence/sol-20261110/csv-first-edit-unknown-root-review.json).
  [Один readonly TEXT quarantine](evidence/sol-20261110/csv-text-unknown-quarantine-root-review.json)
  затем реально выполнен на193: обаcanonical locks, fresh120s READclock, ровноодин
  currentcursor getUpdates(timeout0,limit20), EMPTY0/unsaturated. Cursor/R83raw
  неизменны; send/ACK/download/grade отсутствуют. EMPTY не доказывает unsent;
  R83UNKNOWN сохранён, эту quarantine и отправку не повторять. Динамические45
  unresolved/3UNKNOWN сохранены, исходные44/2 не очищались.
- [x] R84 ODS ordinaryRECALL once2673→text2675, closed16:34:31, actual192:
  [имя/sheet/все6фактов/tail/fullcustodyPASS](evidence/sol-20261110/ods-ordinary-recall-root-review.json).
  5 настоящих session_search, свой historicalnative5285 копирует5278/R80; это
  retrieval-backed recall, не pure-memory. Compaction5326/5340 и прежние ODT/search
  копии коррелированы без новых writeeffects; все4original938B sourcepins неизменны.
- [x] Plain ordinary user «Стоп, отменяю.» подключён и установлен193:
  [37baseline/44candidate actualwholemodule controls, publisher96+5,
  receiver28/real11refs/independentreview](evidence/sol-20261110/c10-native-publication-root-review.json).
  ACL/principal/control origin/quoted/forwarded/internal/media/group fences сохранены.
  Offline native cancel не заменяет live; фактический R85 ниже остаётся PARTIAL.
- [ ] R85 originalC10 один START2676/native5351 и обычный STOP2678→reply2679:
  [состоявшаяся остановка, ошибка ответа, несостоявшийся Question](evidence/sol-20261110/c10-original-partial-root-review.json).
  STOP-INTENT достоверно видел занятое поколение1/token/lease этого START; после
  ответа nativegeneration2 inactive, без lease/token/queue/pending/delegated/web/terminal.
  Реальный текст: Englishnative Stopped плюс JSON control_unavailable. Receiver
  отказал на strictRussian-only ACK; суффикс — отдельный настоящий productFAIL.
  Последующий Question не имеет intent/ACK, NOT_RUN. CanonicalSTOPPED/его старый
  product_cancelled marker сохранены; Root отдельно доказал native effect.
  Полный C10/B00 не принят, physicalbackend cessation и full latefence window
  не доказаны. PID291584 завершён exit1, original600deadline17:16:27 истёк безreset.
  START/STOP/старый2455 не повторять; будущий missingQuestiontail требует собственного
  конкретного основания и конечной операции. Source/offline repair — отдельный пакет.
- [x] R86 genuinelyfirst ODS F03 once2680→native949B2684, closed17:26:52 exit0:
  [подготовка/Root source review](evidence/sol-20261110/ods-edit-preparation-root-review.json),
  [фактическая правка/независимая fidelity/fullraw custodyPASS](evidence/sol-20261110/ods-edit-root-review.json).
  Actual193 native5354/5355 fulloriginalread →5358/5359 spreadsheet_edit/CAS/create-only
  →5360/5361 fullnewread →5362 durablefinal/actualcaption. Новый949B5503cc95…fe6d:
  Данные!B3 numeric1→2, все5другихcells/полныйостальнойXML/memberpayloads и strict
  serialization/membermetadata PASS; все4original938B sourcepins fullidentity неизменны.
  Один wrongobjectcontent tool_call schema-refusal до writeinvocation сохранён,
  модель сериализовалаJSON и выполнила один настоящий write. Ни повторной отправки,
  ни пересоздания готовогофайла. Formal NOT_ESTABLISHED/RECEIVED_UNGRADED отдельно.
  Genuine simplecase не доказывает formulas/styles/multisheet/locale/stringIDs/updatejoin
  или wholeF03. Silent selectedXMLcommentloss193FAIL сохранён; source-only typedrefusal
  candidate139ba0f7…ca63 NOT_INSTALLED и не является comment-preserving featurePASS.
- [ ] Остальной полный originalscope/formatvariants/B00/regression/recovery открыт.
  Локальные C10/CSV ограничения не блокируют независимые допустимые обязательства.

**Операции / исполнители.** Root/Sol единолично владеет runtime/admission/live/Git.
R79/R80/R81/R82/R84 закрыты с узкими semantic/custodyPASS; formal tester во всех
новых узких прогонах NOT_ESTABLISHED/RECEIVED_UNGRADED. R83 UNKNOWN и его один
READquarantine закрыты без разрешения resend. R85 закрыт PARTIAL/nativeStopknown,
reportFAIL/QuestionNOTRUN; исходные clock/каноническийrun не переписаны.
R86 `f03-ods-edit-preserve-01-20261110` закрыт17:26:52 exit0, актор завершён;
private `/home/jericho/.cache/FRW-SOL-V3-ODS-FIRST-NATIVE-EDIT-20261110/ROOT-ods-LIVE-RUN.json`.
Root сохраняет исходные R31/R80/R84 факты, не повторяет creator/read/recall.
`ods_first_native_edit` завершён/Root принят: RESULTb729728d…33e5, source193simple
маршрут уже работоспособен; source-only commentguard139ba0f7…ca63 отдельно.
`c10_live_stop_reporting_repair` — finite SOURCE/OFFLINE, private
`/home/jericho/.cache/FRW-SOL-V3-C10-LIVE-STOP-REPORT-REPAIR-20261110/RESULT.json`.
Диагностика сообщает retained A0 runtime480 против obsolete consumer cap120;
окончательный пакет/review ещё не принят Root. Подчинённые reviewers принадлежат
этому назначению; живых эффектов им не разрешено. Попытка дополнительного finite
readonly next-format child17:23 отклонена native `agent thread limit reached`;
контролирующий обвес не создаётся, Root продолжает независимую работу.
Остальные finite дети завершены и не изображаются действующими.

Ближайшая граница: опубликовать установленный193 и фактические ODT/ODS/CSVUNKNOWN/C10PARTIAL
свидетельства одним содержательным срезом. Затем принять connected C10 repair/review,
интегрировать исправление через существующий pluginconsumer и отдельно выбрать
конечную будущую missingQuestiontail/следующее genuinelymissing original obligation.
Ошибка проверяющего оценивает тот же файл, не вызывает новую генерацию/отправку. R42/R43, UNKNOWN_SEND, неизвестные P01/Q02 и исторический S11
защищены от повторов. Новый run-id/допуск/модель/перезапуск/исправленный состав сами
повтора не разрешают. Nativegoal active подтверждён повторным get_goal; критерии
неизменны, вечерней передачи не было. После опубликованного b856e969…b940 здесь
ведётся следующий содержательный срез; точный SHA сообщается после commit/push,
без selfhash. SHA256SUMS305 относится к предыдущим точным Git-байтам, перед новым
commit обновляется по index bytes. Постоянные сервисы сохраняются исправными.

## 0. Состояние разработки

| Предмет | Факт |
|---|---|
| Репозиторий | `/home/jericho/jericho/Friday_rework`, ветка `main` |
| Исходный HEAD продолжения | `585f9cb9790a6182908db9ccdde263176ae39969` (сверка 10.11, 09:04 МСК); прежний `476496a` — исторический |
| Последний опубликованный HEAD/origin/main | `b856e9692ddfdd7e4d1faa14c3518c12babeb940`; следующая рабочая дельта указана выше |
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

## 2. Обслуживаемый runtime (установка193, 10.11.2026 16:44 МСК; новые userоперации отдельно выше)

| Предмет | Факт |
|---|---|
| Home | `/home/jericho/jericho/Friday_rework/.runtime/friday-normal-both-workers-frw032` |
| Состав | **193 слоя**; к192 добавлен только `ordinary-direct-plain-cancel-after-source192`. Receipt `5b3df307…1978`; input `3e5997f4…473a`; stamp/marker согласованы, upstream/base прежние |
| Gateway | `hermes-gateway-1b7e7667.service` active/running, **MainPID280113**, ExecMainStartTimestamp 2026-11-10 16:43:09 МСК, NRestarts 0 |
| Состояние gateway | `gateway_state.json`: pid280113, start_time **2351085**, `gateway_state: running`, Telegram `connected`, `served_profiles = [default, dest_telegram, telegram-bot-8812646969]`; текущая активность определяется по единственному Root user-run выше |
| Boot | `d518758e-bce0-4bd5-89a1-fc4e113f0623`, загрузка 2026-11-10 10:11:19 МСК; реальный power outage |
| Приёмников | **один** (процесс280113, проверено по фактической executable/bootstrap identity) |
| Docker | В этом проходе контейнеры не запускались; прежний inactive-срез не выдаётся за новую проверку A0 |
| База `dest_telegram` | 196 сообщений / 2 сессии, `quick_check ok`, счётчики до/после установки сохранены |
| База `telegram-bot-8812646969` | 5350 сообщений / 5 сессий до/после установки193; `quick_check ok`, неизменны. Последующие R85/R86 — отдельные новые эффекты; 17:24 readonly quick_check всех3БД OK, tester5364/5 после единственного R86 (consumer closed17:26:52) |
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
  (в checkpoint) и `/home/jericho/.cache/FRW-KIMI-FMT-20261108/INDEPENDENT-AUTHORITY-R29…R84.json`.
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
