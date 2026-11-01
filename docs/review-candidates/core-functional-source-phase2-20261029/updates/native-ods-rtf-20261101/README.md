Native ODS and RTF source additions

This reviewed source adds native ODS reading, typed creation, exact cell edits, text-key table joins and revision-based merges. Joins and merges create new plain tables and do not preserve source formatting. RTF gains bounded body/table reading, plain or structured creation, and exact text edits. Source changes, ambiguous or unsupported content, reused destinations and cancellation are checked through the existing workspace publication path.

Apply `native-ods-rtf.patch` to the accepted Source121 native source. The separate `fullfresh-prerequisites.patch` corrects only project patch dependency metadata; it does not change native implementation bytes. Full fresh composition produced 148 layers and 17,745 files equal to the incremental target. The historical incremental receipt remains preserved separately.

The manifest supplies exact before/after hashes. Local implementation and independent checks are recorded in `OBSERVATIONS.json`; repeated checks of the same bytes are listed separately. These are source and local-consumer results. Installation, Office, Telegram, visual and user acceptance remain pending.
