"""Single-operation ownership for R4. The driver supplies reviewed inputs and transport."""

import fcntl
import os
from pathlib import Path
import signal
import tempfile
import time


class Once:
    def __init__(self, actor, current, composer, binding_ref):
        self.actor = actor
        self.current = current
        self.compose = composer.compose_observer
        self.binding_ref = binding_ref
        self.binding = actor.doc(binding_ref)
        self.work = Path(self.binding['workdir'])
        self.phase = actor.doc(self.binding['phase'])
        self.context = {'run_id': self.binding['run_id'], 'scenario_sha256': self.phase['scenario_sha256']}
        metadata = current.document(self.binding['prepare'])['metadata_helper']
        actor.need(metadata['sha256'] == current.METADATA_SHA, 'R4_METADATA_HELPER_CHANGED')
        self.metadata = current.source_module(metadata, '_R4_once_metadata')

    def record(self, name, value):
        return self.actor.new(self.work / name, self.actor.encoded(value))

    def record_failure(self, name, exc, **values):
        try:
            self.record(name, dict(**self.context, **values, exception_class=type(exc).__name__, no_retry=True,
                                   acceptance='NOT_ESTABLISHED'))
        except Exception as record_error:
            exc.add_note(f'Protected ending record failed: {type(record_error).__name__}')

    def observer(self, directory, role, slot_owner, clock=None, invocation=None):
        wall, mono = time.time(), time.monotonic()
        owner = self.actor.kernel(os.getpid())
        proof = self.actor.new(directory / f'proof-{role}.json', self.actor.encoded(dict(
            schema='frw.Root.ordinary-current-proof.v1', role=role, **self.context,
            contract=self.binding['contract'], prepare=self.binding['prepare'], boot_id=owner['boot_id'],
            lock_owners=dict(slot=slot_owner, consumer=owner, credential=owner), clock=clock,
            once_invocation=invocation, created_at=wall, expires_at=wall + 120,
            created_monotonic=mono, expires_monotonic=mono + 120)))
        raw = self.compose(self.actor.readref(self.binding['source']), **self.context,
                           authority=self.actor.doc(self.binding['authority']),
                           authority_ref=self.binding['authority'], checker_ref=self.binding['checker'],
                           proof_ref=proof, contract_ref=self.binding['contract'],
                           prepare_ref=self.binding['prepare'])
        source = self.actor.new(directory / f'observer-{role}.py', raw)
        return self.actor.load_raw(raw, source['path'], f'_R4_{role}'), source

    def execute(self, launch):
        """Qualify under the existing slot, start one clock, and reap the same child."""
        actor = self.actor
        actor.protected_directory(self.work)
        slot = actor.safe_lock(actor.SLOT, self.binding['slot_identity'])
        previous = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
        stops = []
        child = child_identity = child_pidfd = clock_ref = claim = None
        stage = 'PRECLOCK'
        forwarded = False
        lifetime = dict(cleanup_attempted=False)

        def forward_stop():
            nonlocal forwarded
            if stops and not forwarded and child_pidfd is not None:
                forwarded = True
                try:
                    signal.pidfd_send_signal(child_pidfd, signal.SIGINT)
                except ProcessLookupError:
                    forwarded = False

        def request_stop(sig, _frame):
            stops.append(int(sig))
            forward_stop()

        try:
            for sig in previous:
                signal.signal(sig, request_stop)
            actor.need(not list(self.work.iterdir()), 'R4_OPERATION_DIRECTORY_ALREADY_USED')
            parent = actor.kernel(os.getpid())
            with tempfile.TemporaryDirectory(prefix='preclock-', dir=self.work) as scratch:
                observer, source = self.observer(Path(scratch), 'preclock', parent)
                qualified = actor.qualify_before_clock(
                    {'run_id': self.context['run_id'], 'selected_tester': source}, observer, self.metadata,
                    actor.readref(source), self.phase)
            scope = self.binding['disk_scope']
            baseline = actor.scan_scope(scope, deadline=time.monotonic() + 30)
            actor.need(not stops, 'R4_STOP_BEFORE_CLAIM')
            claim = self.record('claim.json', dict(binding=self.binding_ref, **self.context, parent=parent,
                                                   no_retry=True, readonly_qualification=qualified))
            stage = 'CLOCK'
            actor.need(not stops, 'R4_STOP_BEFORE_CLOCK')
            start = time.monotonic()
            clock = dict(schema='frw.Root.F07.finite-operation-clock.v1', status='ROOT_BOUND_FUTURE_OPERATION',
                         **self.context, timing=self.current.TIMING, old_effects_clocks_preserved=True,
                         started_monotonic=start, deadline_monotonic=start + self.current.TIMING['outer_seconds'])
            clock_ref = self.record('clock.json', clock)
            try:
                stage = 'LAUNCH'
                actor.need(not stops, 'R4_STOP_BEFORE_BIRTH')
                child = launch(slot, parent, claim, clock_ref)
                if child.poll() is None:
                    try:
                        child_pidfd = os.pidfd_open(child.pid)
                        forward_stop()
                        child_identity = actor.kernel(child.pid)
                    except (FileNotFoundError, ProcessLookupError):
                        if child.poll() is None:
                            raise
                birth = self.record('child-birth.json', dict(pid=child.pid, identity=child_identity, parent=parent,
                                                            clock=clock_ref, claim=claim))
                stage = 'WAIT'
                result = actor.wait_owned(child, clock, scope, baseline, self.binding['resources']['disk_bytes'],
                                          stops, lifetime, monitor_failure_path=self.work / 'disk-failure.json')
            finally:
                if child is not None and child.poll() is None and not lifetime['cleanup_attempted']:
                    actor.stop_reap(child, clock, [], lifetime)
            result.update(**self.context, owned_child_reaped=True, parent_stops=stops,
                          stop_forwarded=forwarded, child_birth=birth,
                          operation_clock=clock_ref, no_retry=True, acceptance='NOT_ESTABLISHED')
            self.record('parent-ended.json', result)
            return result
        except actor.StopUnconfirmed as exc:
            self.record_failure('stop-unconfirmed.json', exc, state='STOP_UNCONFIRMED', pid=child.pid,
                                identity=child_identity, parent=parent, operation_clock=clock_ref)
            raise
        except BaseException as exc:
            if claim is not None:
                self.record_failure('parent-failure.json', exc, stage=stage, operation_clock=clock_ref,
                                    owned_child_reaped=child is not None and child.poll() is not None,
                                    parent_stops=stops, stop_forwarded=forwarded)
            raise
        finally:
            for sig, handler in previous.items():
                signal.signal(sig, handler)
            if child_pidfd is not None:
                os.close(child_pidfd)
            os.close(slot)

    def consume(self, slot, parent, claim, clock, runner_factory):
        """Keep the active R4 gates on the normal new, send and observe methods."""
        progress = dict(stage='BOOTSTRAP', run=None)
        ending = False

        def stop_once(_signum, _frame):
            if not ending:
                signal.signal(signal.SIGINT, signal.SIG_IGN)
                raise KeyboardInterrupt

        previous = signal.signal(signal.SIGINT, stop_once)
        try:
            try:
                self._consume_locked(slot, parent, claim, clock, runner_factory, progress)
                ending = True
            except BaseException as exc:
                ending = True
                self.record_failure('consumer-ended.json', exc, **progress)
                raise
            self.record('consumer-ended.json', dict(**self.context, **progress, exception_class=None, no_retry=True,
                                                    acceptance='NOT_ESTABLISHED'))
        finally:
            signal.signal(signal.SIGINT, previous)

    def _consume_locked(self, slot, parent, claim, clock, runner_factory, progress):
        actor = self.actor
        actor.child_limits(self.binding['resources'])
        actor.need(parent == actor.kernel(os.getppid()), 'R4_PARENT_IDENTITY_CHANGED')
        actor.need(actor.lock_identity(os.fstat(slot)) == self.binding['slot_identity']
                   == actor.lock_identity(actor.SLOT.lstat()), 'R4_INHERITED_SLOT_CHANGED')
        self.metadata.lock_held(actor.SLOT, parent)
        fcntl.flock(slot, fcntl.LOCK_EX | fcntl.LOCK_NB)
        actor.need(claim == actor.fileref(self.work / 'claim.json') and clock == actor.fileref(self.work / 'clock.json'),
                   'R4_PARENT_OPERATION_REFERENCES_CHANGED')
        claim_value = actor.doc(claim)
        actor.need(claim_value['binding'] == self.binding_ref and claim_value['parent'] == parent
                   and claim_value['no_retry'] is True and all(claim_value[key] == value
                   for key, value in self.context.items()), 'R4_PARENT_CLAIM_CHANGED')
        base = actor.load_raw(actor.readref(self.binding['source']), self.binding['source']['path'], '_R4_store')
        paths = [actor.STATE, *(actor.STATE / name for name in ('runs', 'updates', 'downloads'))]
        before = [actor.protected_directory(path) for path in paths]
        store = base.Store(actor.STATE)
        actor.need(before == [actor.protected_directory(path) for path in paths], 'R4_STORE_CONSTRUCTOR_MUTATED_DIRS')
        with store.lock(create=False) as consumer, store.lock(actor.STATE / 'tester-token', create=False) as credential:
            owner = actor.kernel(os.getpid())
            invocation = self.record('consumer-invocation.json', dict(
                schema='frw.Root.F07.one-ordinary-consumer-invocation.v1', run_id=self.context['run_id'],
                consumer=owner, driver_binding=self.binding_ref, clock=clock, no_retry=True))
            observer, _ = self.observer(self.work, 'owned_consumer', parent, clock, invocation)
            runner = runner_factory(observer, store)
            path = store.run_path(self.context['run_id'])
            present_before = os.path.lexists(path)
            try:
                progress['stage'] = 'NEW'
                run = runner.new(self.context['run_id'], self.phase['scenario'])
                progress['stage'] = 'SEND'
                runner.send(run, consumer_fd=consumer, credential_fd=credential)
                progress['stage'] = 'OBSERVE'
                runner.observe(run)
            except BaseException as exc:
                try:
                    if not present_before and os.path.lexists(path):
                        progress['run'] = actor.fileref(path)
                except Exception as read_error:
                    exc.add_note(f'Protected run reference unavailable: {type(read_error).__name__}')
                raise
            progress['run'] = actor.fileref(path)
