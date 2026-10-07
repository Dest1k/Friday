"""Executable reproductions of BLOCKED native web guarantees, not acceptance.

No public DNS/socket/provider is used. Actual requests/urllib3/parser and donor
dispatch run against finite local collaborators; every test-owned thread drains.
"""
import asyncio
import io
import json
import socket
import threading
import time

import pytest

from plugins.web import keyless_mcp as mcp
from tools import web_tools_extract as extract, url_safety, interrupt


def observation(name, **fields):
    import os
    from pathlib import Path
    directory = Path(os.environ['FRIDAY_FIXTURE_EVIDENCE'])
    (directory / (name + '.json')).write_text(json.dumps(fields, indent=2) + '\n')


def test_real_requests_dns_exceeds_whole_call_timeout_without_socket(monkeypatch):
    calls = []
    def slow_dns(host, port, *args, **kwargs):
        calls.append((host, port))
        time.sleep(1.10)  # finite simulated libc resolver; never a public DNS call
        raise socket.gaierror(socket.EAI_AGAIN, 'synthetic resolver still pending')
    monkeypatch.setattr(socket, 'getaddrinfo', slow_dns)
    began = time.monotonic()
    with pytest.raises(mcp.KeylessMCPError, match='bounded request failed'):
        mcp.mcp_call(mcp.EXA_MCP_URL, 'web_search_exa',
                     {'query': 'official documentation', 'numResults': 3}, timeout=1)
    elapsed = time.monotonic() - began
    assert calls == [('mcp.exa.ai', 443)]  # actual requests/urllib3 path, one try
    assert elapsed >= 1.10
    observation('slow-dns', requested_timeout_s=1, elapsed_s=elapsed,
                dns_calls=calls, sockets_created=0, work_drained=True,
                guarantee='BLOCKED_DNS_NOT_BOUNDED_BY_REQUESTS_TIMEOUT')


@pytest.mark.parametrize('mode', ['slow-headers', 'fast-success'])
def test_real_response_header_parser_outlives_read_inactivity_timeout(monkeypatch, mode):
    """Run genuine urllib3/http.client headers through a finite synthetic socket.

    Every successful read takes less than the requested socket inactivity cap;
    the aggregate header phase exceeds the whole MCP clock. This is a transport
    fixture, not TLS, network or system socket acceptance.
    """
    import urllib3.connection
    import urllib3.connectionpool
    timeouts, closed, writes = [], [], []
    body = json.dumps({'jsonrpc':'2.0','id':1,
                       'result':{'content':[{'type':'text','text':'source'}]}}).encode()
    fragments = [b'HTTP/1.1 200 OK\r\n']
    fragments += [b'X-Fixture: slow\r\n'] * 22
    fragments += [b'Content-Length: ' + str(len(body)).encode() + b'\r\n',
                  b'Connection: close\r\n', b'\r\n', body]

    class Raw(io.RawIOBase):
        def __init__(self, owner):
            self._sock = owner
            self.parts = list(fragments)
        def readable(self):
            return True
        def readinto(self, target):
            if not self.parts:
                return 0
            if mode == 'slow-headers':
                time.sleep(.045)
            part = self.parts.pop(0)
            target[:len(part)] = part
            return len(part)

    class Socket:
        def settimeout(self, timeout):
            timeouts.append(timeout)
        def sendall(self, data):
            writes.append(data)
        def makefile(self, *args, **kwargs):
            return io.BufferedReader(Raw(self))
        def close(self):
            closed.append(True)

    class Connection(urllib3.connection.HTTPSConnection):
        def connect(self):
            self.sock = Socket()
            self.is_verified = True
            self.proxy_is_verified = True

    monkeypatch.setattr(urllib3.connectionpool.HTTPSConnectionPool,
                        'ConnectionCls', Connection)
    began = time.monotonic()
    if mode == 'slow-headers':
        with pytest.raises(mcp.KeylessMCPError, match='keyless timeout'):
            mcp.mcp_call(mcp.EXA_MCP_URL, 'web_search_exa',
                         {'query':'official documentation','numResults':3}, timeout=1)
    else:
        assert mcp.mcp_call(mcp.EXA_MCP_URL, 'web_search_exa',
                           {'query':'official documentation','numResults':3}, timeout=1) == 'source'
    elapsed = time.monotonic() - began
    assert writes and closed and timeouts and all(0 < t <= 1 for t in timeouts)
    assert elapsed > 1 if mode == 'slow-headers' else elapsed < 1
    observation(mode, requested_timeout_s=1, elapsed_s=elapsed,
                socket_inactivity_timeouts=timeouts, real_header_parser=True,
                actual_TLS_DNS_network=False,
                late_success_refused=mode == 'slow-headers',
                guarantee='BLOCKED_HEADER_PHASE_NOT_BOUNDED_BY_WHOLE_CALL_CLOCK'
                          if mode == 'slow-headers' else 'POSITIVE_FINITE_PARSER_CONTROL')


@pytest.mark.parametrize('action', ['timeout', 'cancel'])
def test_native_extract_return_or_cancel_does_not_settle_sync_worker(monkeypatch, action):
    entered, release, drained = threading.Event(), threading.Event(), threading.Event()
    worker = []
    class Provider:
        name = 'exa'
        def extract(self, urls, **kwargs):
            worker.append(threading.get_ident())
            entered.set()
            try:
                assert release.wait(2), 'fixture owner must release owned worker'
                return [{'url':urls[0], 'content':'late data'}]
            finally:
                drained.set()
    monkeypatch.setattr(extract, '_extract_timeout_seconds', lambda: .03)
    monkeypatch.setattr(extract, '_rescue_eligible', lambda provider: False)

    async def run():
        pending = asyncio.create_task(extract._dispatch_extract(
            Provider(), ['https://docs.python.org/3/'], None))
        try:
            while not entered.is_set():
                await asyncio.sleep(.001)
            if action == 'cancel':
                pending.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await pending
            else:
                result = await pending
                assert 'timed out' in result[0]['error']
            assert not drained.is_set()
            observation('extract-' + action, caller_returned=True, worker_active=True,
                        worker_tids=worker, automatic_rescue=False,
                        guarantee='BLOCKED_CANCELLED_FUTURE_IS_NOT_SYNC_WORKER_CESSATION')
        finally:
            release.set()
            while not drained.is_set():
                await asyncio.sleep(.001)
    asyncio.run(run())  # its real default executor shuts down/joins after release
    assert drained.is_set()


def test_native_ssrf_dns_cancellation_leaves_resolver_work(monkeypatch):
    entered, release, drained = threading.Event(), threading.Event(), threading.Event()
    def resolve(*args):
        entered.set()
        try:
            assert release.wait(2)
            return [(socket.AF_INET,socket.SOCK_STREAM,6,'',('93.184.216.34',443))]
        finally:
            drained.set()
    monkeypatch.setattr(url_safety, '_getaddrinfo', resolve)
    monkeypatch.setattr(url_safety, '_resolve_allow_private_urls', lambda: False)
    async def run():
        pending = asyncio.create_task(url_safety.async_is_safe_url('https://example.com/'))
        try:
            while not entered.is_set():
                await asyncio.sleep(.001)
            pending.cancel()
            with pytest.raises(asyncio.CancelledError):
                await pending
            assert not drained.is_set()
            observation('ssrf-dns-cancel', resolver_still_active=True,
                        guarantee='BLOCKED_NATIVE_SSRF_DNS_TO_THREAD_HAS_NO_STOP_JOIN')
        finally:
            release.set()
            while not drained.is_set():
                await asyncio.sleep(.001)
    asyncio.run(run())
    assert drained.is_set()


def test_keyless_batch_starts_next_request_after_native_stop(monkeypatch):
    calls = []
    def call(url, tool, arguments, timeout=30):
        calls.append({'arguments':arguments, 'timeout':timeout,
                      'interrupted_at_entry':interrupt.is_interrupted()})
        if len(calls) == 1:
            interrupt.set_interrupt(True)
        return '# Synthetic source\nUntrusted source text'
    monkeypatch.setattr(mcp, 'mcp_call', call)
    interrupt.set_interrupt(False)
    try:
        rows = mcp.exa_extract_keyless(['https://example.com/1','https://example.com/2'])
        assert len(rows) == 2 and len(calls) == 2
        assert calls[1]['interrupted_at_entry'] and calls[1]['timeout'] == 30
        observation('batch-after-stop', calls=calls,
                    guarantee='BLOCKED_PER_URL_LOOP_REDISPATCHES_AFTER_STOP_WITH_FRESH_CLOCK')
    finally:
        interrupt.set_interrupt(False)


def test_native_deadline_primitive_abandons_worker_without_join():
    from agent.deadline import run_bounded_sync
    entered, release, drained = threading.Event(), threading.Event(), threading.Event()
    def operation():
        entered.set()
        try:
            assert release.wait(2)
        finally:
            drained.set()
    try:
        result = run_bounded_sync(operation, .03, label='finite-web-fixture')
        assert entered.is_set() and result.timed_out and not drained.is_set()
        observation('native-deadline-abandon', caller_timed_out=True, worker_active=True,
                    guarantee='BLOCKED_NATIVE_RUN_BOUNDED_SYNC_IS_NOT_SETTLEMENT')
    finally:
        release.set()
        assert drained.wait(1)
        for thread in threading.enumerate():
            if thread.name == 'deadline-finite-web-fixture':
                thread.join(1)
                assert not thread.is_alive()


def test_actual_exa_redispatches_after_dispatch_timeout_and_caller_stop(monkeypatch):
    from plugins.web.exa import provider as exa
    from hermes_cli.config import atomic_config_replace
    from hermes_constants import get_hermes_home
    from tools.configure_local_test import build_config
    config = build_config(base_url='http://127.0.0.1:8011/v1', model='offline-fixture',
        key_env='FRIDAY_FIXTURE_KEY', context=40960, max_input=40954,
        main_output=4096, summary_output=2048, margin=1024, template_overhead=2048,
        web_profile='exa-keyless')
    atomic_config_replace(get_hermes_home() / 'config.yaml', config)
    entered, release, drained = threading.Event(), threading.Event(), threading.Event()
    calls = []
    def call(url, tool, arguments, timeout=30):
        calls.append({'urls':arguments['urls'], 'timeout':timeout,
                      'worker_interrupted':interrupt.is_interrupted()})
        if len(calls) == 1:
            entered.set()
            assert release.wait(2)
        else:
            drained.set()
        return '# Source\nFinite synthetic response'
    monkeypatch.setattr(mcp, 'mcp_call', call)
    monkeypatch.setattr(exa, 'use_keyless', lambda *a: True)
    monkeypatch.setattr(exa, 'provider_env', lambda *a: '')
    monkeypatch.setattr(extract, '_extract_timeout_seconds', lambda: .03)
    monkeypatch.setattr(extract, '_rescue_eligible', lambda provider: False)
    interrupt.set_interrupt(False)
    async def run():
        pending = asyncio.create_task(extract._dispatch_extract(
            exa.ExaWebSearchProvider(),
            ['https://example.com/1','https://example.com/2'], None))
        try:
            entry_deadline = time.monotonic() + .5
            while not entered.is_set():
                assert not pending.done(), pending.result()
                assert time.monotonic() < entry_deadline, 'finite fixture entry bound'
                await asyncio.sleep(.001)
            result = await pending
            assert 'timed out' in result[0]['error'] and len(calls) == 1
            # This is the real caller-thread stop bit. asyncio.to_thread copies
            # ContextVars, but this native path never binds acting_for_tid.
            interrupt.set_interrupt(True)
            release.set()
            drain_deadline = time.monotonic() + .5
            while not drained.is_set():
                assert time.monotonic() < drain_deadline, 'finite fixture drain bound'
                await asyncio.sleep(.001)
            assert len(calls) == 2 and not calls[1]['worker_interrupted']
            observation('actual-exa-late-redispatch', caller_timed_out=True,
                        caller_stop=True, calls=calls, original_dispatch_s=.03,
                        guarantee='BLOCKED_ACTUAL_EXA_LATE_REQUEST_AND_UNBOUND_CALLER_STOP')
        finally:
            interrupt.set_interrupt(False)
            release.set()
    asyncio.run(run())
    assert drained.is_set()


def test_finite_async_extract_can_cancel_and_drain_without_sync_worker(monkeypatch):
    """Positive capability control: the dispatch seam works for a real coroutine.

    It does not establish that the actual Exa provider implements that seam.
    """
    entered, drained = [], []
    class Provider:
        name = 'finite-async-fixture'
        async def extract(self, urls, **kwargs):
            entered.append(True)
            try:
                await asyncio.Event().wait()
            finally:
                drained.append(True)
    monkeypatch.setattr(extract, '_extract_timeout_seconds', lambda: .03)
    monkeypatch.setattr(extract, '_rescue_eligible', lambda provider: False)
    result = asyncio.run(extract._dispatch_extract(Provider(), ['https://example.com/'], None))
    assert entered and drained and 'timed out' in result[0]['error']
    observation('async-capability-control', cancellation_drained=True,
                actual_exa_async_capability=False, product_accepted=False)
