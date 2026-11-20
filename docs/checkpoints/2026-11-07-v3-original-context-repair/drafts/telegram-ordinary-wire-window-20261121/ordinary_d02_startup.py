"""Retainable D02 startup observation from the already owned native gateway."""

import json
import os
from pathlib import Path
import re
import socket
import stat
import struct
import time


REQUEST_ID = 'd02-startup-owner'
MAX_RESPONSE = 512 * 1024
SCHEMA = 'frw.Root.D02.native-gateway-start-observation.v1'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def remaining(deadline):
    seconds = deadline - time.monotonic()
    if not 0 < seconds < float('inf'):
        raise TimeoutError('D02 startup observation deadline')
    return seconds


def kernel_identity(pid):
    process = (Path('/proc') / str(pid) / 'stat').read_text()
    return dict(pid=pid, start_time=int(process.rsplit(') ', 1)[1].split()[19]),
                boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())


def socket_identity(path):
    info = path.lstat()
    require(path.resolve(strict=True) == path and stat.S_ISSOCK(info.st_mode)
            and info.st_uid == os.getuid() and not info.st_mode & 0o077,
            'D02 owned native gateway socket required')
    return info.st_dev, info.st_ino, info.st_ctime_ns


def unique_fields(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'D02 duplicate identify field')
        result[key] = value
    return result


def identify(path, pid, deadline):
    request = dict(protocol=1, id=REQUEST_ID, verb='identify')
    with socket.socket(socket.AF_UNIX) as connection:
        connection.settimeout(remaining(deadline))
        connection.connect(str(path))
        peer = connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize('3i'))
        peer_pid, peer_uid, _ = struct.unpack('3i', peer)
        require((peer_pid, peer_uid) == (pid, os.getuid()), 'D02 native identify peer changed')
        connection.settimeout(remaining(deadline))
        connection.sendall(json.dumps(request).encode() + b'\n')
        raw = bytearray()
        while not raw.endswith(b'\n'):
            connection.settimeout(remaining(deadline))
            chunk = connection.recv(min(65536, MAX_RESPONSE + 2 - len(raw)))
            raw.extend(chunk)
            require(chunk and len(raw) <= MAX_RESPONSE + 1 and raw.count(b'\n') <= 1,
                    'D02 incomplete or oversized identify response')
    reply = json.loads(raw, object_pairs_hook=unique_fields)
    require(type(reply) is dict and reply.get('id') == REQUEST_ID
            and reply.get('ok') is True and type(reply.get('protocol')) is int
            and reply['protocol'] == 1 and type(reply.get('result')) is dict,
            'D02 native identify refused')
    return reply['result']


def observe_owner(home, active, *, code_sha, receipt_sha256, overlay_sha256, read_active, deadline):
    """Run after the service start readback, within its remaining observation budget.

    ``active`` and ``read_active`` use the existing owned unit observation. The
    source pins come from the checked installed successor, before this call.
    The caller retains the returned mapping with its existing private writer.
    """
    path = Path(home) / 'gateway.sock'
    identity = dict(pid=active['pid'], start_time=active['birth_ticks'], boot_id=active['boot_id'])
    invocation = active['invocation_id']
    require(type(identity['pid']) is int and identity['pid'] > 0
            and type(identity['start_time']) is int and identity['start_time'] > 0
            and type(invocation) is str and re.fullmatch('[0-9a-f]{32}', invocation),
            'D02 startup needs an owned service invocation')
    require(all(type(pin) is str and re.fullmatch(pattern, pin)
                for pin, pattern in ((code_sha, '[0-9a-f]{40}'),
                                     (receipt_sha256, '[0-9a-f]{64}'),
                                     (overlay_sha256, '[0-9a-f]{64}'))),
            'D02 startup needs checked installation pins')
    remaining(deadline)
    require(kernel_identity(identity['pid']) == identity, 'D02 startup kernel identity changed')
    socket_before = socket_identity(path)
    reported = identify(path, identity['pid'], deadline)
    owner = reported.get('friday_owner')
    source = owner.get('source') if type(owner) is dict else None
    expected = dict(protocol=1, kind='hermes-gateway', pid=identity['pid'],
                    start_time=identity['start_time'], hermes_home=str(home), code_sha=code_sha)
    source_pins = dict(root=str(Path(home) / 'hermes-agent'), commit=code_sha,
                       receipt=receipt_sha256, plugin=overlay_sha256)
    require(all(type(reported.get(key)) is type(value) and reported[key] == value
                for key, value in expected.items())
            and type(source) is dict and owner.get('home') == str(home)
            and all(source.get(key) == value for key, value in source_pins.items()),
            'D02 native identify generation changed')
    require(read_active(deadline) == active and kernel_identity(identity['pid']) == identity
            and socket_identity(path) == socket_before, 'D02 startup owner changed during observation')
    remaining(deadline)
    expected['friday_owner'] = dict(home=str(home), source=source_pins)
    return dict(schema=SCHEMA, identity=identity, transport='unix-peer-credentials',
                invocation_id=invocation, identify=expected)


def retain_owner(home, active, *, read_generation, read_active, write_private, deadline):
    """Bind the checked installation to the retained proof for the same start."""
    remaining(deadline)
    generation = read_generation(deadline)

    def recheck(stop):
        require(read_generation(stop) == generation, 'D02 installed startup generation changed')
        return read_active(stop)

    proof = observe_owner(home, active, read_active=recheck, deadline=deadline, **generation)
    return write_private(proof)
