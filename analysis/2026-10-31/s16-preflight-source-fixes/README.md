# S16 preflight source fixes

This completed source-only block preserves four accepted one-line changes:

- Route runtime validation to `self.binding.current.b.read`, the existing descriptor-aware reader.
- Admit owner-only `0700` in the immutable source reader and static custody capture predicates. Existing `0400`, `0600`, `0644`, and `0664` handling and owner, path, link, identity, hash, and parent checks remain unchanged. Mutable readers are unchanged.
- Compare seed memory with the exact `path`/`sha256`/`identity` projection used by the real `Current.bind_predecessor`; preserve baseline metadata and `Current.leaf` checks.

The four patches use logical filenames independent of any checkout or installation path. Each has one replacement and three context lines on each side. The manifest records the accepted full before/after source hashes; it does not contain those full private sources. These fragments are publication material, not an installation recipe.

Retained source checks are reported separately and were not rerun for publication:

| Delta | Source checks | Root independent checks |
| --- | ---: | ---: |
| Runtime callback | 19 | 8 |
| Immutable source custody (both predicates, P6) | 61 | 26 |
| Seed memory projection | 17 | 15 |

These counts describe their original scopes, not a combined suite or runtime acceptance. Unchanged P5 and 315-check evidence was reused without rerunning it. This preparation did not reinstall, requalify, or reseal history and did not create new tests.

At the final-preparation snapshot on 2026-10-31, two historical pre-admission failures were closed with zero admission/send effects; their original failures and closed operations remain preserved. The current actual S16 attempt sent once, and its owned harness process was reaped with exit code 2. Canonical receive stopped after partial captures; the full 180-second observation window was not confirmed. The first local native-message SQL cursor comparison refused while lease equality passed; the original mutation and refusal cause remain UNKNOWN. A later cleanup resource-tracking native RPC `TimeoutError` is separate and does not establish the cause of the earlier refusal. The model result and product semantic result remain UNKNOWN; this harness outcome is not a product semantic FAIL. No resend or replay occurred. A later finite, read-only check accepted operational resource closure after correcting a checker that compared message identifiers from different Telegram bots. Native input authentication, original ownership, route, generation, single-send and canonical custody checks remained in force; the checker delta passed 24 reviewer and 15 Root independent controls. The same original uncapped baseline resumed with its counters preserved. This resource closure does not complete the original receive window. The saved native response and hash-linked local files were also inspected: it emitted two artifacts against an exactly-one contract; local CSV parsing preserved the source table, while TSV parsing split a multiline comment. Authenticated recipient files and consumer safety remain unverified, so no whole-case semantic result is granted. Installed Source114 remains unchanged. These four fixes are accepted only in the owned harness source; no runtime, semantic, or full release PASS is claimed.

Publication checks: accepted source and delta hashes matched; each seven-line before/after fragment matched its accepted source; exact application was checked in memory against only that seven-line before-image. Diff bodies and AFTER bytes were preserved, with only logical diff headers changed. Added-line whitespace and the publication file set were checked. The output excludes private paths, usernames, chat/session identifiers, request/plan/ownership data, credentials, raw handoffs, logs, and private evidence. `SHA256SUMS` covers this README, the manifest, and all four patches; the manifest lists the other payload hashes and accepted source hashes.
