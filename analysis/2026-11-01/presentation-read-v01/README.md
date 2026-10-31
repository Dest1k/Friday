# Presentation reading V-01 — accepted initial result and continuation

Date: 2026-11-01. Installed version: **Source116**, test consumer **tester393**. Both cases used the installed version; neither required a new installation.

A real PPTX was uploaded and sent once through Telegram. One text reply was observed, the full 180-second capture completed, and the finite run closed normally with resource cleanup accepted (`resource0`). Root separately accepted the reply's semantics: **PASS**.

The initial request was:

> Сводка по презентации: выводы, цифры на слайдах, отдельно заметки докладчика.

The reply correctly reported all five slide titles, the three cached chart values, all four table rows with leading-zero order IDs, and the computed sum **10101.2**. It identified the sum as arithmetic rather than a source cell, separated technical speaker notes, and stated that formatting/images/master styles were unchecked and the embedded chart workbook was not recalculated. The source data are synthetic.

The initial reply is in [response-redacted.txt](response-redacted.txt), with its previously published bytes unchanged. Exactly **one redaction** replaces a technical synthetic marker from the notes. The rest of the response is preserved. [status.json](status.json) records the distinct raw and redacted text hashes.

The short continuation was sent once in the same conversation, without reuploading the PPTX:

> На каком слайде показаны продажи по артикулам и какое значение у A01?

The [exact followup reply](followup-response.txt) correctly answered **slide 3, A01 = 3601.5**, retained the cached-data/no-recalculation limitation, and gave the correct B02/C03 values and total. Root accepted its semantics and operational closure at **02:11 MSK**. The full 180-second observation completed; origin to finite termination took **202.433261257 seconds**. Termination was normal, the owned process was reaped, resource cleanup passed, and permanent services remained running. No new stop attempt or original-effect replay occurred.

For both replies, canonical tester records still say `RECEIVED_UNGRADED`, with delivery/overall acceptance `NOT_ESTABLISHED` and artifact acceptance `NOT_VERIFIED`. The continuation record's historical `original_outcome=UNKNOWN` also remains unchanged. Root's semantic acceptance and operational closure are separate recorded reviews.

V-02 creation/editing/PDF remains **NOT_ACCEPTED**, and the known Office edit/save preservation **FAIL** remains open ([retained diagnostic](../presentation-office-diagnostic/STATUS.json)). V-01 establishes presentation reading and this short continuation only. It does not establish the full user journey, DSH/A0 completion, or overall mission completion.

Earlier archive exposure is known, so neither result carries a cold benchmark claim. The continuation does not establish a retrieval mechanism. The original PPTX and private operational evidence are not included.
