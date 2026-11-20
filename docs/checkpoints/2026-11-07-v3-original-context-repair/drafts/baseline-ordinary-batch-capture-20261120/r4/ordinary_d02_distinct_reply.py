"""Assess exact closed R4 captures for the separate D02 ODT journey."""

from datetime import datetime
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import stat
from types import ModuleType


PHASES = ('D-02-ALT-ODT-01', 'D-02-ALT-ODT-02')
PLAN_SHA256 = (
    '088d47d6a8efbf63068bb8fff13c69af05478a20156960811ac1d170db46c4cf',
    'bab05e12b1465b984bf58acfd8b25507162b31c135dbb3623623951a06b10a05',
)
SOURCE_SHA256 = 'bae9af5c7d9d9a1ed4c4d6ebde175ea37d852209b1ab9f689569f78503e4d953'
SOURCE_BYTES = 1115
SOURCE_NAME = 'D02-Mednaya-otmel-v1.odt'
SOURCE_MIME = 'application/vnd.oasis.opendocument.text'
R4_SHA256 = '44577894f0669d305d2cd713048928c7ccbce265a40f1f6d09080b1fb62228bd'
PREP_SHA256 = '9239d8b97d7937bc8876f3f578a133812eac39394758c2e776bdc79aaa3e4d94'
DRIVER_SHA256 = '6885c9af1bd676abc660207954ec3f59ea64d99c6b504cc21f921fa6199f53d0'
NOMINAL_SHA256 = 'c7a1f135fc2995318db235241bc1eb266f74ca4363800936a6d7e15515c97fe8'
ORACLE_SHA256 = 'cd9c4f800a73a5adcbef5c412354dd73eb4eabf622c7aa1d89b56030f3a23147'
CONTEXT_SCHEMA = 'frw.root.d02-distinct-saved-context.v1'
CACHE = Path.home() / '.cache'
PREP = CACHE / 'FRW-ASTRA-D02-DISTINCT-ODT-20261120'
ORACLE_PATH = CACHE / 'FRW-ASTRA-BASELINE-D02-PASSIVE-20261120' / 'check_d02.py'
NOMINAL_PATH = Path.home() / (
    'jericho/Friday_rework/docs/checkpoints/2026-11-07-v3-original-context-repair/'
    'drafts/baseline-ordinary-batch-capture-20261120/r4/ordinary_d02_reply.py'
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return sha256(data).hexdigest()


def module(raw, path, expected_sha):
    require(type(raw) is bytes and digest(raw) == expected_sha, 'Pinned D02 code bytes changed')
    namespace = ModuleType('_d02_distinct_' + Path(path).stem)
    namespace.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), namespace.__dict__)
    return namespace


def read_exact(observer, value, *, expected_path=None, expected_sha=None):
    require(type(value) is dict and set(value) == {'path', 'bytes', 'sha256'}
            and type(value['path']) is str and type(value['bytes']) is int
            and 0 < value['bytes'] <= observer.MAX_JSON
            and type(value['sha256']) is str and re.fullmatch('[a-f0-9]{64}', value['sha256']),
            'Exact protected distinct D02 reference required')
    path = Path(value['path'])
    require(path.is_absolute() and str(path) == value['path'] and '..' not in path.parts
            and (expected_path is None or path == expected_path)
            and (expected_sha is None or value['sha256'] == expected_sha),
            'Distinct D02 reference selects different evidence')
    raw = observer.safe_read(path, value['bytes'])
    require(len(raw) == value['bytes'] and digest(raw) == value['sha256'],
            'Protected distinct D02 evidence bytes changed')
    return raw


def record(observer, raw):
    decoded = json.loads(raw, object_pairs_hook=observer.unique_object)
    require(type(decoded) is dict and observer.encoded(decoded) == raw,
            'Canonical distinct D02 record required')
    return decoded


class ReadStore:
    """The part of R4 Store used by the retained custody readers."""

    def __init__(self, observer, root):
        self.observer = observer
        self.root = Path(root)
        require(self.root.is_absolute() and '..' not in self.root.parts,
                'Absolute distinct D02 receiver root required')
        self.runs, self.captures, self.downloads = (self.root / name for name in ('runs', 'updates', 'downloads'))
        # Read the directory identities without constructing Store, which can mkdir.
        self.fence = self.identity()

    def identity(self):
        identities = []
        for directory in (self.root, self.runs, self.captures, self.downloads):
            info = self.observer.no_symlinks(directory).stat()
            require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
                    and stat.S_IMODE(info.st_mode) == 0o700, 'Private distinct D02 receiver required')
            identities.append((info.st_dev, info.st_ino))
        return identities

    def run_path(self, run_id):
        return self.observer.Store.run_path(self, run_id)

    def get(self, path, default=None):
        return self.observer.Store.get(self, path, default)


def prepare(observer):
    preparation = observer.safe_read(PREP / 'RESULT.json')
    require(digest(preparation) == PREP_SHA256, 'Exact distinct D02 preparation required')
    pinned = json.loads(preparation, object_pairs_hook=observer.unique_object)
    require(pinned['fixture']['mime_type'] == SOURCE_MIME
            and pinned['fixture']['file']['bytes'] == SOURCE_BYTES,
            'Distinct D02 ODT preparation changed')
    source_ref = pinned['fixture']['file']
    read_exact(observer, source_ref, expected_path=PREP / SOURCE_NAME, expected_sha=SOURCE_SHA256)
    plans = []
    for phase, expected_sha, row in zip(PHASES, PLAN_SHA256, pinned['ordered_phases'], strict=True):
        require(row['phase'] == phase and row['scenario_sha256'] == expected_sha,
                'Distinct D02 preparation phase changed')
        raw = read_exact(observer, row['plan'], expected_path=PREP / (phase + '.passive.json'),
                         expected_sha=expected_sha)
        plans.append(observer.validate_scenario(record(observer, raw)))
    nominal = module(observer.safe_read(NOMINAL_PATH, 65536, private=False), NOMINAL_PATH, NOMINAL_SHA256)
    driver_path = PREP / 'check_distinct_d02.py'
    driver = module(observer.safe_read(driver_path, 65536), driver_path, DRIVER_SHA256)
    oracle = module(observer.safe_read(ORACLE_PATH, 65536), ORACLE_PATH, ORACLE_SHA256)
    return plans, source_ref, nominal, driver, oracle


def route_matches(message, scenario, sender_id):
    sender, chat = message.get('from'), message.get('chat')
    return (type(sender) is dict and type(chat) is dict
            and type(sender.get('id')) is int and sender['id'] == sender_id
            and sender.get('is_bot') is True
            and type(chat.get('id')) is int and chat['id'] == scenario['peer_id']
            and chat.get('type') == 'private' and message.get('message_thread_id') is None
            and message.get('is_topic_message') is not True)


def upload_ack(observer, nominal, runner, run, upload):
    ref = run['sent_api_ack_reference']
    ack = runner.read_reference({key: ref[key] for key in ('basename', 'bytes', 'sha256')},
                                f"send-ack-{run['id']}-0-1.json")
    if ref['representation'] == 'botapi-wire-envelope-json':
        ack = ack['result']
    scenario = run['scenario']
    require(route_matches(ack, scenario, scenario['tester_id'])
            and observer.valid_input_ack(ack, upload, require_document_size=True)
            and nominal.MEDIA.intersection(ack) == {'document'} and 'text' not in ack
            and ack['document'].get('file_name') == SOURCE_NAME
            and ack['document'].get('mime_type') == SOURCE_MIME,
            'Distinct D02 original upload ACK omitted or changed exact metadata')
    return ack


def retained_reply(observer, nominal, runner, run, observation, captures, ack, upload):
    uid = observation['update_id']
    update, arrival = runner.committed_capture(run, uid)
    message = update['message']
    if upload is None:
        text, selected = nominal.reply_text(runner, run, observation, captures, ack)
    else:
        parent = message.get('reply_to_message')
        scenario = run['scenario']
        require(type(parent) is dict and route_matches(parent, scenario, scenario['tester_id'])
                and type(parent.get('message_id')) is int and parent['message_id'] == ack['message_id']
                and type(parent.get('date')) is int and parent['date'] == ack['date']
                and observer.valid_input_ack(parent, upload, require_document_size=True)
                and nominal.MEDIA.intersection(parent) == {'document'} and 'text' not in parent
                and parent['caption'] == ack['caption']
                and all(parent['document'].get(key) == ack['document'][key] for key in
                        ('file_unique_id', 'file_name', 'mime_type', 'file_size')),
                'Distinct D02 reply parent differs from the exact upload ACK')
        text = message.get('text')
        selected = {'reply_id': message.get('message_id'), 'arrival_update': uid,
                    'text_sha256': observation['text_sha256']}
    require(observation['kind'] == 'reply_text' and observation.get('text_source') in (None, 'text')
            and captures.get(uid) == arrival and observation['raw_update'] == arrival['raw_update']
            and run['sent_at'] <= arrival['arrived_at'] < run['capture_until']
            and update['update_id'] == uid and message['message_id'] == observation['message_id']
            and run['sent_date'] <= message['date'] <= run['capture_until']
            and route_matches(message, run['scenario'], run['scenario']['peer_id'])
            and not nominal.MEDIA.intersection(message)
            and type(text) is str and text == observation['text']
            and digest(text.encode('utf-8')) == selected['text_sha256'],
            'Distinct D02 reply must be committed direct private text within the original window')
    receipt = {key: observation['receipt_' + key] for key in ('path', 'bytes', 'sha256')}
    receipt_name = f"{run['id']}-{selected['reply_id']}-{selected['text_sha256']}.text-receipt.json"
    read_exact(observer, receipt, expected_path=runner.store.downloads / receipt_name)
    return text, dict(selected, arrived_at=arrival['arrived_at'], raw_update=arrival['raw_update'],
                      text_receipt=receipt)


def assess_phase(observer, nominal, driver, oracle, store, stage, cursor, scenario, source):
    phase, run_id, run_ref = stage['phase'], stage['run_id'], stage['run_ref']
    run = nominal.pinned_record(observer, run_ref, store.run_path(run_id))
    require(run.get('id') == run_id and run.get('scenario') == scenario
            and run.get('scenario_sha256') == digest(observer.encoded(scenario))
            and type(run.get('step')) is int and run['step'] == 0
            and type(run.get('send_attempts')) is int and run['send_attempts'] == 1
            and type(run.get('repeat_count')) is int and run['repeat_count'] == 0
            and run.get('send_state') == 'sent' and run.get('status') == 'EVIDENCE_READY'
            and run.get('capture_window_complete') is True,
            'Exact closed distinct D02 phase with one send required')
    created = datetime.fromisoformat(run['created_at'])
    deadline, until = run['deadline'], run['capture_until']
    require(created.utcoffset() is not None and type(deadline) in (int, float)
            and math.isfinite(deadline) and abs(deadline - created.timestamp() - 300) <= 1
            and until == run['sent_at'] + 180,
            'Distinct D02 original 180-second window and 300-second deadline required')

    runner = observer.Runner(store, None)
    runner.verify_reply_custody(run, cursor)
    captures, _, drain = runner.receive_inventory(run, cursor, terminal=True)
    terminal, poll = drain.get('complete'), runner.read_poll_intent(run)
    require(terminal is not None and until <= terminal['completed_at'] < deadline
            and (poll is None or poll['outcome'] != 'PENDING'),
            'Distinct D02 original receiver window did not settle')
    upload = scenario['steps'][0].get('input')
    if upload is not None:
        ack = upload_ack(observer, nominal, runner, run, upload)
        body, content_type = observer.document_multipart(upload, source)
        metadata = run['request_metadata']
        require(metadata['body_sha256'] == digest(body) and metadata['body_bytes'] == len(body)
                and metadata['content_type'] == content_type,
                'Distinct D02 protected multipart task differs from the exact ODT bytes')
    else:
        ack = nominal.original_ack(runner, run)
        require(route_matches(ack, scenario, scenario['tester_id'])
                and not nominal.MEDIA.intersection(ack) and 'caption' not in ack,
                'Distinct D02 follow-up ACK does not bind the exact private text route')

    observations = run['observations']
    updates = [item['update_id'] for item in observations]
    require(run.get('reply_outcome') == 'RECEIVED_UNGRADED' and updates and updates == sorted(set(updates)),
            'Distinct D02 phase has no complete ordered retained answer')
    retained = [retained_reply(observer, nominal, runner, run, item, captures, ack, upload)
                for item in observations]
    answer = '\n'.join(text for text, _ in retained)
    require(answer.strip(), 'Distinct D02 phase has no substantive retained answer')
    screen = driver.semantic_checks(oracle, phase, answer, source) if len(answer) <= 8000 else None
    keys = ('scenario_sha256', 'sent_message_id', 'send_intent_at', 'send_dispatch_at', 'sent_at',
            'capture_start_offset', 'capture_until', 'deadline', 'receive_head',
            'sent_task_reference', 'sent_api_ack_reference', 'sent_window_reference')
    return {
        **{key: run[key] for key in keys}, 'phase': phase, 'run_id': run_id, 'run': run_ref,
        'source_sha256': SOURCE_SHA256, 'context': stage['context_ref'],
        'capture_end_offset': terminal['offset'], 'terminal_completed_at': terminal['completed_at'],
        'replies': [reference for _, reference in retained],
        'answer_sha256': digest(answer.encode('utf-8')), 'screen': screen,
        'status': 'CONTENT_MATCH_ONLY' if screen and all(screen.values()) else 'REVIEW_REQUIRED',
    }


def check_context(observer, store, context_ref, source_ref, original, scenario):
    context = record(observer, read_exact(observer, context_ref))
    expected = {
        'schema': CONTEXT_SCHEMA, 'receiver_root': str(store.root), 'source': source_ref,
        'upload_ack': original['sent_api_ack_reference'],
        'dialog': {key: scenario[key] for key in ('peer_id', 'peer_username', 'tester_id')},
    }
    require(context.keys() == expected.keys() | {'ordinary_context'}
            and observer.encoded({key: context[key] for key in expected}) == observer.encoded(expected),
            'Distinct D02 receiver, dialog, active source or original upload ACK context changed')
    read_exact(observer, context['ordinary_context'])
    return context


def assess_saved_series(observer_source, store_root, *, stages, cursor_ref, predecessor_ref=None):
    """Read an ordered prefix. The caller holds the exact receiver and context pins.

    The second capture requires the saved first-stage result and identical
    caller-selected context. Receiver custody, native conversation continuity,
    source use and authority have separate evidence requirements.
    """
    require(type(stages) in (list, tuple) and 1 <= len(stages) <= len(PHASES)
            and all(type(stage) is dict and set(stage) == {'phase', 'run_id', 'run_ref', 'context_ref'}
                    and stage['phase'] == phase for stage, phase in zip(stages, PHASES)),
            'Exact distinct D02 phase prefix required')
    ordered_pair = len(stages) == len(PHASES)
    context_ref = stages[0]['context_ref']
    require((ordered_pair and predecessor_ref is not None and context_ref is not None
             and context_ref == stages[1]['context_ref'])
            or (not ordered_pair and predecessor_ref is None),
            'Distinct D02 follow-up requires the saved first result and identical pinned context')
    observer = module(observer_source, 'pinned-r4.py', R4_SHA256)
    if ordered_pair:
        require(type(stages[1]['context_ref']) is dict
                and observer.encoded(context_ref) == observer.encoded(stages[1]['context_ref']),
                'Distinct D02 follow-up context pin changed')
    store = ReadStore(observer, store_root)
    cursor_path = store.root / 'cursor.json'
    cursor = record(observer, read_exact(observer, cursor_ref, expected_path=cursor_path))
    plans, source_ref, nominal, driver, oracle = prepare(observer)
    upload = plans[0]['steps'][0]['input']
    source = observer.read_document_input(upload, lambda: None)
    first = assess_phase(observer, nominal, driver, oracle, store, stages[0], cursor, plans[0], source)
    results = [first]
    context = (check_context(observer, store, context_ref, source_ref, first, plans[0])
               if context_ref is not None else None)
    if ordered_pair:
        predecessor = read_exact(observer, predecessor_ref)
        require(first['status'] == 'CONTENT_MATCH_ONLY' and observer.encoded(first) == predecessor,
                'Distinct D02 predecessor must be the actual closed matching first result')
        second = assess_phase(observer, nominal, driver, oracle, store, stages[1], cursor, plans[1], source)
        require(first['run_id'] != second['run_id']
                and second['capture_start_offset'] >= first['capture_end_offset']
                and min(second['send_intent_at'], second['send_dispatch_at'])
                    >= max(first['deadline'], first['terminal_completed_at']),
                'Distinct D02 follow-up began before original predecessor settlement')
        results.append(second)

    message_ids = [value for item in results for value in
                   [item['sent_message_id'], *(reply['reply_id'] for reply in item['replies'])]]
    require(len(message_ids) == len(set(message_ids)), 'Distinct D02 tester message identity was reused')
    for item in results:
        read_exact(observer, item['run'], expected_path=store.run_path(item['run_id']))
    read_exact(observer, cursor_ref, expected_path=cursor_path)
    if context is not None:
        read_exact(observer, context_ref)
        read_exact(observer, context['ordinary_context'])
    if predecessor_ref is not None:
        read_exact(observer, predecessor_ref)
    require(observer.read_document_input(upload, lambda: None) == source and store.identity() == store.fence,
            'Distinct D02 protected ODT or receiver identity changed during assessment')
    return {'stages': results, 'cursor': cursor_ref, 'predecessor': predecessor_ref,
            'native_conversation_continuity': 'OPEN', 'native_source_provenance': 'OPEN',
            'formal_acceptance': 'OPEN'}
