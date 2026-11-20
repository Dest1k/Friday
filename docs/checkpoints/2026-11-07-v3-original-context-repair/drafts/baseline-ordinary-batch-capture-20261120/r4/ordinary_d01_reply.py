"""Assess the exact saved D01 alternative after the selected R4 caller closes."""

from hashlib import sha256
import json
from pathlib import Path
import re
from types import ModuleType

SCENARIO_SHA256 = 'a985da3b6f729b51edd0f19971fe97d0e1606215cd06403bc49c636471a81632'
SOURCE_SHA256 = '94b36b19e8665ecf52c9ada141b4d5860545ba40559aeca977d4db88b38441c2'
VERIFIER_SHA256 = '16be9b4aff105f4ee04715f984acecdafbc7d563e1d86b0a3ac63cda1d726bcb'
RTF_SCENARIO_SHA256 = '45e1732b0d49020182a3a9f2d67056b8c11d9c0f314240de077eb6fd19a13641'
RTF_SOURCE_SHA256 = '008f55eddd87fe35f7a40413d97eecba9a293d2029db9a32420d0973001b3535'
RTF_VERIFIER_SHA256 = '7060f9386c2be154a1eab1db05056a75c37651aed9f0127c728a7e95ad5241ac'
PINNED_SCENARIOS = {
    SCENARIO_SHA256: (SOURCE_SHA256, VERIFIER_SHA256, {}),
    RTF_SCENARIO_SHA256: (RTF_SOURCE_SHA256, RTF_VERIFIER_SHA256, {'source_format': 'rtf'}),
}
DOCX_MIME = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
MAX_DOCX_BYTES = 8 * 1024 * 1024
MEDIA = {
    'animation', 'audio', 'contact', 'dice', 'document', 'game', 'invoice',
    'location', 'paid_media', 'passport_data', 'photo', 'poll', 'sticker',
    'story', 'successful_payment', 'venue', 'video', 'video_note', 'voice',
}


class InvalidEvidence(ValueError):
    """The saved state cannot support D01 content assessment."""


def require(condition, message):
    if not condition:
        raise InvalidEvidence(message)


def digest(raw):
    return sha256(raw).hexdigest()


def check_reference(reference, path, limit):
    require(type(reference) is dict and set(reference) == {'path', 'bytes', 'sha256'}
            and reference['path'] == str(path) and path.is_absolute()
            and type(reference['bytes']) is int and 0 < reference['bytes'] <= limit
            and type(reference['sha256']) is str and re.fullmatch('[0-9a-f]{64}', reference['sha256']),
            'Exact saved D01 reference required')


def read_exact(observer, reference, path, limit):
    check_reference(reference, path, limit)
    raw = observer.safe_read(path, reference['bytes'])
    require(len(raw) == reference['bytes'] and digest(raw) == reference['sha256'],
            'Saved D01 reference bytes changed')
    return raw


def canonical(observer, raw):
    value = json.loads(raw, object_pairs_hook=observer.unique_object)
    require(type(value) is dict and observer.encoded(value) == raw, 'Saved D01 record is not canonical')
    return value


def pick_reply(observer, runner, run, cursor):
    # Follow the S01 reader's closed receiver sequence and original private ACK.
    runner.verify_reply_custody(run, cursor)
    captures, _, drain = runner.receive_inventory(run, cursor, terminal=True)
    completion = drain.get('complete')
    poll_intent = runner.read_poll_intent(run)
    require(completion is not None and (poll_intent is None or poll_intent['outcome'] != 'PENDING'),
            'D01 receive journal did not complete the original window')

    observations = run['observations']
    require(len(observations) == 1, 'D01 requires one unambiguous retained reply')
    observation = observations[0]
    uid = observation['update_id']
    update, arrival = runner.committed_capture(run, uid)
    require(arrival == captures.get(uid) and (
            run['sent_at'] <= arrival['arrived_at'] < run['capture_until']),
            'D01 reply arrived outside the original committed window')
    message = update['message']
    parent = message.get('reply_to_message')
    chat, sender = message['chat'], message['from']
    peer_id = run['scenario']['peer_id']
    require(update['update_id'] == uid and message['message_id'] == observation['message_id']
            and chat['id'] == sender['id'] == peer_id and chat['type'] == 'private'
            and sender['is_bot'] is True
            and isinstance(parent, dict) and parent.get('message_id') == run['sent_message_id']
            and message.get('message_thread_id') is None and message.get('is_topic_message') is not True
            and parent.get('message_thread_id') is None and parent.get('is_topic_message') is not True
            and run['sent_date'] <= message['date'] <= run['capture_until'],
            'D01 reply must directly bind the original unthreaded private ACK')
    if observation['kind'] == 'reply_text':
        require(not MEDIA.intersection(message) and type(message.get('text')) is str
                and observation['raw_update'] == arrival['raw_update'],
                'D01 expected substantive retained inline text')
        data = message['text'].encode('utf-8')
        require(digest(data) == observation['text_sha256'], 'D01 retained text differs from the receipt')
        media = 'chat-text'
    else:
        require(observation['kind'] == 'document' and MEDIA.intersection(message) == {'document'}
                and 'text' not in message and observation.get('complete_artifact') is True
                and observation.get('artifact_acceptance') == 'RECEIVED_UNGRADED',
                'D01 expected a complete quarantined recipient DOCX')
        advertised, downloaded = message['document'], observation['get_file']
        name = advertised.get('file_name')
        require(type(name) is str and Path(name).suffix.lower() == '.docx'
                and advertised.get('mime_type') == DOCX_MIME
                and observation['advertised_document'] == advertised
                and all(type(advertised.get(k)) is str and advertised[k]
                        and downloaded.get(k) == advertised[k] for k in ('file_id', 'file_unique_id'))
                and type(observation['bytes']) is int
                and observation['bytes'] == advertised.get('file_size') == downloaded.get('file_size'),
                'D01 recipient DOCX identity, type or byte count differs')
        path = runner.store.downloads / (
            f"{run['id']}-{observation['message_id']}-{observation['sha256']}.bin")
        reference = {key: observation[key] for key in ('path', 'bytes', 'sha256')}
        data = read_exact(observer, reference, path, MAX_DOCX_BYTES)
        media = 'docx'
    custody = {key: run[key] for key in
               ('scenario_sha256', 'sent_message_id', 'capture_until', 'deadline',
                'sent_api_ack_reference', 'sent_task_reference', 'sent_window_reference', 'receive_head')}
    custody.update(reply_update_id=uid, reply_message_id=observation['message_id'],
                   arrived_at=arrival['arrived_at'], completed_at=completion['completed_at'],
                   raw_update=arrival['raw_update'], media=media,
                   receipt={key: observation['receipt_' + key] for key in ('path', 'bytes', 'sha256')},
                   reply_bytes=len(data), reply_sha256=digest(data))
    if media == 'docx':
        custody['recipient_file'] = reference
    return data, custody


def assess_saved_reply(observer, store, *, run_id, run_ref, cursor_ref, verifier_source):
    """Read pinned records and assess their one bound reply. The caller owns settlement pins."""
    require(type(run_id) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,63}', run_id),
            'Exact D01 run ID required')
    run_path, cursor_path = store.run_path(run_id), store.root / 'cursor.json'
    run_raw = read_exact(observer, run_ref, run_path, observer.MAX_JSON)
    cursor_raw = read_exact(observer, cursor_ref, cursor_path, observer.MAX_JSON)
    run = canonical(observer, run_raw)
    cursor = canonical(observer, cursor_raw)
    scenario = run.get('scenario')
    scenario_sha = digest(observer.encoded(scenario))
    require(scenario_sha in PINNED_SCENARIOS, 'Exact closed D01 alternative and one ACK required')
    source_sha, verifier_sha, source_options = PINNED_SCENARIOS[scenario_sha]
    require(type(verifier_source) is bytes and digest(verifier_source) == verifier_sha,
            'Exact existing D01 verifier required')
    require(run.get('id') == run_id and run.get('scenario_sha256') == scenario_sha
            and type(run.get('step')) is int and run['step'] == 0
            and type(run.get('send_attempts')) is int and run['send_attempts'] == 1
            and type(run.get('repeat_count')) is int and run['repeat_count'] == 0
            and type(run.get('sent_message_id')) is int and run['sent_message_id'] > 0
            and run.get('sent_ids') == [run['sent_message_id']] and run.get('send_state') == 'sent'
            and run.get('status') == 'EVIDENCE_READY' and run.get('capture_window_complete') is True,
            'Exact closed D01 alternative and one ACK required')
    upload = scenario['steps'][0]['input']
    require(upload['sha256'] == run['request_metadata']['input_sha256'] == source_sha,
            'D01 source differs from admitted upload')
    runner = observer.Runner(store, None)
    response, custody = pick_reply(observer, runner, run, cursor)
    source = observer.read_document_input(upload, lambda: None)
    require(digest(source) == source_sha, 'D01 protected source bytes changed')
    assessor = ModuleType('_d01_pinned_content_assessor')
    assessor.__file__ = '<pinned D01 check_summary.py>'
    exec(compile(verifier_source, assessor.__file__, 'exec'), assessor.__dict__)
    try:
        assessment = assessor.verify_summary(source, response, custody['media'], **source_options)
    except assessor.NeedsReview as error:
        assessment = {'status': 'REVIEW_REQUIRED', 'reason': str(error)}
    if run.get('reply_outcome') != 'RECEIVED_UNGRADED':
        raise InvalidEvidence('D01 saved reply outcome changed')
    require(read_exact(observer, run_ref, run_path, observer.MAX_JSON) == run_raw
            and read_exact(observer, cursor_ref, cursor_path, observer.MAX_JSON) == cursor_raw,
            'D01 saved run or cursor changed during assessment')
    return dict(run_id=run_id, run=run_ref, cursor=cursor_ref, source_sha256=digest(source),
                custody=custody, assessment=assessment, formal_acceptance='NOT_ESTABLISHED')
