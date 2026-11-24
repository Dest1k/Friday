# Separate TrueConf Tester

This package runs the approved ordinary direct-chat document and exact-text continuation. It uses the TrueConf Connector, the reviewed Tester receipt and observation code, and the ordinary document checks extracted from the stock verifier. The configuration example is disabled.

## Install or use as an import

The prepared `friday_trueconf_tester/` directory is a self-contained Python source package apart from the dependencies in `requirements.txt`. Use a Linux Python 3.11+ environment with the pinned dependencies. Copy that directory to an owner-controlled installation location or use the prepared directory. Add its containing directory to the Python import path, or start Python from that containing directory. No installer or service activation is needed.

The CLI takes an explicit operation and config path.

```bash
python3 -m friday_trueconf_tester check --config "$TESTER_CONFIG"
python3 -m friday_trueconf_tester fresh --config "$TESTER_CONFIG"
python3 -m friday_trueconf_tester resume --config "$TESTER_CONFIG"
```

The programmatic seam is `await friday_trueconf_tester.entrypoint.execute(mode, config_path)`. The CLI prints a state and CORE credit. Exit 0 means check completed or the local observation matched, 2 is a refusal, 3 is held or incomplete, 4 is outbound `UNKNOWN`, and 130 is interruption. The journal carries the full local evidence. Execution uses the packaged observer and Connector. The stock Telegram runner and gateway are outside this entry's execution path.

The package includes its verifier module. To reproduce the source using the patched stock verifier supplied by the owner, run this from the package root.

```bash
python3 -B packaging/extract_observer.py "$PATCHED_STOCK_OBSERVER" > stock-observer.rebuilt.py
cmp stock-observer.rebuilt.py friday_trueconf_tester/_stock_observer.py
```

The input and output SHA-256 digests live in `packaging/OBSERVER-PINS.json`. The portable module keeps the stock document input, byte verification, custody, and ordinary plan checks used by this scenario. The operator supplies the approved scenario plan and its pinned input document. Recovery uses the Linux boot identifier and the monotonic clock.

## Configure and authorize

Start with `tester.config.example.json`, mode 0600 under a real Tester-owned mode 0700 directory. Keep plan, credential and optional CA PEM files as distinct mode 0600 leaves in that directory. The state directory is a separate mode 0700 leaf. The existing scenario's pinned absolute input document must be inside the Tester directory and outside state. Copying the document to a new inode requires provisioning its matching stock `input_stat` and SHA-256 in the approved plan. For the supported run, phase 1 sends one document and expects its exact bytes, MIME, name and caption. Phase 2 sends one native text reply and expects exactly one text continuation. The stock verifier enforces the existing scenario schema.

Pin the canonical HTTPS origin, exact Tester account, exact Product account and exact ordinary P2P chat ID in the protected config. Provision a dedicated Tester account with ordinary rights and an exclusive Tester session. The operator must independently confirm the chat ID belongs to the intended Tester–Product pair before enabling. Connector responses verify the authenticated Tester ID, origin certificate and direct-chat ID/type. The server read used here gives no independent proof of the Product membership mapping before upload. Incoming observations still require the exact configured Product sender. [TrueConf authentication](https://trueconf.ru/docs/chatbot-connector/ru/connect-and-auth/) · [Chat reads](https://trueconf.ru/docs/chatbot-connector/ru/chats/)

Use a separate Tester credential manifest with keys `schema`, `origin`, `tester_user_id`, `username`, and `password`. The schema is `friday.trueconf-tester.credentials.v1`. Bind the explicit manifest to the same canonical origin and exact Tester account. `ca_file: null` uses the interpreter's system trust. A configured PEM supplies the trust anchors for HTTP and WSS. Certificate and hostname checks apply in either case. This CLI supports the documented Tester password grant. Where password grant is unavailable, a separate authorized credential integration is required. [TrueConf authentication](https://trueconf.ru/docs/chatbot-connector/ru/connect-and-auth/)

Enable the config only in an independently approved cutover. The example uses an invalid-domain origin and is disabled. Disabled `check` opens no credential, state directory or connection. Enabled `check` verifies local file protections, plan, input and trust configuration without reading credential contents or opening a connection. A successful check is local readiness only.

## Fresh and resumed observation

- `fresh` authenticates without unread replay in a finite startup window. It uses the approved observer's original deadline after authentication. An existing journal or staged intent refuses a fresh operation. Each approved phase records its send intent and submits once. The Tester validates the scoped native response and retains verified bytes and observed receipt before acknowledging the notification.
- `resume` opens only an exact, acknowledged interrupted observation under its saved same-boot cutoff and remaining budget. It authenticates with unread replay and issues no sends. A matched resumed document can leave its unsent continuation held for a separate decision. Old `UNKNOWN` and `SEND_INTENT` remain protected. The operation closes its own Connector session.
- The wire fixture covers the document and continuation sequence, same-account and configuration refusals, and a fresh process resuming observation over verified HTTPS/WSS. Real Bridge behavior and full backlog replay remain open. The published unread flag operates on at most 1,000 unread messages and supplies no cursor, complete-backlog marker or lost-send reconciliation. [TrueConf unread](https://trueconf.ru/docs/chatbot-connector/ru/connect-and-auth/) · [Wire ACK](https://trueconf.ru/docs/chatbot-connector/ru/base-format-message/)
