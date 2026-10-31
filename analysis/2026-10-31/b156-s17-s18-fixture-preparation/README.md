# S17 correction-only reuse and S18 workbook fixture preparation

This source package makes the synthetic workbook preparation reproducible without Friday, Telegram, Office, a model, or third-party Python packages. It is preparation evidence. S18 runtime execution, returned-file reopen, visual/formula-engine behavior, delivery, and full-case acceptance are unestablished. No operation is authorized by these files.

The S17 correction-only comparison and its short continuation were already delivered and semantically accepted as a closed subset. That work is reuse only: no new comparison, upload, continuation, or retry is needed. Full180 and full-case qualification remain false; the original receiver refusal and presentation limitation remain recorded privately. The synthetic fixture pair changes only `Orders!C3` (3 to 4) and `Orders!F3` (1 to 2), adds/deletes no rows, and preserves the formula sources and text identifiers. Decimal arithmetic gives 10101.20 to 10601.10 RUB, a 499.90 difference; this is separate from an observed spreadsheet-engine recalculation.

The existing rich synthetic workbook contains a linked chart, three defined names and a real table, but lacks data validation. The preparation inserts one whole-number rule (1 through 100) on `Orders!C2:C5`. Only `xl/worksheets/sheet1.xml` changes; every other ZIP member is retained byte for byte. The resulting fixture has SHA256 `4038289a6e89c86da8fd547705f9eb98ffbf48566e4dc22652768e405f7dec0d` in the checked Python environment.

Run the portable local controls from this directory:

```sh
python3 -B -m unittest discover -s tests -v
```

To reproduce the S18 input and three original negative-control fixtures:

```sh
python3 -B source/prepare_fixture.py \
  --rich fixtures/source/orders_rich_table.xlsx \
  --correction fixtures/source/orders_correction_only.xlsx \
  --fixture build/orders_s18_validation.xlsx \
  --negative-dir build/negative_fixtures
```

`build/` is disposable local output. Exact ZIP file hashes can depend on Python/compression versions; the tests also check the exact member insertion and all unaffected member bytes. The three input XLSX files and two JSON seeds are synthetic order data, retained to make the preparation independent of private workspaces. Their origin and metadata were inspected; they are neither received user artifacts nor model answers.

The structural checker follows worksheet-to-drawing-to-chart and worksheet-to-table relationships. Orphan ZIP parts do not count as retained features. Defined names retain target and semantic sheet scope; merely reordering sheets must remain accepted. These controls apply to the known synthetic fixture and are not a general XLSX conformance validator. Static XML checks do not establish successful consumer reopen or visual preservation.

The ordinary document tester source supports one document per ordinary step. The selected serial route uses its predecessor; a restricted nonserial fresh-upload route also exists. No list-valued two-document adapter is introduced, and no S17 replay is prepared. Future S18 admission, source/process identity, permissions, custody, clocks, resources and returned-file paths must be established separately by the integration owner.

Only the XLSX and a natural request belong in any separately authorized user task. Checker source, expected values, private evidence and fixture-preparation records are not user-task attachments. `PUBLIC_REQUESTS.json` preserves neutral case descriptions without transport identifiers or private oracle files.

This export adapts reusable source to portable public paths and omits private history/ABI main routines. Original B156 checks and reviewer controls are historical observations, not automatic validation of these adapted bytes. See `OBSERVATIONS.json` for checks actually performed on this public candidate. No source installation, service or product state changes are included.

The optional `source/assess_received_s18.py` is a narrow source-origin structural assessor for a future separately authorized derivative of this exact synthetic S18 fixture. Its helper bytes are unchanged from the independently accepted source-only implementation. It compares original cells and formula sources, validation coverage, scoped names, and linked chart/table structures; it does not establish actual received-file custody, runtime identity, consumer/Office reopen, recalculation, validation enforcement, visual preservation or semantic user acceptance. Cached results are ignored. Unsupported projections remain explicit, and additional cells/features require review rather than a blanket rejection.

Before any future user task, explicitly declare the natural request, including this edit:

> В приложенной книге измени количество в Orders!C3 с 3 на 4. Верни исправленную книгу, сохрани остальные исходные данные и формулы, проверку данных, именованные диапазоны, диаграмму и таблицу. Кратко сообщи, что удалось сохранить и что не поддерживается.

Only the workbook and natural request belong in that user task: do not attach expected totals, oracle files, checker source, synthetic mutants or acceptance declarations. No task is sent or authorized by this documentation.

After the integration owner separately establishes custody and all operational bindings, the static CLI accepts caller-supplied paths:

```sh
python3 -B source/assess_received_s18.py \
  --source build/orders_s18_validation.xlsx \
  --received path/to/returned.xlsx
```

The source must have SHA256 `4038289a6e89c86da8fd547705f9eb98ffbf48566e4dc22652768e405f7dec0d`. Exit zero means a JSON assessment was produced, including reports requiring review; it never means Office or user acceptance. Exit two means `UNKNOWN`. Read every status and gap. JSON includes caller-supplied paths and workbook-derived facts; keep actual local reports private as appropriate.

The added portable controls generate the known source through the existing public `prepare_fixture.py`, create only temporary synthetic mutants, and remove them after the test run. They require no new binary fixture and run with the existing unittest command above. `RECEIVED_ASSESSOR_OBSERVATIONS.json` records checks actually executed on these adapted test bytes; historical source reviews are reused for the unchanged helper and do not establish any product/runtime result.
