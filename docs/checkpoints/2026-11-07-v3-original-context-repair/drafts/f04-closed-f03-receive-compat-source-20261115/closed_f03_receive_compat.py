
# Closed-F03 receive compatibility only. No first-send entry, send wrapper,
# admission, clock, run/cursor mutation or historical receipt rewriting.
_F04_CLOSED_F03_RUN = 'f03-ods-formulas-original-221-20261114'
_F04_CLOSED_F03_PHASE = {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-F03-EXACT-R108-CUSTODY-DELTA-20261114/revision2/candidate/first_send.py', 'bytes': 19459, 'sha256': '52d48a7cfc6162c137569728ec024e6d2633a0d7901ef92071b47cd764af63d7'}

def _f04_closed_f03_readonly_phase():
    import ast as _ast
    import types as _types
    ref = _F04_CLOSED_F03_PHASE
    raw = safe_read(Path(ref['path']))
    if len(raw) != ref['bytes'] or digest(raw) != ref['sha256']:
        raise Refused('Closed F03 first-send implementation changed')
    allowed = {'enc', 'sha', 'require', 'unique', 'read', 'refshape', 'rawref',
               'doc', 'pin', 'finite', 'plan', 'unbound', 'contract', 'validate',
               'effective_deadline'}
    tree = _ast.parse(raw, filename=ref['path'])
    tree.body = [node for node in tree.body
                 if isinstance(node, (_ast.Import, _ast.ImportFrom, _ast.Assign))
                 or isinstance(node, _ast.FunctionDef) and node.name in allowed]
    if {node.name for node in tree.body if isinstance(node, _ast.FunctionDef)} != allowed:
        raise Refused('Closed F03 readonly dependency closure changed')
    module = _types.ModuleType('_F04_closed_F03_readonly_phase')
    module.__file__ = ref['path']
    exec(compile(tree, ref['path'], 'exec'), module.__dict__)
    return module

def _f04_closed_f03_owner(self, run):
    if 'first_send_phase' not in run:
        return False
    if (run.get('id') != _F04_CLOSED_F03_RUN
            or run.get('status') != 'EVIDENCE_READY' or run.get('send_state') != 'sent'
            or type(run.get('step')) is not int or run['step'] != 0
            or type(run.get('send_attempts')) is not int or run['send_attempts'] != 1
            or run.get('capture_window_complete') is not True
            or 'continuation_reference' in run or 'new_ack_timeout_seconds' in run):
        raise Refused('Exact closed F03 first-send owner required')
    return True

def _f04_closed_f03_effective_deadline(self, run):
    if not _f04_closed_f03_owner(self, run):
        return run['deadline']
    try:
        # Exact producer semantics: validate defaults to active=False/preintent=False.
        # It authenticates immutable clock/once/before/contracts without reopening them.
        return _f04_closed_f03_readonly_phase().effective_deadline(self, run)
    except Exception as exc:
        raise Refused('Closed F03 durable first-send clock refused') from exc

def _f04_closed_f03_receive_context(self, run):
        context = dict(self.capture_binding(run), tester_id=TESTER, peer_id=PEER,
                    window=run['sent_window_reference'], deadline=self.effective_deadline(run),
                    capture_start_offset=run['capture_start_offset'],
                    prior_tracking=run['reply_capture_prior_tracking'])
        if 'first_send_phase' in run:
            context['first_send_phase'] = run['first_send_phase']
            context['original_deadline'] = run['deadline']
        if 'continuation_reference' in run:
            context['continuation'] = run['continuation_reference']
        return context

def _f04_closed_f03_receive_inventory(self, run, cursor=None, terminal=False):
        history = self.b00_closed_partial_history(run)
        if (not isinstance(run.get('seen'), list) or any(type(uid) is not int for uid in run['seen'])
                or not isinstance(run.get('observations'), list)
                or any(not isinstance(o, dict) for o in run['observations'])
                or not isinstance(run.get('message_ids'), list)):
            raise Refused('Capture processed-state shape invalid')
        sequence = run.get('receive_sequence')
        if type(sequence) is not int or not 0 <= sequence <= 3 * (run['scenario']['max_updates'] + 1):
            raise Refused('Mandatory capture receipt sequence missing or invalid')
        global_check = cursor is None
        if global_check:
            try:
                cursor = json.loads(safe_read(self.store.root / 'cursor.json'), object_pairs_hook=unique_object)
            except (ValueError, UnicodeError):
                raise Refused('Capture cursor is not unambiguous JSON') from None
        if (not isinstance(cursor, dict) or type(cursor.get('offset')) is not int
                or cursor['offset'] < run['capture_start_offset']
                or not isinstance(cursor.get('capture_receipts'), dict)
                or cursor['capture_receipts'].get(self.receive_key(run)) != run.get('receive_head')
                or run.get('receive_head') is None):
            raise Refused('Mandatory independent cursor/run capture commitment missing or changed')
        if global_check:
            self.cursor_offsets(cursor)
        context = self.receive_context(run)
        reference = run['receive_head']; records = []
        for index in range(sequence, -1, -1):
            name = 'receive-' + self.receive_key(run) + '-' + str(index) + '.json'
            record = self.read_reference(reference, name)
            if (not isinstance(record, dict) or record.get('context') != context
                    or type(record.get('sequence')) is not int or record['sequence'] != index
                    or type(record.get('offset')) is not int or record['offset'] < run['capture_start_offset']):
                raise Refused('Capture receipt does not bind the exact run/window/sequence')
            records.append(record); reference = record.get('previous')
        if reference is not None:
            raise Refused('Capture receipt seed has unexpected predecessor')
        expected_names = {'receive-' + self.receive_key(run) + '-' + str(index) + '.json'
                          for index in range(sequence + 1)}
        prefix = 'receive-' + self.receive_key(run) + '-'
        actual_names = {path.name for path in self.store.root.glob(prefix + '*.json')
                        if path.name[len(prefix):-5].isdigit()}
        if actual_names != expected_names:
            raise Refused('Unpaired capture/process witness outside committed receipt inventory')
        captures = {}; processed = {}; processing = set(); offset = run['capture_start_offset']; message_ids = []
        drain = {}; terminal_updates = None; terminal_processed = None
        for record in reversed(records):
            kind = record.get('kind'); uid = record.get('update_id')
            if drain.get('complete'):
                raise Refused('No capture operation may follow terminal completion')
            if kind == 'terminal_intent':
                started = record.get('started_at'); timeout = record.get('timeout_seconds')
                count = record.get('update_count')
                if (drain or processing or set(captures) != set(processed)
                        or record['offset'] != offset
                        or type(started) not in (int, float) or not math.isfinite(started)
                        or not run['capture_until'] <= started < self.effective_deadline(run) - REPLY_WINDOW_RESERVE
                        or type(timeout) not in (int, float) or not math.isfinite(timeout)
                        or not (0 < timeout <= min(10, self.effective_deadline(run) - started - REPLY_WINDOW_RESERVE)
                                or (history is not None and history['pending_update'] is None
                                    and record.get('http_timeout_cap') == 10
                                    and 10 < timeout <= self.effective_deadline(run) - started - REPLY_WINDOW_RESERVE))
                        or type(count) is not int or not len(processed) <= count <= run['scenario']['max_updates']
                        or type(record.get('limit')) is not int
                        or record['limit'] != min(20, run['scenario']['max_updates'] - count + 1)):
                    raise Refused('Invalid or repeated terminal drain intent')
                drain = {'intent': record}; terminal_processed = len(processed)
                continue
            if kind == 'terminal_response':
                intent = drain.get('intent'); received = record.get('received_at')
                if (intent is None or 'response' in drain or record['offset'] != offset
                        or type(received) not in (int, float) or not math.isfinite(received)
                        or not intent['started_at'] <= received <= intent['started_at'] + intent['timeout_seconds']
                        or received >= self.effective_deadline(run) - REPLY_WINDOW_RESERVE):
                    raise Refused('Invalid terminal response boundary')
                name = 'terminal-response-' + self.receive_key(run) + '.json'
                wire = self.read_reference(record.get('wire'), name)
                terminal_updates = wire.get('result') if isinstance(wire, dict) and wire.get('ok') is True else None
                if (not isinstance(terminal_updates, list) or len(terminal_updates) > intent['limit']
                        or any(not isinstance(u, dict) or type(u.get('update_id')) is not int
                               or u['update_id'] < offset for u in terminal_updates)
                        or len({u['update_id'] for u in terminal_updates}) != len(terminal_updates)):
                    raise Refused('Invalid terminal response update inventory')
                drain['response'] = record
                continue
            if kind == 'terminal_complete':
                intent = drain.get('intent'); completed = record.get('completed_at')
                if (terminal_updates is None or len(terminal_updates) >= intent['limit']
                        or processing or record['offset'] != offset
                        or set(captures) != set(processed)
                        or len(processed) - terminal_processed != len(terminal_updates)
                        or run['update_count'] != intent['update_count'] + len(terminal_updates)
                        or type(completed) not in (int, float) or not math.isfinite(completed)
                        or not drain['response']['received_at'] <= completed < self.effective_deadline(run)
                        or any(u['update_id'] not in processed for u in terminal_updates)):
                    raise Refused('Unproven or saturated terminal drain cannot complete')
                drain['complete'] = record
                continue
            if kind == 'seed':
                legacy_heads = record.get('legacy_heads', {})
                if (not isinstance(legacy_heads, dict)
                        or any(not key.startswith('legacy:')
                               or cursor['capture_receipts'].get(key) != head
                               for key, head in legacy_heads.items())):
                    raise Refused('Seed-bound legacy capture commitments missing or changed')
                if record['sequence'] != 0 or record['offset'] != offset:
                    raise Refused('Capture receipt seed changed')
                continue
            if type(uid) is not int or uid < run['capture_start_offset']:
                raise Refused('Capture receipt update identity invalid')
            if kind == 'capture':
                if drain and (terminal_updates is None
                              or not any(u.get('update_id') == uid for u in terminal_updates)):
                    raise Refused('Capture does not belong to the single terminal response')
                if uid in captures or uid < offset or record['offset'] != uid + 1:
                    raise Refused('Capture receipt offset/identity sequence invalid')
                raw = safe_read(self.store.captures / (str(uid) + '.json'))
                arrival_raw = safe_read(self.store.captures / (str(uid) + '.arrival.json'))
                if (record.get('raw_update') != {'basename': str(uid) + '.json', 'bytes': len(raw), 'sha256': digest(raw)}
                        or record.get('arrival') != {'basename': str(uid) + '.arrival.json', 'bytes': len(arrival_raw), 'sha256': digest(arrival_raw)}):
                    raise Refused('Committed raw/whole-arrival custody missing or changed')
                try:
                    update = json.loads(raw, object_pairs_hook=unique_object)
                    arrival = json.loads(arrival_raw, object_pairs_hook=unique_object)
                except (ValueError, UnicodeError):
                    raise Refused('Raw/arrival is not unambiguous JSON') from None
                if (not isinstance(update, dict) or update.get('update_id') != uid
                        or not isinstance(arrival, dict) or arrival.get('context') != context
                        or arrival.get('update_id') != uid or arrival.get('raw_update') != record['raw_update']
                        or type(arrival.get('arrived_at')) not in (int, float) or not math.isfinite(arrival['arrived_at'])):
                    raise Refused('Capture arrival identity/time/run/window changed')
                if drain and (update not in terminal_updates
                              or arrival['arrived_at'] < drain['response']['received_at']):
                    raise Refused('Terminal raw update or host arrival changed')
                captures[uid] = arrival; offset = uid + 1
            elif kind == 'processing':
                if uid not in captures or uid in processing or uid in processed or record['offset'] != offset:
                    raise Refused('Processing intent does not bind an unprocessed capture')
                processing.add(uid)
            elif kind == 'processed':
                if uid not in processing or uid in processed or record['offset'] != offset or not isinstance(record.get('observations'), list):
                    raise Refused('Processed capture receipt sequence invalid')
                if not isinstance(record.get('message_ids'), list):
                    raise Refused('Processed message identity commitment missing')
                processed[uid] = record; processing.remove(uid); message_ids = record['message_ids']
            else:
                raise Refused('Unknown capture receipt operation')
        stopped1667 = False
        if processing == {261479189} and run.get('id') == 'root-settings-restarted-e109244e1a93':
            self.settings_stopped1667_history(run)
            stopped1667 = True
        stopped1754 = False
        if processing == {261479248} and run.get('id') == M03_RUN:
            self.m03_stopped1754_history(run)
            stopped1754 = True
        stopped_r02 = False
        if processing == {261479318} and run.get('id') == 'root-m12-upload-305fa49d4a48':
            self.m12_r02_local_history(run)
            stopped_r02 = True
        stopped_w03 = False
        if processing == {261479334} and run.get('id') == 'root-w03-fulltext-5db764f4a3fe':
            self.w03_stopped_local_history(run)
            stopped_w03 = True
        history_pending = history['pending_update'] if history is not None else None
        if processing and not (stopped1667 or stopped1754 or stopped_r02 or stopped_w03
                              or (history_pending is not None and processing == {history_pending})):
            raise Refused('Processing outcome uncertain; retained evidence must not be replayed')
        if history is not None:
            if history_pending is None:
                intent = drain.get('intent', {})
                expected_drain = {'intent', 'response', 'complete'} if history['terminal_complete'] else {'intent'}
                if (set(drain) != expected_drain or intent.get('http_timeout_cap') != 10
                        or intent.get('budget_semantics') != 'VALIDATION_PLUS_HTTP_WITHIN_ORIGINAL_DEADLINE'
                        or not 10 < intent.get('timeout_seconds', 0) <= self.effective_deadline(run) - intent['started_at'] - REPLY_WINDOW_RESERVE):
                    raise Refused('Exact historical terminal custody required')
            elif drain or processing != {history_pending}:
                raise Refused('Exact stopped processing custody required; never invent completion')
        if cursor['offset'] < offset:
            raise Refused('Cursor rewound behind committed capture inventory')
        # Directory enumeration only detects extras. Required files always come from
        # the independent commitment above, including the crash-before-process case.
        # Explicit historical cursors validate their own committed inventory. The
        # live global cursor checker separately joins every current owner/raw pair.
        if global_check and cursor['offset'] == offset:
            for path in self.store.captures.glob('*.json'):
                stem = path.name.split('.')[0]
                if stem.isdigit() and int(stem) >= run['capture_start_offset'] and int(stem) not in captures:
                    raise Refused('Unpaired raw/arrival outside committed capture inventory')
        committed_message_ids = message_ids + ([history['pending_message_id']] if history_pending is not None else [1669] if stopped1667 else [1756] if stopped1754 else [1859] if stopped_r02 else [1883] if stopped_w03 else [])
        if run.get('message_ids') != committed_message_ids:
            raise Refused('Committed processed message identities missing or changed')
        if set(run.get('seen', [])) != set(processed) | ({history_pending} if history_pending is not None else set()) | ({261479189} if stopped1667 else {261479248} if stopped1754 else {261479318} if stopped_r02 else {261479334} if stopped_w03 else set()):
            raise Refused('Processed seen inventory missing or changed')
        for uid, record in processed.items():
            if [o for o in run.get('observations', []) if o.get('update_id') == uid] != record['observations']:
                raise Refused('Committed processed observations missing or changed')
        return (captures, processed, drain) if terminal else (captures, processed)

def _f04_closed_f03_legacy_receive_inventory(self, owner, head, captures=None):
        sequence = owner.get('legacy_receive_sequence')
        if (type(sequence) is not int or not 0 <= sequence <= owner['scenario']['max_updates']
                or owner.get('legacy_receive_head') != head
                or owner.get('scenario_sha256') != digest(encoded(owner['scenario']))):
            raise Refused('Legacy capture lacks independent exact run commitment')
        context = dict(run_id=owner['id'], scenario_sha256=owner['scenario_sha256'],
                       tester_id=TESTER, peer_id=PEER, deadline=self.effective_deadline(owner))
        reference = head; records = []
        for index in range(sequence, -1, -1):
            name = 'legacy-receive-' + owner['id'] + '-' + str(index) + '.json'
            record = self.read_reference(reference, name)
            if (not isinstance(record, dict) or record.get('kind') != 'legacy_capture'
                    or record.get('context') != context
                    or type(record.get('sequence')) is not int or record['sequence'] != index
                    or type(record.get('step')) is not int
                    or not 0 <= record['step'] < len(owner['scenario']['steps'])
                    or reply_capture(owner['scenario']['steps'][record['step']]['observe'])
                    or record['step'] >= len(owner['sent_ids'])
                    or record.get('sent_message_id') != owner['sent_ids'][record['step']]
                    or type(record.get('prior_offset')) is not int or record['prior_offset'] < 0
                    or type(record.get('update_id')) is not int
                    or record['update_id'] < record['prior_offset']
                    or type(record.get('offset')) is not int
                    or record['offset'] != record['update_id'] + 1):
                raise Refused('Legacy capture receipt run/identity/offset binding changed')
            uid = record['update_id']
            raw = safe_read(self.store.captures / (str(uid) + '.json'))
            arrival_raw = safe_read(self.store.captures / (str(uid) + '.arrival.json'))
            if (record.get('raw_update') != dict(basename=str(uid) + '.json', bytes=len(raw), sha256=digest(raw))
                    or record.get('arrival') != dict(basename=str(uid) + '.arrival.json', bytes=len(arrival_raw), sha256=digest(arrival_raw))):
                raise Refused('Legacy committed whole raw/arrival custody changed')
            try:
                update = json.loads(raw, object_pairs_hook=unique_object)
                arrival = json.loads(arrival_raw, object_pairs_hook=unique_object)
            except (ValueError, UnicodeError):
                raise Refused('Legacy raw/arrival is not unambiguous JSON') from None
            if (not isinstance(update, dict) or update.get('update_id') != uid
                    or not isinstance(arrival, dict) or arrival.get('update_id') != uid
                    or arrival.get('raw_update') != record['raw_update']
                    or type(arrival.get('arrived_at')) not in (int, float)
                    or not math.isfinite(arrival['arrived_at'])):
                raise Refused('Legacy capture raw/arrival identity/time changed')
            if captures is not None:
                if uid in captures:
                    raise Refused('Capture UID has multiple independent owners')
                captures[uid] = arrival
            records.append(record); reference = record.get('previous')
        if reference is not None or any(a['prior_offset'] < b['offset']
                                        for a, b in zip(records, records[1:])):
            raise Refused('Legacy capture receipt chain changed or rewound')
        prefix = 'legacy-receive-' + owner['id'] + '-'
        expected = {prefix + str(i) + '.json' for i in range(sequence + 1)}
        actual = {p.name for p in self.store.root.glob(prefix + '*.json')
                  if p.name[len(prefix):-5].isdigit()}
        if actual != expected:
            raise Refused('Unpaired legacy capture receipt outside committed inventory')
        return records[0]['offset']

_f04_before_closed_f03_context = Runner.receive_context
_f04_before_closed_f03_inventory = Runner.receive_inventory
_f04_before_closed_f03_legacy_inventory = Runner.legacy_receive_inventory

def _f04_receive_context(self, run):
    if _f04_closed_f03_owner(self, run):
        return _f04_closed_f03_receive_context(self, run)
    return _f04_before_closed_f03_context(self, run)

def _f04_receive_inventory(self, run, cursor=None, terminal=False):
    if _f04_closed_f03_owner(self, run):
        return _f04_closed_f03_receive_inventory(self, run, cursor, terminal)
    return _f04_before_closed_f03_inventory(self, run, cursor, terminal)

def _f04_legacy_receive_inventory(self, owner, head, captures=None):
    if _f04_closed_f03_owner(self, owner):
        return _f04_closed_f03_legacy_receive_inventory(self, owner, head, captures)
    return _f04_before_closed_f03_legacy_inventory(self, owner, head, captures)

Runner.effective_deadline = _f04_closed_f03_effective_deadline
Runner.receive_context = _f04_receive_context
Runner.receive_inventory = _f04_receive_inventory
Runner.legacy_receive_inventory = _f04_legacy_receive_inventory
