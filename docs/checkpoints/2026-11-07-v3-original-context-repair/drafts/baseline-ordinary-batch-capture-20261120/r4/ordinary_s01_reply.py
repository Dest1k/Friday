"""Read the exact retained S01 reply from an already closed R4 run."""

from hashlib import sha256


SCENARIO_SHA256 = '8a028fd974f9290f8cf978e7d2d7ab75f66cb2bb468606365f5e5512468b057d'
MEDIA = {
    'animation', 'audio', 'contact', 'dice', 'document', 'game', 'invoice',
    'location', 'paid_media', 'passport_data', 'photo', 'poll', 'sticker',
    'story', 'successful_payment', 'venue', 'video', 'video_note', 'voice',
}


def read_reply(runner, run, cursor, *, expected_run_id):
    """Return verbatim UTF-8 bytes and their custody metadata.

    The caller supplies the protected run/cursor and the reviewed R4 observer
    with no transport. Native ingress, delivery and content grading are separate.
    """
    if (runner.api is not None or not isinstance(cursor, dict)
            or run.get('id') != expected_run_id or run.get('scenario_sha256') != SCENARIO_SHA256
            or type(run.get('step')) is not int or run['step'] != 0
            or type(run.get('send_attempts')) is not int or run['send_attempts'] != 1
            or run.get('send_state') != 'sent' or run.get('status') != 'EVIDENCE_READY'
            or run.get('capture_window_complete') is not True):
        raise ValueError('Exact closed S01 run and read-only observer required')

    runner.verify_reply_custody(run, cursor)
    captures, _, drain = runner.receive_inventory(run, cursor, terminal=True)
    terminal = drain.get('complete')
    poll_intent = runner.read_poll_intent(run)
    if terminal is None or (poll_intent is not None and poll_intent['outcome'] == 'PENDING'):
        raise ValueError('S01 receive journal did not complete the original window')

    observations = run['observations']
    if len(observations) != 1 or observations[0].get('kind') != 'reply_text':
        raise ValueError('S01 requires exactly one retained text reply')
    receipt = observations[0]
    uid = receipt['update_id']
    update, arrival = runner.committed_capture(run, uid)
    if (arrival != captures.get(uid) or arrival['raw_update'] != receipt['raw_update']
            or not run['sent_at'] <= arrival['arrived_at'] < run['capture_until']):
        raise ValueError('S01 reply arrival does not bind the original capture window')

    message = update['message']
    parent = message.get('reply_to_message')
    chat, sender = message['chat'], message['from']
    peer_id = run['scenario']['peer_id']
    if (update['update_id'] != uid or message['message_id'] != receipt['message_id']
            or chat['id'] != peer_id or chat['type'] != 'private'
            or sender['id'] != peer_id or sender['is_bot'] is not True
            or not isinstance(parent, dict) or parent.get('message_id') != run['sent_message_id']
            or message.get('message_thread_id') is not None or message.get('is_topic_message') is True
            or parent.get('message_thread_id') is not None or parent.get('is_topic_message') is True
            or not run['sent_date'] <= message['date'] <= run['capture_until']
            or MEDIA.intersection(message)):
        raise ValueError('S01 reply must be a direct unthreaded private text to the original ACK')

    raw_text = message['text'].encode('utf-8')
    if sha256(raw_text).hexdigest() != receipt['text_sha256']:
        raise ValueError('S01 raw text digest differs from the retained receipt')
    return raw_text, {
        'run_id': run['id'], 'scenario_sha256': run['scenario_sha256'],
        'source_sha256': run['request_metadata']['input_sha256'],
        'request_body_sha256': run['request_metadata']['body_sha256'],
        'sent_message_id': run['sent_message_id'], 'message_id': receipt['message_id'],
        'update_id': uid, 'arrived_at': arrival['arrived_at'],
        'capture_until': run['capture_until'], 'terminal_completed_at': terminal['completed_at'],
        'send_ack': run['sent_api_ack_reference'], 'send_task': run['sent_task_reference'],
        'send_window': run['sent_window_reference'], 'receive_head': run['receive_head'],
        'raw_update': receipt['raw_update'], 'receipt_path': receipt['receipt_path'],
        'receipt_sha256': receipt['receipt_sha256'], 'receipt_bytes': receipt['receipt_bytes'],
        'text_sha256': receipt['text_sha256'], 'text_bytes': len(raw_text),
    }
