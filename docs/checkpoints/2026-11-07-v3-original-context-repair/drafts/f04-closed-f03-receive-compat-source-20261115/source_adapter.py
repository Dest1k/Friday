"""F04 Root source adapter. Import and all constructors are effect free.

bind_full_v42 preserves its three ordinary admission seams and adds a bounded
readonly compatibility seam for the exact closed F03 producer receipt contract.
Current, clocks, single use and native closure remain owned by Root; no F03
first-send entry or send seam is installed.
"""
import ast
import copy
import hashlib
import json
import re

BASE = {
    'path': '/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/evidence/tester/bot_tester.v42.py',
    'bytes': 1136988,
    'sha256': 'f0caba28ba9e823574a5149b55989aea7f4e5c893c3a89a7b4eb0ed0cf5e7ad3',
}
ISSUER = {
    'path': '/home/jericho/jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/issue-fresh-admission.py',
    'bytes': 29781,
    'sha256': 'ae6f2631eb6b053d1463a15665eaef7354b622756cee76c69b582ae8eb70d518',
}
SOURCE = {
    'path': '/home/jericho/.cache/FRW-ASTRA-V3-F03-RICH-ODS-ORIGINAL221-20261114/input/orders-formulas-original.ods',
    'bytes': 16538,
    'sha256': 'a2e68bc685e4d689aa7972ff4f2c7f9841441c9dcb4fc5e40327a5ae190b5d58',
}
ROOT_SCOPE = 'case165/F04/format27_to26/original_required_rich_formula'
CAPTION = ('Преобразуй приложенный ODS в настоящий XLSX и пришли полученный файл в эту беседу. '
           'Сохрани все листы, их порядок, строки, типы данных, строковые идентификаторы, исходные числа, '
           'формулы произведений и межлистовую итоговую формулу; не заменяй формулы значениями. '
           'Сохрани поддерживаемые имена, диаграммы, фильтр, проверки данных, объединения и текущее скрытое '
           'состояние. Исходник не изменяй. Перечисли все реальные потери и непроверенные аспекты, а также '
           'ограничения кэшей и пересчёта. Не называй преобразование полностью без потерь или эквивалентным '
           'по внешнему виду и физической разметке.')
STAT_FIELDS = {'device', 'inode', 'size_bytes', 'uid', 'mtime_ns', 'ctime_ns'}
OLD_AUTHORITY = 'ordinary-independent-jarvis-activate-20261109-r68'


def need(condition, code):
    if not condition:
        raise ValueError(code)


def encoded(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, allow_nan=False) + '\n').encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def is_sha(value):
    return type(value) is str and re.fullmatch('[a-f0-9]{64}', value) is not None


def path_shape(value):
    need(type(value) is str and value.startswith('/') and not value.startswith('//')
         and not any(part in ('', '.', '..') for part in value.split('/')[1:])
         and not any(ord(ch) < 32 or 127 <= ord(ch) <= 159 for ch in value),
         'F04_ABSOLUTE_CANONICAL_PATH_REQUIRED')
    value.encode('utf-8')
    return value


def reference(value):
    need(type(value) is dict and set(value) == {'path', 'bytes', 'sha256'}
         and type(value['bytes']) is int and value['bytes'] > 0
         and is_sha(value['sha256']), 'F04_EXACT_REFERENCE_REQUIRED')
    path_shape(value['path'])
    return value


def stat_shape(value):
    need(type(value) is dict and set(value) == STAT_FIELDS
         and all(type(v) is int and v >= 0 for v in value.values())
         and value['inode'] > 0 and value['size_bytes'] == SOURCE['bytes'],
         'F04_FRESH_EXACT_SOURCE_STAT_REQUIRED')
    return value


def construct_scenario(source_stat):
    """Root supplies fresh metadata later. This creates no file or admission."""
    stat_shape(source_stat)
    return {
        'tester_id': 8812646969, 'peer_id': 8751854128, 'peer_username': '@jerichodevbot',
        'deadline_seconds': 300, 'max_updates': 64, 'pace_seconds': 2,
        'steps': [{
            'input': {'kind': 'document', 'path': SOURCE['path'], 'sha256': SOURCE['sha256'],
                      'stat': dict(source_stat), 'filename': 'orders-formulas-original.ods',
                      'mime_type': 'application/vnd.oasis.opendocument.spreadsheet', 'caption': CAPTION},
            'observe': {'mode': 'bounded_reply_capture', 'window_seconds': 180,
                        'document_max_bytes': 1048576, 'max_documents': 1,
                        'max_messages': 4, 'max_text_chars': 8000},
        }],
    }


def scenario_shape(value):
    need(type(value) is dict and type(value.get('steps')) is list
         and len(value['steps']) == 1, 'F04_EXACT_SINGLETON_SCENARIO_REQUIRED')
    try:
        pin = value['steps'][0]['input']['stat']
    except (KeyError, IndexError, TypeError):
        raise ValueError('F04_SOURCE_STAT_UNBOUND') from None
    need(value == construct_scenario(pin), 'F04_ORIGINAL_SOURCE_CAPTION_OR_BOUNDS_CHANGED')
    return value


def _seams(tree):
    runners = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Runner']
    need(len(runners) == 1, 'F04_SINGLE_RUNNER_REQUIRED')
    runner = runners[0]
    nodes = []
    for name in ('ORDINARY_INDEPENDENT_SCENARIOS', 'ORDINARY_INDEPENDENT_AUTHORITY'):
        hits = [n for n in runner.body if isinstance(n, ast.Assign)
                and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)
                and n.targets[0].id == name]
        need(len(hits) == 1, 'F04_UNIQUE_SOURCE_SEAM_REQUIRED')
        nodes.append(hits[0])
    methods = [n for n in runner.body if isinstance(n, ast.FunctionDef)
               and n.name == 'ordinary_independent_admission']
    need(len(methods) == 1, 'F04_UNIQUE_ADMISSION_METHOD_REQUIRED')
    ids = [n for n in ast.walk(methods[0]) if isinstance(n, ast.Constant)
           and n.value == OLD_AUTHORITY]
    need(len(ids) == 1, 'F04_UNIQUE_AUTHORITY_ID_SEAM_REQUIRED')
    return nodes + ids


def _normalized(tree, authority_id):
    tree = copy.deepcopy(tree)
    runner = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Runner')
    for node in runner.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id in {
                'ORDINARY_INDEPENDENT_SCENARIOS', 'ORDINARY_INDEPENDENT_AUTHORITY'} for t in node.targets):
            node.value = ast.Constant(value='EXACT_EXISTING_SEAM')
        if isinstance(node, ast.FunctionDef) and node.name == 'ordinary_independent_admission':
            hits = [n for n in ast.walk(node) if isinstance(n, ast.Constant) and n.value == authority_id]
            need(len(hits) == 1, 'F04_BOUND_AUTHORITY_LITERAL_NOT_UNIQUE')
            hits[0].value = 'EXACT_AUTHORITY_ID_SEAM'
    return ast.dump(tree, include_attributes=False)


def bind_full_v42(base_raw, run_id, scenario_sha256, authority, authority_id):
    """Pure exact three-seam successor; full remaining AST must be identical."""
    need(type(base_raw) is bytes and len(base_raw) == BASE['bytes']
         and digest(base_raw) == BASE['sha256'], 'F04_PINNED_FULL_V42_REQUIRED')
    need(type(run_id) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', run_id)
         and 'UNBOUND' not in run_id and is_sha(scenario_sha256), 'F04_ACTUAL_RUN_SCENARIO_REQUIRED')
    reference(authority)
    need(type(authority_id) is str and authority_id and authority_id != OLD_AUTHORITY
         and 'UNBOUND' not in authority_id, 'F04_ACTUAL_NEW_AUTHORITY_REQUIRED')
    text = base_raw.decode('utf-8')
    before = ast.parse(text)
    nodes = _seams(before)
    lines = text.splitlines(keepends=True)
    values = ({run_id: scenario_sha256}, authority)
    edits = []
    for node, value in zip(nodes[:2], values):
        name = node.targets[0].id
        edits.append((node.lineno, node.end_lineno, '    ' + name + ' = ' + repr(value) + '\n'))
    node = nodes[2]
    need(node.lineno == node.end_lineno, 'F04_AUTHORITY_LITERAL_SINGLE_LINE_REQUIRED')
    line = lines[node.lineno - 1]
    # Source columns are UTF-8 bytes; this existing comparison line is ASCII.
    need(line.isascii(), 'F04_LITERAL_LINE_ENCODING_CHANGED')
    edits.append((node.lineno, node.end_lineno,
                  line[:node.col_offset] + repr(authority_id) + line[node.end_col_offset:]))
    for first, last, replacement in sorted(edits, reverse=True):
        lines[first - 1:last] = [replacement]
    bound = ''.join(lines).encode()
    after = ast.parse(bound)
    need(_normalized(before, OLD_AUTHORITY) == _normalized(after, authority_id),
         'F04_NON_SEAM_TESTER_AST_CHANGED')
    return _add_closed_f03_receive_compatibility(bound)


def verify_issued(document, root, authority_id):
    """Additional singleton/scope check; generic v42 rechecks its full admission."""
    need(type(document) is dict and document.get('schema') ==
         'frw.Root.ordinary-independent-history-admission.v1'
         and document.get('authority_id') == authority_id
         and document.get('operator') == 'Root' and document.get('accepted') is True
         and document.get('run_scenarios') == {root['run_id']: root['scenario_sha256']}
         and document.get('scope') == root['authority_scope']
         and document.get('product_or_B00_acceptance') is False
         and document.get('new_trial_for_historical_task') is False
         and document.get('unknown_effects_resolved') is False,
         'F04_ISSUED_SINGLETON_ORIGINAL_SCOPE_REQUIRED')
    return True


CLOSED_F03_RECEIVE_COMPATIBILITY = "\n# Closed-F03 receive compatibility only. No first-send entry, send wrapper,\n# admission, clock, run/cursor mutation or historical receipt rewriting.\n_F04_CLOSED_F03_RUN = 'f03-ods-formulas-original-221-20261114'\n_F04_CLOSED_F03_PHASE = {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-F03-EXACT-R108-CUSTODY-DELTA-20261114/revision2/candidate/first_send.py', 'bytes': 19459, 'sha256': '52d48a7cfc6162c137569728ec024e6d2633a0d7901ef92071b47cd764af63d7'}\n\ndef _f04_closed_f03_readonly_phase():\n    import ast as _ast\n    import types as _types\n    ref = _F04_CLOSED_F03_PHASE\n    raw = safe_read(Path(ref['path']))\n    if len(raw) != ref['bytes'] or digest(raw) != ref['sha256']:\n        raise Refused('Closed F03 first-send implementation changed')\n    allowed = {'enc', 'sha', 'require', 'unique', 'read', 'refshape', 'rawref',\n               'doc', 'pin', 'finite', 'plan', 'unbound', 'contract', 'validate',\n               'effective_deadline'}\n    tree = _ast.parse(raw, filename=ref['path'])\n    tree.body = [node for node in tree.body\n                 if isinstance(node, (_ast.Import, _ast.ImportFrom, _ast.Assign))\n                 or isinstance(node, _ast.FunctionDef) and node.name in allowed]\n    if {node.name for node in tree.body if isinstance(node, _ast.FunctionDef)} != allowed:\n        raise Refused('Closed F03 readonly dependency closure changed')\n    module = _types.ModuleType('_F04_closed_F03_readonly_phase')\n    module.__file__ = ref['path']\n    exec(compile(tree, ref['path'], 'exec'), module.__dict__)\n    return module\n\ndef _f04_closed_f03_owner(self, run):\n    if 'first_send_phase' not in run:\n        return False\n    if (run.get('id') != _F04_CLOSED_F03_RUN\n            or run.get('status') != 'EVIDENCE_READY' or run.get('send_state') != 'sent'\n            or type(run.get('step')) is not int or run['step'] != 0\n            or type(run.get('send_attempts')) is not int or run['send_attempts'] != 1\n            or run.get('capture_window_complete') is not True\n            or 'continuation_reference' in run or 'new_ack_timeout_seconds' in run):\n        raise Refused('Exact closed F03 first-send owner required')\n    return True\n\ndef _f04_closed_f03_effective_deadline(self, run):\n    if not _f04_closed_f03_owner(self, run):\n        return run['deadline']\n    try:\n        # Exact producer semantics: validate defaults to active=False/preintent=False.\n        # It authenticates immutable clock/once/before/contracts without reopening them.\n        return _f04_closed_f03_readonly_phase().effective_deadline(self, run)\n    except Exception as exc:\n        raise Refused('Closed F03 durable first-send clock refused') from exc\n\ndef _f04_closed_f03_receive_context(self, run):\n        context = dict(self.capture_binding(run), tester_id=TESTER, peer_id=PEER,\n                    window=run['sent_window_reference'], deadline=self.effective_deadline(run),\n                    capture_start_offset=run['capture_start_offset'],\n                    prior_tracking=run['reply_capture_prior_tracking'])\n        if 'first_send_phase' in run:\n            context['first_send_phase'] = run['first_send_phase']\n            context['original_deadline'] = run['deadline']\n        if 'continuation_reference' in run:\n            context['continuation'] = run['continuation_reference']\n        return context\n\ndef _f04_closed_f03_receive_inventory(self, run, cursor=None, terminal=False):\n        history = self.b00_closed_partial_history(run)\n        if (not isinstance(run.get('seen'), list) or any(type(uid) is not int for uid in run['seen'])\n                or not isinstance(run.get('observations'), list)\n                or any(not isinstance(o, dict) for o in run['observations'])\n                or not isinstance(run.get('message_ids'), list)):\n            raise Refused('Capture processed-state shape invalid')\n        sequence = run.get('receive_sequence')\n        if type(sequence) is not int or not 0 <= sequence <= 3 * (run['scenario']['max_updates'] + 1):\n            raise Refused('Mandatory capture receipt sequence missing or invalid')\n        global_check = cursor is None\n        if global_check:\n            try:\n                cursor = json.loads(safe_read(self.store.root / 'cursor.json'), object_pairs_hook=unique_object)\n            except (ValueError, UnicodeError):\n                raise Refused('Capture cursor is not unambiguous JSON') from None\n        if (not isinstance(cursor, dict) or type(cursor.get('offset')) is not int\n                or cursor['offset'] < run['capture_start_offset']\n                or not isinstance(cursor.get('capture_receipts'), dict)\n                or cursor['capture_receipts'].get(self.receive_key(run)) != run.get('receive_head')\n                or run.get('receive_head') is None):\n            raise Refused('Mandatory independent cursor/run capture commitment missing or changed')\n        if global_check:\n            self.cursor_offsets(cursor)\n        context = self.receive_context(run)\n        reference = run['receive_head']; records = []\n        for index in range(sequence, -1, -1):\n            name = 'receive-' + self.receive_key(run) + '-' + str(index) + '.json'\n            record = self.read_reference(reference, name)\n            if (not isinstance(record, dict) or record.get('context') != context\n                    or type(record.get('sequence')) is not int or record['sequence'] != index\n                    or type(record.get('offset')) is not int or record['offset'] < run['capture_start_offset']):\n                raise Refused('Capture receipt does not bind the exact run/window/sequence')\n            records.append(record); reference = record.get('previous')\n        if reference is not None:\n            raise Refused('Capture receipt seed has unexpected predecessor')\n        expected_names = {'receive-' + self.receive_key(run) + '-' + str(index) + '.json'\n                          for index in range(sequence + 1)}\n        prefix = 'receive-' + self.receive_key(run) + '-'\n        actual_names = {path.name for path in self.store.root.glob(prefix + '*.json')\n                        if path.name[len(prefix):-5].isdigit()}\n        if actual_names != expected_names:\n            raise Refused('Unpaired capture/process witness outside committed receipt inventory')\n        captures = {}; processed = {}; processing = set(); offset = run['capture_start_offset']; message_ids = []\n        drain = {}; terminal_updates = None; terminal_processed = None\n        for record in reversed(records):\n            kind = record.get('kind'); uid = record.get('update_id')\n            if drain.get('complete'):\n                raise Refused('No capture operation may follow terminal completion')\n            if kind == 'terminal_intent':\n                started = record.get('started_at'); timeout = record.get('timeout_seconds')\n                count = record.get('update_count')\n                if (drain or processing or set(captures) != set(processed)\n                        or record['offset'] != offset\n                        or type(started) not in (int, float) or not math.isfinite(started)\n                        or not run['capture_until'] <= started < self.effective_deadline(run) - REPLY_WINDOW_RESERVE\n                        or type(timeout) not in (int, float) or not math.isfinite(timeout)\n                        or not (0 < timeout <= min(10, self.effective_deadline(run) - started - REPLY_WINDOW_RESERVE)\n                                or (history is not None and history['pending_update'] is None\n                                    and record.get('http_timeout_cap') == 10\n                                    and 10 < timeout <= self.effective_deadline(run) - started - REPLY_WINDOW_RESERVE))\n                        or type(count) is not int or not len(processed) <= count <= run['scenario']['max_updates']\n                        or type(record.get('limit')) is not int\n                        or record['limit'] != min(20, run['scenario']['max_updates'] - count + 1)):\n                    raise Refused('Invalid or repeated terminal drain intent')\n                drain = {'intent': record}; terminal_processed = len(processed)\n                continue\n            if kind == 'terminal_response':\n                intent = drain.get('intent'); received = record.get('received_at')\n                if (intent is None or 'response' in drain or record['offset'] != offset\n                        or type(received) not in (int, float) or not math.isfinite(received)\n                        or not intent['started_at'] <= received <= intent['started_at'] + intent['timeout_seconds']\n                        or received >= self.effective_deadline(run) - REPLY_WINDOW_RESERVE):\n                    raise Refused('Invalid terminal response boundary')\n                name = 'terminal-response-' + self.receive_key(run) + '.json'\n                wire = self.read_reference(record.get('wire'), name)\n                terminal_updates = wire.get('result') if isinstance(wire, dict) and wire.get('ok') is True else None\n                if (not isinstance(terminal_updates, list) or len(terminal_updates) > intent['limit']\n                        or any(not isinstance(u, dict) or type(u.get('update_id')) is not int\n                               or u['update_id'] < offset for u in terminal_updates)\n                        or len({u['update_id'] for u in terminal_updates}) != len(terminal_updates)):\n                    raise Refused('Invalid terminal response update inventory')\n                drain['response'] = record\n                continue\n            if kind == 'terminal_complete':\n                intent = drain.get('intent'); completed = record.get('completed_at')\n                if (terminal_updates is None or len(terminal_updates) >= intent['limit']\n                        or processing or record['offset'] != offset\n                        or set(captures) != set(processed)\n                        or len(processed) - terminal_processed != len(terminal_updates)\n                        or run['update_count'] != intent['update_count'] + len(terminal_updates)\n                        or type(completed) not in (int, float) or not math.isfinite(completed)\n                        or not drain['response']['received_at'] <= completed < self.effective_deadline(run)\n                        or any(u['update_id'] not in processed for u in terminal_updates)):\n                    raise Refused('Unproven or saturated terminal drain cannot complete')\n                drain['complete'] = record\n                continue\n            if kind == 'seed':\n                legacy_heads = record.get('legacy_heads', {})\n                if (not isinstance(legacy_heads, dict)\n                        or any(not key.startswith('legacy:')\n                               or cursor['capture_receipts'].get(key) != head\n                               for key, head in legacy_heads.items())):\n                    raise Refused('Seed-bound legacy capture commitments missing or changed')\n                if record['sequence'] != 0 or record['offset'] != offset:\n                    raise Refused('Capture receipt seed changed')\n                continue\n            if type(uid) is not int or uid < run['capture_start_offset']:\n                raise Refused('Capture receipt update identity invalid')\n            if kind == 'capture':\n                if drain and (terminal_updates is None\n                              or not any(u.get('update_id') == uid for u in terminal_updates)):\n                    raise Refused('Capture does not belong to the single terminal response')\n                if uid in captures or uid < offset or record['offset'] != uid + 1:\n                    raise Refused('Capture receipt offset/identity sequence invalid')\n                raw = safe_read(self.store.captures / (str(uid) + '.json'))\n                arrival_raw = safe_read(self.store.captures / (str(uid) + '.arrival.json'))\n                if (record.get('raw_update') != {'basename': str(uid) + '.json', 'bytes': len(raw), 'sha256': digest(raw)}\n                        or record.get('arrival') != {'basename': str(uid) + '.arrival.json', 'bytes': len(arrival_raw), 'sha256': digest(arrival_raw)}):\n                    raise Refused('Committed raw/whole-arrival custody missing or changed')\n                try:\n                    update = json.loads(raw, object_pairs_hook=unique_object)\n                    arrival = json.loads(arrival_raw, object_pairs_hook=unique_object)\n                except (ValueError, UnicodeError):\n                    raise Refused('Raw/arrival is not unambiguous JSON') from None\n                if (not isinstance(update, dict) or update.get('update_id') != uid\n                        or not isinstance(arrival, dict) or arrival.get('context') != context\n                        or arrival.get('update_id') != uid or arrival.get('raw_update') != record['raw_update']\n                        or type(arrival.get('arrived_at')) not in (int, float) or not math.isfinite(arrival['arrived_at'])):\n                    raise Refused('Capture arrival identity/time/run/window changed')\n                if drain and (update not in terminal_updates\n                              or arrival['arrived_at'] < drain['response']['received_at']):\n                    raise Refused('Terminal raw update or host arrival changed')\n                captures[uid] = arrival; offset = uid + 1\n            elif kind == 'processing':\n                if uid not in captures or uid in processing or uid in processed or record['offset'] != offset:\n                    raise Refused('Processing intent does not bind an unprocessed capture')\n                processing.add(uid)\n            elif kind == 'processed':\n                if uid not in processing or uid in processed or record['offset'] != offset or not isinstance(record.get('observations'), list):\n                    raise Refused('Processed capture receipt sequence invalid')\n                if not isinstance(record.get('message_ids'), list):\n                    raise Refused('Processed message identity commitment missing')\n                processed[uid] = record; processing.remove(uid); message_ids = record['message_ids']\n            else:\n                raise Refused('Unknown capture receipt operation')\n        stopped1667 = False\n        if processing == {261479189} and run.get('id') == 'root-settings-restarted-e109244e1a93':\n            self.settings_stopped1667_history(run)\n            stopped1667 = True\n        stopped1754 = False\n        if processing == {261479248} and run.get('id') == M03_RUN:\n            self.m03_stopped1754_history(run)\n            stopped1754 = True\n        stopped_r02 = False\n        if processing == {261479318} and run.get('id') == 'root-m12-upload-305fa49d4a48':\n            self.m12_r02_local_history(run)\n            stopped_r02 = True\n        stopped_w03 = False\n        if processing == {261479334} and run.get('id') == 'root-w03-fulltext-5db764f4a3fe':\n            self.w03_stopped_local_history(run)\n            stopped_w03 = True\n        history_pending = history['pending_update'] if history is not None else None\n        if processing and not (stopped1667 or stopped1754 or stopped_r02 or stopped_w03\n                              or (history_pending is not None and processing == {history_pending})):\n            raise Refused('Processing outcome uncertain; retained evidence must not be replayed')\n        if history is not None:\n            if history_pending is None:\n                intent = drain.get('intent', {})\n                expected_drain = {'intent', 'response', 'complete'} if history['terminal_complete'] else {'intent'}\n                if (set(drain) != expected_drain or intent.get('http_timeout_cap') != 10\n                        or intent.get('budget_semantics') != 'VALIDATION_PLUS_HTTP_WITHIN_ORIGINAL_DEADLINE'\n                        or not 10 < intent.get('timeout_seconds', 0) <= self.effective_deadline(run) - intent['started_at'] - REPLY_WINDOW_RESERVE):\n                    raise Refused('Exact historical terminal custody required')\n            elif drain or processing != {history_pending}:\n                raise Refused('Exact stopped processing custody required; never invent completion')\n        if cursor['offset'] < offset:\n            raise Refused('Cursor rewound behind committed capture inventory')\n        # Directory enumeration only detects extras. Required files always come from\n        # the independent commitment above, including the crash-before-process case.\n        # Explicit historical cursors validate their own committed inventory. The\n        # live global cursor checker separately joins every current owner/raw pair.\n        if global_check and cursor['offset'] == offset:\n            for path in self.store.captures.glob('*.json'):\n                stem = path.name.split('.')[0]\n                if stem.isdigit() and int(stem) >= run['capture_start_offset'] and int(stem) not in captures:\n                    raise Refused('Unpaired raw/arrival outside committed capture inventory')\n        committed_message_ids = message_ids + ([history['pending_message_id']] if history_pending is not None else [1669] if stopped1667 else [1756] if stopped1754 else [1859] if stopped_r02 else [1883] if stopped_w03 else [])\n        if run.get('message_ids') != committed_message_ids:\n            raise Refused('Committed processed message identities missing or changed')\n        if set(run.get('seen', [])) != set(processed) | ({history_pending} if history_pending is not None else set()) | ({261479189} if stopped1667 else {261479248} if stopped1754 else {261479318} if stopped_r02 else {261479334} if stopped_w03 else set()):\n            raise Refused('Processed seen inventory missing or changed')\n        for uid, record in processed.items():\n            if [o for o in run.get('observations', []) if o.get('update_id') == uid] != record['observations']:\n                raise Refused('Committed processed observations missing or changed')\n        return (captures, processed, drain) if terminal else (captures, processed)\n\ndef _f04_closed_f03_legacy_receive_inventory(self, owner, head, captures=None):\n        sequence = owner.get('legacy_receive_sequence')\n        if (type(sequence) is not int or not 0 <= sequence <= owner['scenario']['max_updates']\n                or owner.get('legacy_receive_head') != head\n                or owner.get('scenario_sha256') != digest(encoded(owner['scenario']))):\n            raise Refused('Legacy capture lacks independent exact run commitment')\n        context = dict(run_id=owner['id'], scenario_sha256=owner['scenario_sha256'],\n                       tester_id=TESTER, peer_id=PEER, deadline=self.effective_deadline(owner))\n        reference = head; records = []\n        for index in range(sequence, -1, -1):\n            name = 'legacy-receive-' + owner['id'] + '-' + str(index) + '.json'\n            record = self.read_reference(reference, name)\n            if (not isinstance(record, dict) or record.get('kind') != 'legacy_capture'\n                    or record.get('context') != context\n                    or type(record.get('sequence')) is not int or record['sequence'] != index\n                    or type(record.get('step')) is not int\n                    or not 0 <= record['step'] < len(owner['scenario']['steps'])\n                    or reply_capture(owner['scenario']['steps'][record['step']]['observe'])\n                    or record['step'] >= len(owner['sent_ids'])\n                    or record.get('sent_message_id') != owner['sent_ids'][record['step']]\n                    or type(record.get('prior_offset')) is not int or record['prior_offset'] < 0\n                    or type(record.get('update_id')) is not int\n                    or record['update_id'] < record['prior_offset']\n                    or type(record.get('offset')) is not int\n                    or record['offset'] != record['update_id'] + 1):\n                raise Refused('Legacy capture receipt run/identity/offset binding changed')\n            uid = record['update_id']\n            raw = safe_read(self.store.captures / (str(uid) + '.json'))\n            arrival_raw = safe_read(self.store.captures / (str(uid) + '.arrival.json'))\n            if (record.get('raw_update') != dict(basename=str(uid) + '.json', bytes=len(raw), sha256=digest(raw))\n                    or record.get('arrival') != dict(basename=str(uid) + '.arrival.json', bytes=len(arrival_raw), sha256=digest(arrival_raw))):\n                raise Refused('Legacy committed whole raw/arrival custody changed')\n            try:\n                update = json.loads(raw, object_pairs_hook=unique_object)\n                arrival = json.loads(arrival_raw, object_pairs_hook=unique_object)\n            except (ValueError, UnicodeError):\n                raise Refused('Legacy raw/arrival is not unambiguous JSON') from None\n            if (not isinstance(update, dict) or update.get('update_id') != uid\n                    or not isinstance(arrival, dict) or arrival.get('update_id') != uid\n                    or arrival.get('raw_update') != record['raw_update']\n                    or type(arrival.get('arrived_at')) not in (int, float)\n                    or not math.isfinite(arrival['arrived_at'])):\n                raise Refused('Legacy capture raw/arrival identity/time changed')\n            if captures is not None:\n                if uid in captures:\n                    raise Refused('Capture UID has multiple independent owners')\n                captures[uid] = arrival\n            records.append(record); reference = record.get('previous')\n        if reference is not None or any(a['prior_offset'] < b['offset']\n                                        for a, b in zip(records, records[1:])):\n            raise Refused('Legacy capture receipt chain changed or rewound')\n        prefix = 'legacy-receive-' + owner['id'] + '-'\n        expected = {prefix + str(i) + '.json' for i in range(sequence + 1)}\n        actual = {p.name for p in self.store.root.glob(prefix + '*.json')\n                  if p.name[len(prefix):-5].isdigit()}\n        if actual != expected:\n            raise Refused('Unpaired legacy capture receipt outside committed inventory')\n        return records[0]['offset']\n\n_f04_before_closed_f03_context = Runner.receive_context\n_f04_before_closed_f03_inventory = Runner.receive_inventory\n_f04_before_closed_f03_legacy_inventory = Runner.legacy_receive_inventory\n\ndef _f04_receive_context(self, run):\n    if _f04_closed_f03_owner(self, run):\n        return _f04_closed_f03_receive_context(self, run)\n    return _f04_before_closed_f03_context(self, run)\n\ndef _f04_receive_inventory(self, run, cursor=None, terminal=False):\n    if _f04_closed_f03_owner(self, run):\n        return _f04_closed_f03_receive_inventory(self, run, cursor, terminal)\n    return _f04_before_closed_f03_inventory(self, run, cursor, terminal)\n\ndef _f04_legacy_receive_inventory(self, owner, head, captures=None):\n    if _f04_closed_f03_owner(self, owner):\n        return _f04_closed_f03_legacy_receive_inventory(self, owner, head, captures)\n    return _f04_before_closed_f03_legacy_inventory(self, owner, head, captures)\n\nRunner.effective_deadline = _f04_closed_f03_effective_deadline\nRunner.receive_context = _f04_receive_context\nRunner.receive_inventory = _f04_receive_inventory\nRunner.legacy_receive_inventory = _f04_legacy_receive_inventory\n"

def _add_closed_f03_receive_compatibility(bound):
    tree = ast.parse(bound)
    names = {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    need(not any(name.startswith('_f04_closed_f03_') for name in names), 'F04_CLOSED_F03_COMPATIBILITY_ALREADY_PRESENT')
    mains = [node for node in tree.body if isinstance(node, ast.If) and ast.dump(node.test, include_attributes=False) == ast.dump(ast.parse("__name__ == '__main__'", mode='eval').body, include_attributes=False)]
    need(len(mains) == 1 and mains[0] is tree.body[-1], 'F04_UNIQUE_FINAL_MAIN_BOUNDARY_REQUIRED')
    lines = bound.decode('utf-8').splitlines(keepends=True)
    boundary = mains[0].lineno - 1
    changed = (''.join(lines[:boundary]) + CLOSED_F03_RECEIVE_COMPATIBILITY + '\n' + ''.join(lines[boundary:])).encode()
    after = ast.parse(changed)
    extra = ast.parse(CLOSED_F03_RECEIVE_COMPATIBILITY).body
    need(len(after.body) == len(tree.body) + len(extra) and ast.dump(ast.Module(body=after.body[:len(tree.body)-1] + [after.body[-1]], type_ignores=[]), include_attributes=False) == ast.dump(tree, include_attributes=False), 'F04_NONCOMPATIBILITY_TESTER_AST_CHANGED')
    need([ast.dump(node, include_attributes=False) for node in after.body[len(tree.body)-1:-1]] == [ast.dump(node, include_attributes=False) for node in extra], 'F04_EXACT_CLOSED_F03_COMPATIBILITY_REQUIRED')
    return changed
