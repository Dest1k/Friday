"""One locally bound direct-chat document roundtrip and explicit continuation."""
from __future__ import annotations

import asyncio
import math
import os
import time
from contextlib import asynccontextmanager, suppress
from copy import deepcopy
from dataclasses import asdict, dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from . import _stock_observer as stock
from .trueconf.trueconf_client import (
    IngressAckError,
    IngressKey,
    IngressReceipt,
    TrueConfError,
)
from .trueconf.trueconf_files import FileTransferError, file_origin


@dataclass(frozen=True)
class DirectRoute:
    server: str
    tester_user_id: str
    product_user_id: str
    chat_id: str


def valid_id(value):
    return (isinstance(value, str) and 1 <= len(value) <= 512
            and all(char.isprintable() and not char.isspace() for char in value))


def _document_output(step):
    upload = step['input']
    expected = step['observe']['documents'][0]
    return {'filename': expected.get('filename_equals', upload['filename']),
            'mime_type': upload['mime_type']}


def validate_plan(plan, route, authenticated_route, observation_seconds):
    if (not isinstance(plan, dict) or not isinstance(route, DirectRoute) or route != authenticated_route
            or route.tester_user_id == route.product_user_id
            or not all(valid_id(v) for v in vars(route).values())):
        raise stock.Refused('Authenticated independent direct route required')
    stock.validate_scenario_steps(plan)
    steps = plan['steps']
    if (len(steps) != 2 or 'input' not in steps[0]
            or steps[0]['input']['kind'] != 'document'
            or set(steps[0]['observe']) != {'documents'}
            or len(steps[0]['observe']['documents']) != 1
            or set(steps[1]) != {'request', 'observe'}
            or set(steps[1]['observe']) != {'text_equals'}):
        raise stock.Refused('Expected one file action followed by one exact-text action')
    document = steps[0]['observe']['documents'][0]
    required = {'sha256', 'max_bytes', 'caption_equals'}
    if set(document) not in (required, required | {'filename_equals'}):
        raise stock.Refused('Exact output hash, byte bound and caption required')
    if 'filename_equals' in document:
        if not isinstance(document['filename_equals'], str):
            raise stock.Refused('Exact output filename required')
        # Validate the declared basename and catalogue MIME before any send.
        stock.ordinary_document_response_failures(_document_output(steps[0]), [])
    if (not isinstance(observation_seconds, tuple) or len(observation_seconds) != 2
            or any(type(seconds) not in (int, float) or not 0 < seconds <= 600
                   for seconds in observation_seconds)
            or sum(observation_seconds) >= plan['deadline_seconds']):
        raise stock.Refused('Invalid finite phase windows')


_SCHEMA = 'friday.trueconf-tester.direct-document.v2'
_RECONNECTABLE = {
    'websocket_disconnected', 'not_connected', 'ingress_delivery_closed',
    'websocket_request_failed', 'websocket_open_failed',
}


def _origin(route):
    url = route.server if '://' in route.server else 'https://' + route.server
    try:
        return file_origin(url)[0]
    except FileTransferError:
        raise stock.Refused('Invalid pinned TrueConf origin') from None


def _clock():
    return Path('/proc/sys/kernel/random/boot_id').read_text().strip()


def _remaining(cutoff):
    seconds = cutoff - time.monotonic()
    if seconds <= 0:
        raise stock.Refused('Original deadline expired')
    return seconds


def _hex_digest(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def _sync(path, *, directory=False):
    flags = os.O_RDONLY | os.O_NOFOLLOW | (os.O_DIRECTORY if directory else 0)
    fd = os.open(path, flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _staging_path(path):
    return path.with_name(path.name + '.new')


def _preserve_interrupted_write(path, limit):
    staged = _staging_path(path)
    try:
        stock.safe_read(staged, limit)
    except FileNotFoundError:
        return
    parked = path.with_name(path.name + '.abandoned-' + uuid4().hex)
    _sync(staged)
    os.rename(staged, parked)
    _sync(path.parent, directory=True)


def _verify_binding(client, route):
    if (client.origin != _origin(route) or client.expected_user_id != route.tester_user_id
            or client.user_id not in (None, route.tester_user_id)):
        raise stock.Refused('Configured TrueConf origin or account differs from the pinned Tester')


def _verify_identity(client, route, *, unread):
    _verify_binding(client, route)
    if client.user_id != route.tester_user_id or client.unread_requested is not unread:
        raise stock.Refused('Connected TrueConf origin, Tester or replay mode differs from the pinned route')


async def _verify_chat(client, route, cutoff):
    async with asyncio.timeout(min(10, _remaining(cutoff))):
        chat = await client.get_chat(route.chat_id)
    if chat.get('chatId') != route.chat_id or type(chat.get('chatType')) is not int or chat['chatType'] != 1:
        raise stock.Refused('Selected conversation is not an authenticated direct chat')


@asynccontextmanager
async def bounded_events(client):
    stream = aiter(client.deliveries())
    pending = None

    async def before(cutoff):
        nonlocal pending
        if pending is None:
            pending = asyncio.ensure_future(anext(stream))
        done, _ = await asyncio.wait((pending,), timeout=max(0, cutoff - time.monotonic()))
        if not done:
            return None
        current, pending = pending, None
        return current.result()

    try:
        yield before
    finally:
        if pending is not None:
            pending.cancel()
            with suppress(Exception, asyncio.CancelledError):
                await pending
        await stream.aclose()


class _Run:
    def __init__(self, client, store, route, plan, receipt):
        self.client = client
        self.store = store
        self.route = route
        self.origin = _origin(route)
        self.plan = plan
        self.receipt = receipt
        self.path = store.run_path('trueconf-direct-document')

    def save(self):
        self.store.put(self.path, self.receipt)

    @property
    def deadline(self):
        return self.receipt['deadline_monotonic']

    def accept_key(self, delivery):
        event = delivery.event
        if (event.chat_id != self.route.chat_id or event.chat_kind != 'direct'
                or event.sender_type != 1 or event.sender_id != self.route.product_user_id):
            return None
        if not valid_id(event.message_id) or type(event.timestamp) is not int or event.timestamp <= 0:
            raise stock.Refused('Malformed event in the selected conversation')
        key = IngressKey(self.origin, self.route.tester_user_id, self.route.chat_id, event.message_id)
        if delivery.key != key:
            raise stock.Refused('Ingress key differs from the authorized Tester route')
        return key

    async def begin(self, phase, step, window, transmit):
        index = phase['step']
        if _remaining(self.deadline) <= window:
            self.receipt.update(state='INCONCLUSIVE')
            phase.update(state='NOT_SENT', reason='ORIGINAL_WINDOW_UNAVAILABLE')
            self.save()
            return False
        self.receipt.update(state='SEND_INTENT', step=index)
        self.save()
        send_budget = self.deadline - time.monotonic() - window
        if send_budget <= 0:
            phase.update(state='NOT_SENT', reason='ORIGINAL_WINDOW_UNAVAILABLE')
            self.receipt.update(state='INCONCLUSIVE')
            self.save()
            return False
        try:
            async with asyncio.timeout(min(10, send_budget)):
                if index == 0:
                    ack = await self.client.send_file(self.route.chat_id, transmit, caption=step['input']['caption'])
                else:
                    ack = await self.client.send_text(self.route.chat_id, step['request'],
                                                      reply_to=phase['parent_message_id'])
            known_ids = {p['ack']['message_id'] for p in self.receipt['phases'] if 'ack' in p}
            known_ids.update(row['message_id'] for p in self.receipt['phases'] for row in p['observations'])
            if ack.status != 'REJECTED' and (ack.status != 'ACK' or not valid_id(ack.message_id)
                    or type(ack.timestamp) is not int or ack.timestamp <= 0
                    or (index == 0 and not valid_id(ack.file_id)) or ack.message_id in known_ids):
                raise stock.Uncertain('Missing or contradictory native send ACK')
        except (Exception, asyncio.CancelledError) as error:
            phase.update(state='UNKNOWN', reason=type(error).__name__)
            self.receipt.update(state='UNKNOWN')
            self.save()
            if isinstance(error, asyncio.CancelledError):
                raise
            return False
        if ack.status == 'REJECTED':
            phase.update(state='REJECTED', error_code=ack.error_code)
            self.receipt.update(state='REJECTED')
            self.save()
            return False
        observed_at = time.monotonic()
        phase.update(state='OBSERVING', ack_monotonic=observed_at, cutoff_monotonic=observed_at + window,
                     ack={'chat_id': self.route.chat_id, 'message_id': ack.message_id,
                              'timestamp_ms': ack.timestamp, 'file_id': ack.file_id})
        self.receipt.update(state='OBSERVING')
        self.save()
        return True

    def verify_observation(self, phase, row, *, event_hash=None):
        if not isinstance(row, dict) or not valid_id(row.get('message_id')):
            raise stock.Refused('Saved Tester observation identity invalid')
        key = IngressKey(self.origin, self.route.tester_user_id, self.route.chat_id, row['message_id'])
        ack = phase.get('ack')
        if (row.get('key') != asdict(key) or not _hex_digest(row.get('event_sha256'))
                or (event_hash is not None and row['event_sha256'] != event_hash)
                or type(row.get('timestamp_ms')) is not int or not isinstance(ack, dict)
                or type(ack.get('timestamp_ms')) is not int or row['timestamp_ms'] < ack['timestamp_ms']
                or ack.get('chat_id') != self.route.chat_id or not valid_id(ack.get('message_id'))
                or row['message_id'] == ack['message_id']):
            raise stock.Refused('Saved Tester observation contradicts the original key or ACK')
        step = self.plan['steps'][phase['step']]
        if phase['step'] == 1:
            if (row.get('kind') != 'text' or row.get('parent_message_id') != ack['message_id']
                    or row.get('text_sha256') != stock.digest(step['observe']['text_equals'].encode())):
                raise stock.Refused('Saved continuation evidence contradicts the plan')
            return
        if (row.get('kind') != 'document' or not _hex_digest(row.get('sha256'))
                or row.get('parent_message_id') not in (None, ack['message_id'])
                or not valid_id(row.get('file_id')) or type(row.get('bytes')) is not int):
            raise stock.Refused('Saved document evidence contradicts the plan')
        required = step['observe']['documents'][0]
        custody_id = stock.digest(stock.encoded((asdict(key), row['sha256'])))
        target = self.store.downloads / ('trueconf-' + custody_id + '.bin')
        if custody_id != row.get('custody_id') or str(target) != row.get('path'):
            raise stock.Refused('Saved file custody differs from the exact Tester target')
        advertised, resolved = row.get('advertised_document'), row.get('resolved_document')
        if (not isinstance(advertised, dict) or not isinstance(resolved, dict)
                or resolved.get('file_id') != row['file_id'] or resolved.get('ready_state') != 2
                or any(advertised.get(field) != resolved.get(field) for field in ('file_name', 'mime_type', 'bytes'))
                or type(advertised.get('bytes')) is not int or type(resolved.get('bytes')) is not int):
            raise stock.Refused('Saved file metadata contradicts the durable observation')
        data = stock.safe_read(target, required['max_bytes'])
        if stock.digest(data) != row['sha256'] or len(data) != row['bytes']:
            raise stock.Refused('Saved file bytes contradict the durable observation')
        stock.verify_exact_document_bytes(data, row['sha256'], advertised['bytes'], resolved['bytes'], required)
        if stock.ordinary_document_response_failures(_document_output(step), [row]):
            raise stock.Refused('Saved document metadata contradicts the plan')
        _sync(target)
        _sync(target.parent, directory=True)

    async def _document(self, phase, event, key, step, cutoff):
        if len(event.attachments) != 1:
            raise stock.Refused('Ambiguous document response')
        attachment = event.attachments[0]
        required = step['observe']['documents'][0]
        if (attachment.kind != 'file' or not valid_id(attachment.file_id) or type(attachment.size) is not int
                or not 0 < attachment.size <= required['max_bytes']
                or (event.text or '') != required['caption_equals']):
            raise stock.Refused('Malformed or mismatched attachment metadata')
        while True:
            info = await self.client.get_file_info(attachment.file_id)
            readiness = info.get('readyState')
            if type(readiness) is int and readiness == 2:
                break
            if type(readiness) is not int or readiness != 1:
                raise stock.Refused('Selected TrueConf file is unavailable')
            await asyncio.sleep(min(0.25, _remaining(cutoff)))
        if (info.get('fileId') != attachment.file_id or info.get('name') != attachment.name
                or info.get('mimeType') != attachment.mime_type
                or type(info.get('size')) is not int or info['size'] != attachment.size):
            raise stock.Refused('Resolved file metadata contradicts event')
        with TemporaryDirectory(dir=self.store.downloads, prefix='.trueconf-stage-') as scratch:
            staging = Path(scratch) / 'received.bin'
            resolved = await self.client.download_file(attachment.file_id, staging,
                                                       max_bytes=required['max_bytes'], expected_size=attachment.size)
            if resolved != staging:
                raise stock.Refused('Download differs from the exclusive Tester staging target')
            data = stock.safe_read(staging, required['max_bytes'])
        sha = stock.digest(data)
        custody_id = stock.digest(stock.encoded((asdict(key), sha)))
        target = self.store.downloads / ('trueconf-' + custody_id + '.bin')
        if target.exists():
            if stock.safe_read(target, required['max_bytes']) != data:
                raise stock.Refused('Existing Tester custody contradicts the received bytes')
            _sync(target)
            _sync(target.parent, directory=True)
        else:
            _preserve_interrupted_write(target, required['max_bytes'])
            self.store.write(target, data)
        document = {'kind': 'document', 'message_id': event.message_id, 'file_id': attachment.file_id,
                        'timestamp_ms': event.timestamp, 'parent_message_id': event.reply_id, 'sha256': sha,
                        'bytes': len(data), 'path': str(target), 'custody_id': custody_id,
                        'advertised_document': {'file_name': attachment.name,
                                                 'mime_type': attachment.mime_type, 'bytes': attachment.size},
                        'resolved_document': {'file_id': info['fileId'], 'file_name': info['name'],
                                               'mime_type': info['mimeType'], 'bytes': info['size'], 'ready_state': readiness}}
        phase['held'] = dict(document, key=asdict(key), reason='DOCUMENT_NOT_ACCEPTED')
        _remaining(cutoff)
        stock.verify_exact_document_bytes(data, sha, attachment.size, info['size'], required)
        if stock.ordinary_document_response_failures(_document_output(step), [document]):
            raise stock.Refused('Ordinary document metadata expectation failed')
        return document

    async def settle(self, delivery, phase, step, cutoff):
        key = self.accept_key(delivery)
        if key is None:
            return
        event = delivery.event
        event_hash = stock.digest(stock.encoded(asdict(event)))
        for old_phase in self.receipt['phases']:
            for prior in old_phase['observations']:
                if prior['key'] == asdict(key):
                    self.verify_observation(old_phase, prior, event_hash=event_hash)

                    async def match(saved_key):
                        _remaining(cutoff)
                        _sync(self.path)
                        _sync(self.path.parent, directory=True)
                        _remaining(cutoff)
                        return IngressReceipt(saved_key, 'DUPLICATE')

                    async with asyncio.timeout(_remaining(cutoff)):
                        await delivery.accept(match)
                    return
        ack = phase['ack']
        if (event.timestamp < ack['timestamp_ms']
                or any(event.message_id == p.get('ack', {}).get('message_id') for p in self.receipt['phases'])):
            return
        is_document = phase['step'] == 0
        if is_document:
            if event.reply_id not in (None, ack['message_id']) or event.message_type != 202 or not event.attachments:
                return
        elif event.reply_id != ack['message_id'] or event.message_type != 200 or event.attachments:
            return
        if phase['observations']:
            raise stock.Refused('Ambiguous response in the original observation window')
        async with asyncio.timeout(_remaining(cutoff)):
            exact = await self.client.get_message(event.message_id, chat_id=self.route.chat_id)
            if exact != event:
                raise stock.Refused('Exact message lookup contradicts the notification')
            if is_document:
                observation = await self._document(phase, event, key, step, cutoff)
            else:
                if event.text != step['observe']['text_equals']:
                    raise stock.Refused('Conflicting exact-text continuation')
                observation = {'kind': 'text', 'message_id': event.message_id, 'parent_message_id': event.reply_id,
                                   'timestamp_ms': event.timestamp, 'text_sha256': stock.digest(event.text.encode())}
            observation.update(key=asdict(key), event_sha256=event_hash)

            async def commit(saved_key):
                _remaining(cutoff)
                held = phase.pop('held', None)
                phase['observations'].append(observation)
                try:
                    self.save()
                except BaseException:
                    phase['observations'].pop()
                    if held is not None:
                        phase['held'] = held
                    raise
                _remaining(cutoff)
                return IngressReceipt(saved_key, 'NEW')

            await delivery.accept(commit)

    async def observe(self, phase, before):
        index = phase['step']
        cutoff = phase['cutoff_monotonic']
        try:
            if cutoff >= self.deadline:
                raise stock.Refused('Full original phase window no longer fits')
            while time.monotonic() < cutoff:
                delivery = await before(cutoff)
                if delivery is None:
                    break
                self.receipt['update_count'] += 1
                self.save()
                if self.receipt['update_count'] > self.plan['max_updates']:
                    raise stock.Refused('Selected observation update bound exceeded')
                await self.settle(delivery, phase, self.plan['steps'][index], cutoff)
            if not stock.observation_ready(
                    {'scenario': self.plan, 'step': index, 'observations': phase['observations']}):
                raise stock.Refused('Original window closed without the expected response')
            for row in phase['observations']:
                self.verify_observation(phase, row)
            _remaining(self.deadline)
        except (asyncio.CancelledError, IngressAckError, StopAsyncIteration) as error:
            self._hold(phase, error)
            if isinstance(error, asyncio.CancelledError):
                raise
            return False
        except TrueConfError as error:
            if error.reason == 'ingress_persistence_failed':
                # Atomic replacement may have occurred. Do not overwrite ambiguous journal state.
                raise
            if error.reason in _RECONNECTABLE:
                self._hold(phase, error)
            else:
                self._refuse(phase, error)
            return False
        except (stock.Refused, TimeoutError, OSError, ValueError) as error:
            self._refuse(phase, error)
            return False
        phase.update(state='MATCHED', ended_at=stock.stamp())
        self.receipt.update(state='OBSERVED')
        self.save()
        return True

    def _hold(self, phase, error):
        phase.update(reason=type(error).__name__)
        self.receipt.update(state='OBSERVATION_HELD')
        self.save()

    def _refuse(self, phase, error):
        phase.update(state='INCONCLUSIVE', reason=type(error).__name__)
        self.receipt.update(state='INCONCLUSIVE')
        self.save()

    def finish(self, *, continuation_held=False):
        state = 'OBSERVED_CONTINUATION_HELD' if continuation_held else 'MATCHED_LOCAL_OBSERVATION'
        self.receipt.update(state=state, ended_at=stock.stamp())
        self.save()
        return self.receipt


async def run_once(client, store, route, authenticated_route, plan, observation_seconds):
    """Start a fresh, connected Tester run. Each phase has its own recorded send intent."""
    plan = deepcopy(plan)
    validate_plan(plan, route, authenticated_route, observation_seconds)
    _verify_identity(client, route, unread=False)
    started = time.monotonic()
    deadline = started + plan['deadline_seconds']
    receipt = {'schema': _SCHEMA, 'route': asdict(route), 'origin': _origin(route),
                   'plan_sha256': stock.digest(stock.encoded(plan)), 'state': 'PREPARING',
                   'windows_seconds': list(observation_seconds), 'started_at': stock.stamp(),
                   'boot_id': _clock(), 'started_monotonic': started, 'deadline_monotonic': deadline, 'update_count': 0,
                   'core_credit': 0, 'acceptance': 'NOT_ESTABLISHED', 'phases': []}
    run = _Run(client, store, route, plan, receipt)
    with store.lock():
        if os.path.lexists(run.path) or os.path.lexists(_staging_path(run.path)):
            raise stock.Refused('The authorized action is already recorded; preserve its outcome')
        await _verify_chat(client, route, deadline)
        upload = plan['steps'][0]['input']
        data = stock.read_document_input(upload, lambda: _remaining(deadline))
        transmit = stock.secure_dir(store.root / 'transmit') / upload['filename']
        store.write(transmit, data)
        _sync(store.root, directory=True)
        _sync(store.root.parent, directory=True)
        parent = None
        async with bounded_events(client) as before:
            for index, step in enumerate(plan['steps']):
                phase = {'step': index, 'state': 'PREPARING', 'parent_message_id': parent,
                             'method': 'sendFile' if index == 0 else 'sendMessage',
                             'started_at': stock.stamp(), 'observations': []}
                receipt['phases'].append(phase)
                if not await run.begin(phase, step, observation_seconds[index], transmit):
                    return receipt
                if not await run.observe(phase, before):
                    return receipt
                parent = phase['observations'][0]['message_id']
        return run.finish()


def _resume_phase(run, observation_seconds):
    receipt = run.receipt
    if (receipt.get('schema') != _SCHEMA or receipt.get('route') != asdict(run.route)
            or receipt.get('origin') != run.origin or receipt.get('boot_id') != _clock()
            or receipt.get('plan_sha256') != stock.digest(stock.encoded(run.plan))
            or receipt.get('windows_seconds') != list(observation_seconds)
            or receipt.get('state') not in ('OBSERVING', 'OBSERVATION_HELD')):
        raise stock.Refused('No exact acknowledged Tester observation is resumable')
    phases = receipt.get('phases')
    index = receipt.get('step')
    if (type(index) is not int or index not in (0, 1) or not isinstance(phases, list)
            or len(phases) != index + 1 or not all(isinstance(row, dict) for row in phases)
            or type(receipt.get('update_count')) is not int
            or not 0 <= receipt['update_count'] <= run.plan['max_updates']):
        raise stock.Refused('Saved Tester observation shape invalid')
    phase = phases[-1]
    ack = phase.get('ack')
    started = receipt.get('started_monotonic')
    observed_at, cutoff = phase.get('ack_monotonic'), phase.get('cutoff_monotonic')
    if (phase.get('step') != index or phase.get('state') != 'OBSERVING'
            or not isinstance(ack, dict) or ack.get('chat_id') != run.route.chat_id
            or not valid_id(ack.get('message_id')) or type(ack.get('timestamp_ms')) is not int
            or ack['timestamp_ms'] <= 0 or not all(_finite(v) for v in (started, observed_at, cutoff, run.deadline))
            or not 0 <= started <= observed_at <= time.monotonic() < cutoff < run.deadline
            or run.deadline != started + run.plan['deadline_seconds']
            or cutoff != observed_at + observation_seconds[index]):
        raise stock.Refused('Saved native ACK or original observation cutoff invalid')
    if index == 0 and not valid_id(ack.get('file_id')):
        raise stock.Refused('Saved file ACK lacks a native file identity')
    for old_index, old_phase in enumerate(phases):
        rows = old_phase.get('observations')
        if old_phase.get('step') != old_index or not isinstance(rows, list) or len(rows) > 1:
            raise stock.Refused('Saved Tester observation shape invalid')
        for row in rows:
            run.verify_observation(old_phase, row)
    if index == 1:
        previous = phases[0]
        if (previous.get('state') != 'MATCHED' or len(previous['observations']) != 1
                or previous['observations'][0]['message_id'] != phase.get('parent_message_id')):
            raise stock.Refused('Saved continuation lacks its exact document parent')
    return phase


async def resume_observation(client, store, route, authenticated_route, plan, observation_seconds):
    """Observe an already acknowledged phase within its original same-boot cutoff."""
    plan = deepcopy(plan)
    validate_plan(plan, route, authenticated_route, observation_seconds)
    _verify_binding(client, route)
    with store.lock():
        path = store.run_path('trueconf-direct-document')
        receipt = store.get(path)
        if not isinstance(receipt, dict):
            raise stock.Refused('No existing Tester observation')
        run = _Run(client, store, route, plan, receipt)
        phase = _resume_phase(run, observation_seconds)
        cutoff = phase['cutoff_monotonic']
        _sync(path)
        _sync(path.parent, directory=True)
        _preserve_interrupted_write(path, stock.MAX_JSON)
        async with asyncio.timeout(_remaining(cutoff)):
            await client.reconnect(receive_unread=True)
            _verify_identity(client, route, unread=True)
            await _verify_chat(client, route, cutoff)
        async with bounded_events(client) as before:
            if not await run.observe(phase, before):
                return receipt
        return run.finish(continuation_held=phase['step'] == 0)
