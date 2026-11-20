"""Compare a checked D02 send ACK with the observed native receiving receipts.

The caller owns ACK custody, the trusted route and window coverage. A match
among the supplied observations establishes neither completeness nor admission.
"""

from hashlib import sha256
import re


ROUTE_FIELDS = ('session_key', 'source_profile', 'transport_profile', 'runtime_profile')
DOMAIN = b'friday.telegram.payload.v1\x00'


def _positive_native_id(value):
    return type(value) is str and re.fullmatch(r'[1-9][0-9]{0,19}', value) is not None


def _request_witness(ack, scenario):
    if (scenario['tester_id'] == scenario['peer_id']
            or ack['from']['is_bot'] is not True
            or type(ack['from']['id']) is not int or ack['from']['id'] != scenario['tester_id']
            or type(ack['chat']['id']) is not int or ack['chat']['id'] != scenario['peer_id']
            or ack['chat']['type'] != 'private'
            or ack.get('message_thread_id') is not None or ack.get('is_topic_message') is True
            or ack.get('reply_to_message') is not None
            or type(ack['date']) is not int or ack['date'] <= 0
            or type(ack['message_id']) is not int or ack['message_id'] <= 0):
        raise ValueError('D02 send acknowledgement differs from the exact tester route')
    step, = scenario['steps']
    upload = step.get('input')
    kind = 'text' if upload is None else 'caption'
    value = ack.get(kind)
    if type(value) is not str or not value or '\x00' in value:
        raise ValueError('D02 acknowledgement lacks the original SDK-compatible value')
    encoded = value.encode('utf-8')
    if len(encoded) > 16384:
        raise ValueError('D02 acknowledgement value exceeds the native receipt bound')
    if upload is None:
        if ack['text'] != step['request'] or 'caption' in ack or 'document' in ack:
            raise ValueError('D02 text acknowledgement changed')
    else:
        doc = ack['document']
        if (upload['kind'] != 'document' or 'text' in ack
                or doc['file_name'] != upload['filename'] or doc['mime_type'] != upload['mime_type']
                or type(doc.get('file_size')) is not int or doc['file_size'] != upload['stat']['size_bytes']
                or type(doc.get('file_unique_id')) is not str or not doc['file_unique_id']):
            raise ValueError('D02 upload acknowledgement changed')
    return {'kind': kind, 'date': ack['date'],
            'sha256': sha256(DOMAIN + kind.encode('ascii') + b'\x00' + encoded).hexdigest()}


def _matching_attachment(message, document, upload):
    media = message['media']
    if upload is None:
        return media == []
    if type(media) is not list or len(media) != 1:
        return None
    item, = media
    origin, content = item.get('origin'), item.get('content')
    if (type(origin) is not dict
            or not all(origin.get(key) == message[key] for key in ('bot_id', 'chat_id', 'thread_id', 'message_id'))
            or not isinstance(origin.get('file_unique_id'), str) or not origin['file_unique_id']
            or type(origin.get('declared_bytes')) is not int
            or not isinstance(item.get('mime_type'), str) or not item['mime_type']
            or type(content) is not dict or type(content.get('size_bytes')) is not int
            or type(content.get('sha256')) is not str or re.fullmatch(r'[a-f0-9]{64}', content['sha256']) is None):
        return None
    return (origin['file_unique_id'] == document['file_unique_id']
            and origin['declared_bytes'] == document['file_size']
            and item['mime_type'] == document['mime_type']
            and content['size_bytes'] == document['file_size']
            and content['sha256'] == upload['sha256'])


def match_observed_ingress(ack, scenario, route, observations):
    """Return a comparison of a validated ACK with bounded native observations.

    Use the original ACK from D02's R4 upload_ack or original_ack path.
    Each observation is (base receipt, optional payload witness) from
    independently verified state. Incomplete same-route witnesses prevent an
    unqualified match. The function never asserts closed native coverage.
    """
    if (type(route) is not dict or set(route) != set(ROUTE_FIELDS)
            or any(type(value) is not str for value in route.values())
            or not all(route[key] for key in ROUTE_FIELDS if key != 'source_profile')
            or type(observations) not in (list, tuple)
            or len(observations) > scenario['max_updates']):
        raise ValueError('D02 needs a pinned route and a bounded receipt inventory')
    wanted = _request_witness(ack, scenario)
    upload = scenario['steps'][0].get('input')
    peer, tester = str(scenario['peer_id']), str(scenario['tester_id'])
    matching, update_ids, message_ids = [], set(), set()
    missing_payload = missing_attachment = 0

    for receipt, payload in observations:
        if receipt['platform'] != 'telegram' or any(receipt[key] != route[key] for key in ROUTE_FIELDS):
            continue
        message = receipt['message']
        if (message['bot_id'], message['user_id'], message['chat_id'], message['thread_id']) != (peer, tester, tester, ''):
            continue
        message_id, update_id = message['message_id'], message['platform_update_id']
        if (receipt.get('chat_type') != 'dm' or not _positive_native_id(message_id)
                or not _positive_native_id(update_id)
                or update_id in update_ids or message_id in message_ids):
            raise ValueError('D02 direct receiving route contains missing or duplicate native identities')
        update_ids.add(update_id)
        message_ids.add(message_id)
        parent = message['reply_to_message_id']
        if parent != '':
            if not _positive_native_id(parent):
                raise ValueError('D02 native reply parent is malformed')
            continue
        if payload is None:
            missing_payload += 1
            continue
        if (type(payload) is not dict or payload.keys() != wanted.keys()
                or type(payload['date']) is not int or payload['date'] <= 0
                or payload['kind'] not in ('text', 'caption')
                or type(payload['sha256']) is not str or re.fullmatch(r'[a-f0-9]{64}', payload['sha256']) is None):
            raise ValueError('D02 observed payload witness is malformed')
        if payload != wanted:
            continue
        attached = _matching_attachment(message, ack.get('document'), upload)
        if attached is None:
            missing_attachment += 1
        elif attached:
            matching.append({'message_id': message_id, 'update_id': update_id})

    if len(matching) > 1:
        state = 'AMBIGUOUS_OBSERVED_MATCHES'
    elif missing_payload or missing_attachment:
        state = 'INCOMPLETE_OBSERVED_WITNESSES'
    elif matching:
        state = 'ONE_OBSERVED_MATCH'
    else:
        state = 'NO_OBSERVED_MATCH'
    return {'state': state, 'matching': matching, 'missing_payload_witnesses': missing_payload,
            'missing_attachment_witnesses': missing_attachment, 'native_window_complete': None}
