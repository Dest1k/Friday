# Presentation reading V-01 — accepted initial result

Date: 2026-11-01. Installed version: **Source116**, test consumer **tester393**. This case used the installed version; it required no new installation.

A real PPTX was uploaded and sent once through Telegram. One text reply was observed, the full 180-second capture completed, and the finite run closed normally with resource cleanup accepted (`resource0`). Root separately accepted the reply's semantics: **PASS**.

The exact request was:

> Сводка по презентации: выводы, цифры на слайдах, отдельно заметки докладчика.

The reply correctly reported all five slide titles, the three cached chart values, all four table rows with leading-zero order IDs, and the computed sum **10101.2**. It identified the sum as arithmetic rather than a source cell, separated technical speaker notes, and stated that formatting/images/master styles were unchecked and the embedded chart workbook was not recalculated. The source data are synthetic.

The actual reply is in [response-redacted.txt](response-redacted.txt). Exactly **one redaction** replaces a technical synthetic marker from the notes. The rest of the response is preserved. [status.json](status.json) records the observed raw text hash and the distinct published redacted text hash.

The canonical tester records still say `RECEIVED_UNGRADED` for the reply, `NOT_ESTABLISHED` for delivery/overall acceptance, and `NOT_VERIFIED` for artifact acceptance. Root's semantic PASS is a separate recorded review; these tester fields were left unchanged.

The short continuation in the same conversation is **NOT_SENT**. V-02 Office/PDF remains **NOT_ACCEPTED**, and the known Office edit/save preservation **FAIL** remains open ([retained diagnostic](../presentation-office-diagnostic/STATUS.json)). V-01 establishes only the initial presentation-reading milestone. It does not establish the full user journey, DSH/A0 completion, or overall mission completion.

Earlier archive exposure is known, so this result carries no cold benchmark claim. The original PPTX and private operational evidence are not included.
