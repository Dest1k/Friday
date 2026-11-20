"""Check an independently retained D02 upload against the current ordinary session."""

from collections import namedtuple
from contextlib import closing
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import stat
import time


CONTEXT = 'frw.root.d02-distinct-saved-context.v1'
CONTINUITY = 'frw.root.d02-native-upload-continuity.v1'
SOURCE_NAME = 'D02-Mednaya-otmel-v1.odt'
SOURCE_SHA = 'bae9af5c7d9d9a1ed4c4d6ebde175ea37d852209b1ab9f689569f78503e4d953'
SOURCE_BYTES = 1115
ACK_NAME = 'send-ack-root-d02-alt-odt-01-v3-20261121-0-1.json'
MAX_RECORD = 65536

# These projections supply data to the native read/validation functions. They
# have no authority or active-turn lifecycle and never reach the live resolver.
AnchorPolicy = namedtuple('AnchorPolicy', 'principal profile key binding')
AnchorSession = namedtuple('AnchorSession', 'session_id session_key')


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def encoded(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, allow_nan=False) + '\n').encode()


def digest(raw):
    return sha256(raw).hexdigest()


def is_digest(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


def native_id(value):
    return type(value) is str and re.fullmatch('[1-9][0-9]{0,19}', value) is not None


def unique(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, 'D02 duplicate protected record field')
        result[key] = value
    return result


def absolute(value):
    path = Path(value)
    need(path.is_absolute() and str(path) == str(value) and '..' not in path.parts,
         'D02 exact absolute protected path required')
    return path


def protected_record(ref, checked_read):
    need(type(ref) is dict and set(ref) == {'path', 'bytes', 'sha256'}
         and type(ref['path']) is str and type(ref['bytes']) is int
         and 0 < ref['bytes'] <= MAX_RECORD and is_digest(ref['sha256']),
         'D02 exact protected context reference required')
    raw = checked_read(absolute(ref['path']), limit=ref['bytes'], private=True)
    need(type(raw) is bytes and len(raw) == ref['bytes'] and digest(raw) == ref['sha256'],
         'D02 protected context bytes changed')
    value = json.loads(raw, object_pairs_hook=unique)
    need(type(value) is dict and encoded(value) == raw, 'D02 protected context must be canonical')
    return value


def signature(path, *, directory=False):
    info = path.lstat()
    need(path.resolve(strict=True) == path and info.st_uid == os.getuid()
         and (stat.S_ISDIR(info.st_mode) if directory else
              stat.S_ISREG(info.st_mode) and info.st_nlink == 1)
         and stat.S_IMODE(info.st_mode) == (0o700 if directory else 0o600),
         'D02 retained custody path is not private and owned')
    base = (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_nlink)
    return base if directory else base + (info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def file_identity_sha256(path):
    """Compute the protected stat pin at the independently verified upload."""
    return digest(encoded(signature(absolute(path))))


class AnchorReadStore:
    """Only the local reader interface needed by the native anchor snapshot."""

    def __init__(self, path, native_fork_check):
        self.path = path
        self._read_budget = self
        self._reading = False
        self._native_fork_check = native_fork_check

    def acquire(self, store):
        if store is not self or self._reading:
            return False
        self._reading = True
        return True

    def release(self):
        self._reading = False

    def _connect_read_only(self, *, timeout):
        need(self._reading, 'D02 protected read snapshot missing')
        connection = sqlite3.connect(self.path.as_uri() + '?mode=ro', uri=True,
                                     timeout=timeout, isolation_level=None)
        connection.row_factory = sqlite3.Row
        return connection

    def _is_explicit_fork_child_row(self, row, *, include_reset):
        return self._native_fork_check(None, row, include_reset=include_reset)

    def fence(self):
        files = tuple(signature(self.path.with_name(self.path.name + suffix))
                      for suffix in ('', '-wal', '-shm'))
        # SQLite can change read marks in the pre-existing mapped SHM. Check its
        # namespace and extent alongside the durable main/WAL versions.
        return files[:2] + (files[2][:6],)

    def check_carrier_uniqueness(self, selector, message_id, deadline):
        remaining = deadline - time.monotonic()
        need(remaining > 0 and self.acquire(self), 'D02 protected carrier read budget exhausted')
        try:
            with closing(self._connect_read_only(timeout=min(remaining, 0.2))) as conn:
                conn.execute('PRAGMA query_only=ON')
                conn.set_progress_handler(lambda: int(time.monotonic() >= deadline), 1000)
                conn.execute('BEGIN')
                rows = conn.execute(
                    "SELECT id FROM messages WHERE session_id = ? AND platform_message_id = ? "
                    "AND role = 'user' LIMIT 2", (selector[0], message_id)).fetchall()
            need(len(rows) == 1 and rows[0]['id'] == selector[1],
                 'D02 native upload carrier is absent or ambiguous')
        finally:
            self.release()


def check_ack(outer, expected_ack, receiver_root, checked_read):
    need(type(expected_ack) is dict
         and set(expected_ack) == {'basename', 'bytes', 'sha256', 'representation'}
         and expected_ack['basename'] == ACK_NAME
         and type(expected_ack['bytes']) is int and 0 < expected_ack['bytes'] <= MAX_RECORD
         and is_digest(expected_ack['sha256'])
         and expected_ack['representation'] in ('decoded-message-json', 'botapi-wire-envelope-json')
         and outer['upload_ack'] == expected_ack
         and outer['receiver_root'] == str(receiver_root), 'D02 closed upload ACK pin changed')
    raw = checked_read(receiver_root / ACK_NAME, limit=expected_ack['bytes'], private=True)
    need(type(raw) is bytes and len(raw) == expected_ack['bytes'] and digest(raw) == expected_ack['sha256'],
         'D02 closed upload ACK bytes changed')


def check_retained_upload(context_ref, *, session_key, session_id, profile_home, principal, binding,
                          expected_upload_ack, expected_ingress_settlement_sha256, receiver_root,
                          checked_read, native_anchor, native_fork_check, deadline):
    """Return custody hashes for the fixed, already-reviewed phase-one ODT."""
    need(type(deadline) in (int, float) and math.isfinite(deadline) and time.monotonic() < deadline,
         'D02 retained observation deadline exhausted')
    deadline = min(deadline, time.monotonic() + 0.5)
    need(type(principal) is tuple and len(principal) == 4 and principal[:2] == ('telegram', 'default')
         and native_id(principal[2]) and native_id(principal[3]) and principal[2] != principal[3],
         'D02 exact active Telegram principal required')
    platform, _, bot_id, user_id = principal
    home = absolute(profile_home)
    receiver = absolute(receiver_root)
    profile = 'telegram-bot-' + user_id
    fields = ('platform', 'transport_profile', 'account_id', 'user_id')
    need(home.name == profile and session_key == f'agent:{profile}:telegram:dm:{user_id}'
         and type(session_id) is str and re.fullmatch('[A-Za-z0-9_-]{1,96}', session_id)
         and type(binding) is dict and all(binding.get(k) == v for k, v in zip(fields, principal, strict=True))
         and binding.get('runtime_profile') == profile and type(binding.get('tools')) is list
         and {'session_search', 'read_file'} <= set(binding['tools']),
         'D02 current session, profile or source-read rights changed')
    outer = protected_record(context_ref, checked_read)
    need(set(outer) == {'schema', 'receiver_root', 'source', 'upload_ack', 'dialog', 'ordinary_context'}
         and outer['schema'] == CONTEXT, 'D02 exact saved upload context required')
    dialog, source = outer['dialog'], outer['source']
    need(type(dialog) is dict and set(dialog) == {'peer_id', 'peer_username', 'tester_id'}
         and type(dialog['tester_id']) is int and str(dialog['tester_id']) == user_id
         and type(dialog['peer_id']) is int and str(dialog['peer_id']) == bot_id
         and type(dialog['peer_username']) is str and 0 < len(dialog['peer_username']) <= 64
         and type(source) is dict and set(source) == {'path', 'bytes', 'sha256'}
         and type(source['path']) is str and absolute(source['path']).name == SOURCE_NAME
         and type(source['bytes']) is int and source['bytes'] == SOURCE_BYTES
         and source['sha256'] == SOURCE_SHA, 'D02 reviewed dialogue or original ODT changed')
    check_ack(outer, expected_upload_ack, receiver, checked_read)
    inner = protected_record(outer['ordinary_context'], checked_read)
    need(set(inner) == {'schema', 'upload_ack_sha256', 'ingress_settlement_sha256', 'session_key',
                        'selector', 'native_message_id', 'native_update_id', 'message_uid', 'file',
                        'file_identity_sha256'}
         and inner['schema'] == CONTINUITY and inner['session_key'] == session_key
         and inner['upload_ack_sha256'] == expected_upload_ack['sha256']
         and is_digest(expected_ingress_settlement_sha256)
         and inner['ingress_settlement_sha256'] == expected_ingress_settlement_sha256
         and native_id(inner['native_message_id']) and native_id(inner['native_update_id'])
         and type(inner['message_uid']) is str and 0 < len(inner['message_uid']) <= 128
         and is_digest(inner['file_identity_sha256']), 'D02 exact independently joined upload required')
    selector = native_anchor._selector(inner['selector'])
    need(selector[2] == SOURCE_NAME, 'D02 native anchor selects another filename')

    key = digest(json.dumps(principal, ensure_ascii=False, separators=(',', ':')).encode())
    policy = AnchorPolicy(principal, profile, key, binding)
    current = AnchorSession(session_id, session_key)
    route = (platform, user_id, user_id, 'dm', None)
    received = home / 'workspace' / 'received'
    directories = (home, received.parent, received)
    identities = tuple(signature(path, directory=True) for path in directories)
    store = AnchorReadStore(home / 'state.db', native_fork_check)
    snapshot = store.fence()
    lineage, row = native_anchor._read_anchor(store, policy, current, route, selector, deadline)
    need(row[:2] == (inner['native_message_id'], inner['message_uid']),
         'D02 selected carrier differs from the admitted upload')
    store.check_carrier_uniqueness(selector, inner['native_message_id'], deadline)
    file = native_anchor._file(row, policy, SOURCE_NAME)
    need(file == inner['file'] and file['sha256'] == SOURCE_SHA and file['size_bytes'] == SOURCE_BYTES,
         'D02 native selected file differs from reviewed ODT')
    path = home / 'workspace' / file['path']
    identity = file_identity_sha256(path)
    raw = checked_read(path, limit=SOURCE_BYTES, private=True)
    need(SOURCE_SHA == digest(raw) and len(raw) == SOURCE_BYTES
         and identity == inner['file_identity_sha256'] == file_identity_sha256(path),
         'D02 retained ODT was changed or replaced')
    check_ack(outer, expected_upload_ack, receiver, checked_read)
    need(native_anchor._read_anchor(store, policy, current, route, selector, deadline) == (lineage, row)
         and store.fence() == snapshot and identities == tuple(signature(p, directory=True) for p in directories)
         and file_identity_sha256(path) == identity and time.monotonic() < deadline, 'D02 native retained context changed during observation')
    return {
        'context_sha256': context_ref['sha256'],
        'continuity_sha256': outer['ordinary_context']['sha256'],
        'source_sha256': SOURCE_SHA,
        'file_identity_sha256': identity,
        'lineage_sha256': digest(encoded([item['id'] for item in lineage])),
    }
