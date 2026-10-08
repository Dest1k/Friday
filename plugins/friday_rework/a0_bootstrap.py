"""Initial own-profile probe through the existing A0 native owner.

Only protected host setup calls this module. It never grants ordinary job
authority, submits a message, installs a service or borrows another probe.
The original attempt is durable before route/start, and all its execution is
stopped before qualification may publish readiness. Uncertain attempts stay
blocked for exact-owner reconciliation; there is no automatic resume.
"""
from contextlib import contextmanager
import copy
import hashlib
import json
import os
from pathlib import Path
import time

from .host_record import digest
from .host_runtime import HostUnavailable, _pin, a0_deployment_contract, a0_runtime_module
from .worker_provision import pin

FOLDER = 'workers/a0/bootstrap'
PLAN = 'workers/a0/probe-plan.json'


class PrerequisitePending(HostUnavailable):
    """Read-only admission failed before claiming or submitting a native start."""


def _read(path):
    from hermes_cli import friday_user_scope as scope
    from .adapters.a0_native import strict_json
    scope._private(path)
    return strict_json(path.read_bytes())


def _write(path, value, *, replace=False):
    from .onboarding import _new_file, _sync_directory
    data = (json.dumps(value, sort_keys=True, allow_nan=False) + '\n').encode()
    if not replace:
        _new_file(path, data)
        return
    # Same private file owner, atomic replacement; no mutable launch source is
    # needed to recover the exact retained stop identities.
    from hermes_cli import friday_user_scope as scope
    scope._private(path)
    temp = path.with_name(path.name + '.tmp.' + str(os.getpid()))
    try:
        _new_file(temp, data)
        os.replace(temp, path)
        _sync_directory(path.parent)
    finally:
        if temp.exists(): temp.unlink()


def credentials(home):
    return {n: pin(home / n) if (home / n).exists() or (home / n).is_symlink() else None
            for n in ('.env', 'auth.json')}


def _source():
    path = Path(__file__).resolve()
    reference = {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    _pin(reference).read()
    return reference


class InitialProbe:
    def __init__(self, runtime, binding, generation, preparations, budget, verify, *,
                 original_seconds=None, inherited_attempt=None):
        from hermes_cli import friday_user_scope as scope
        if scope._CURRENT.get() is not None:
            raise PermissionError('operator_source_scope_required')
        self.c = a0_deployment_contract(runtime)
        self.home = Path(self.c['runtime_home'])
        self.binding, self.generation = copy.deepcopy(binding), generation
        self.preparations = copy.deepcopy(preparations)
        self.budget, self.verify = budget, verify
        self.folder = self.home / FOLDER
        self.plan_path = self.home / PLAN
        self.runtime = self.route = self.keys = self.created = None
        self.route_module = None
        self.pending_sample = False
        self.samples = []
        self.claimed = self.start_attempted = False
        self.state = {'phase': 'CLAIMED', 'route': None, 'created': None, 'samples': [],
                      'pending_sample': False, 'keys': 'NOT_PREPARED', 'settlement': None}
        from hermes_cli import friday_user_scope as scope
        from hermes_cli.friday_credential_admission import owned_values
        scope._private(self.home, directory=True)
        if (self.folder.exists() or self.folder.is_symlink()
                or self.plan_path.exists() or self.plan_path.is_symlink()):
            raise HostUnavailable('own_a0_bootstrap_requires_reconciliation')
        if (binding['runtime_profile'] != self.c['runtime_profile']
                or type(generation) is not int or generation < 1):
            raise HostUnavailable('foreign_a0_bootstrap_binding')
        self.config_pin = pin(self.home / 'config.yaml')
        self.credential_pins = credentials(self.home)
        self.values = owned_values(self.home)
        from .adapters.a0_config import KEY_REFERENCES
        names = {*KEY_REFERENCES.values(), 'SEARXNG_SECRET'}
        if not names.issubset(self.values):
            raise PrerequisitePending('own_a0_scoped_credentials_missing')
        try: self.m = a0_runtime_module(self.c)
        except (OSError, ValueError, RuntimeError, AttributeError, SyntaxError) as exc:
            raise PrerequisitePending('own_a0_reviewed_native_source_unavailable') from exc
        a = self.c['a0']; m = self.m
        if (str(m.DOCKER) != a['docker']['path'] or str(m.LAUNCHER) != a['launcher']['path']
                or str(m.PROJECT / '.runtime/rootless-docker/supervisor' / m.DAEMON) != a['daemon_unit']['path']):
            raise HostUnavailable('a0_runtime_native_pin_mismatch')
        # This phase inherits setup's entry clock. Installation keeps its own
        # original installer clock; neither operation receives another 3600s.
        seconds = min(300, self.c['budget_seconds']) if original_seconds is None else original_seconds
        if type(seconds) is not int or not 30 <= seconds <= min(300,self.c['budget_seconds']):
            raise HostUnavailable('original_a0_bootstrap_clock_required')
        started = budget.deadline - seconds
        now = time.monotonic()
        if not 0 < started <= now < budget.deadline:
            raise HostUnavailable('original_a0_bootstrap_clock_required')
        accepted_unix = time.time() - (now - started)
        acceptance = {'accepted_unix': accepted_unix,
                      'accepted_monotonic_ns': int(started * 10**9),
                      'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
        phase = {'purpose': 'INITIAL_DEPLOYMENT_PROBE', 'home': str(self.home),
                 'binding': self.binding, 'generation': generation,
                 'preparations': self.preparations, 'runtime_sha256': digest(self.c),
                 'config': self.config_pin, 'credentials': self.credential_pins,
                 'producer': _source(), 'acceptance': acceptance, 'seconds': seconds}
        if inherited_attempt is not None:
            if (inherited_attempt['boot_id'] != acceptance['boot_id']
                    or budget.deadline > inherited_attempt['deadline_mono']):
                raise HostUnavailable('inherited_a0_bootstrap_deadline_changed')
            phase['inherited_attempt'] = copy.deepcopy(inherited_attempt)
        task = 'native-' + digest(phase)
        workspace = Path(self.c['workspace_root']) / task
        self.identity = {'existing_task_id': task, 'admission_hash': hashlib.sha256(task.encode()).hexdigest(),
            'owner': {'bot_id': binding['account_id'], 'user_id': binding['user_id'],
                      'profile': binding['runtime_profile'], 'chat_id': '', 'thread_id': '',
                      'message_id': '', 'session_key': 'own-profile-initial-probe', 'session_id': digest(phase)},
            'worker_kind': 'a0', 'brief_sha256': digest({'purpose': 'INITIAL_DEPLOYMENT_PROBE'}),
            'workspace_reference': str(workspace),
            'supervisor': {'scope': 'user', 'unit': 'friday-rework-worker-' + task[7:39] + '.service'},
            'created_at_unix': accepted_unix, 'budget_seconds': seconds,
            'deadline_unix': accepted_unix + seconds}
        self.acceptance = acceptance
        self.original = dict(phase, schema='friday.a0.initial-probe.v1', association=self.identity,
                             deadline_monotonic=budget.deadline, retry_authorized=False)
        self.current()
        # Native registration, inactive/exclusive daemon, real deadlines and
        # source/network/kernel readback are the existing admission mechanism.
        # No ready flag, static template or operator-provided plan substitutes.
        if not callable(getattr(m, 'route_preflight', None)):
            raise PrerequisitePending('own_a0_reviewed_bootstrap_runtime_missing')
        try:
            m.route_preflight(self.identity, acceptance, a, budget=self.left)
        except (OSError, ValueError, RuntimeError) as exc:
            raise PrerequisitePending('own_a0_native_prerequisites_pending') from exc
        self.current()

    def left(self):
        self.current()
        return self.budget.check(reserve=25)

    def current(self):
        self.budget.check()
        self.verify()
        _pin(self.config_pin).read()
        if credentials(self.home) != self.credential_pins:
            raise HostUnavailable('a0_bootstrap_credentials_changed')
        from hermes_cli.friday_credential_admission import owned_values
        if owned_values(self.home) != self.values:
            raise HostUnavailable('a0_bootstrap_scoped_keys_changed')
        for ref in self.preparations.values(): _pin(ref).read()
        a0_deployment_contract(self.c)
        if self.keys is not None: self.keys.ready()

    def retain(self, **values):
        self.state.update(copy.deepcopy(values))
        if self.claimed: _write(self.folder / 'state.json', self.state, replace=True)

    def retain_route(self, route):
        # Cache before persistence; cleanup still acts if the disk write fails.
        self.route = copy.deepcopy(route)
        self.retain(route=route)

    def start(self):
        self.current()
        self.folder.mkdir(mode=0o700)
        _write(self.folder / 'original.json', self.original)
        _write(self.folder / 'state.json', self.state)
        self.claimed = True
        workspace = Path(self.identity['workspace_reference'])
        workspace.mkdir(mode=0o700)
        self.m.private(workspace, directory=True)
        self.m.prepare_route(self.identity, self.acceptance, self.c['a0'],
                             retain=self.retain_route, budget=self.left)
        network = self.m.current_network(self.identity, self.acceptance,
            owner_slot=self.c['a0']['owner_slot'], launcher_sha256=self.c['a0']['launcher']['sha256'],
            docker_sha256=self.c['a0']['docker']['sha256'], deployment=self.c['a0']['deployment'],
            web=self.c['a0']['web'])
        if (self.route is None or self.route['pending'] is not None
                or self.route['network'] != network or self.route['settlement'] is not None):
            raise HostUnavailable('a0_bootstrap_route_custody_changed')
        a = self.c['a0']; identity = self.identity
        self.plan = self.m.plan(identity['created_at_unix'], identity['deadline_unix'],
            assignment=identity['existing_task_id'], generation=1, owner_slot=a['owner_slot'],
            original_budget_seconds=identity['budget_seconds'], git_metadata=a['git_metadata'],
            network=network, deployment=a['deployment'], web=a['web'], association_binding=identity,
            accepted_monotonic_ns=self.acceptance['accepted_monotonic_ns'], boot_id=self.acceptance['boot_id'])
        self.m.write_json(self.plan_path, self.plan)
        self.runtime = self.m.Runtime(self.plan, budget=self.left)
        self.retain(phase='START_PENDING', plan=pin(self.plan_path))
        def before_ui(usr):
            from .adapters.a0_config import prepare_keys, prepare_web_keys
            self.current()
            self.retain(keys='PREPARATION_PENDING', key_directory=str(usr))
            self.keys = prepare_keys(usr, lambda n: self.values[n])
            self.retain(keys='PREPARED_BASE')
            self.keys = prepare_web_keys(self.keys, usr, lambda n: self.values[n])
            self.retain(keys='PREPARED')
            self.current()
        def on_created(known):
            self.created = copy.deepcopy(known)
            self.retain(created=known)
            self.current()
        snapshot = self.runtime.snapshot_container
        def retained_snapshot(obj):
            self.pending_sample = True
            self.retain(pending_sample=True)
            value = snapshot(obj)
            self.samples.append(copy.deepcopy(value))
            self.pending_sample = False
            self.retain(samples=self.samples, pending_sample=False)
            return value
        self.runtime.snapshot_container = retained_snapshot
        self.start_attempted = True
        self.runtime.start(self.plan_path, self.m.sha(self.plan_path),
                           before_ui=before_ui, on_created=on_created)
        self.current()
        self.wait_ready()
        self.retain(phase='OWNED_PROBE_RUNNING', created=self.runtime.receipt())
        return pin(self.plan_path)

    def wait_ready(self):
        # Only bounded harmless native GETs may be repeated. Create/start,
        # message/model work and uncertain control calls are never replayed.
        script = self.m.HEALTH_SCRIPT.replace('\n raise SystemExit(1)', '')
        if script == self.m.HEALTH_SCRIPT:
            raise HostUnavailable('a0_bootstrap_health_source_changed')
        while True:
            self.current()
            with self.runtime.locked():
                r = self.runtime.receipt()
                obj = self.runtime.inspect(r, timeout=min(3, self.left()))
                unit = self.runtime.supervisor.observe(self.runtime.association(r))
                if (not obj['State']['Running'] or obj['State']['Pid'] <= 0 or unit.missing
                        or unit.quiescent or unit.invocation_id != r['invocation_id']):
                    raise HostUnavailable('a0_bootstrap_native_start_lost')
                sample = self.runtime.snapshot_container(obj)
                r['observations'].append(sample)
                self.runtime.known = r
                self.m.write_json(self.runtime.receipt_path, r, replace=True)
                reply = json.loads(self.runtime.docker('exec', '--workdir=/a0', r['container_id'],
                    '/opt/venv-a0/bin/python', '-B', '-c', script, timeout=min(4, self.left())))
            self.current()
            if (set(reply) == {'http', 'gitinfo_present', 'native_error_present'}
                    and reply['http'] == 200 and reply['gitinfo_present'] is True
                    and reply['native_error_present'] is False): return
            if reply != {'http': None, 'status': 'NOT_READY'}:
                raise HostUnavailable('a0_bootstrap_native_health_refused')
            time.sleep(min(.1, self.left()))

    def stop(self):
        """Existing stop-only custody survives expiry, revocation and disk errors."""
        from scripts.dsh_prepare import StopUnconfirmed
        errors = []; container = retirement = None
        if self.runtime is not None and self.start_attempted:
            try:
                if self.runtime.known is not None:
                    # Keep all observed descendants even after a lost receipt.
                    known = self.runtime.known
                    try:
                        # Other existing observers can add descendant samples.
                        # Reconcile their exact receipt without losing the cached
                        # stop identity if persistence itself is damaged.
                        disk = self.m.private(self.runtime.receipt_path)
                        latest = json.loads(disk.read_text())
                        if (latest['plan_sha256']!=known['plan_sha256']
                                or latest['container_id']!=known['container_id']
                                or latest['invocation_id']!=known['invocation_id']):
                            raise RuntimeError('native receipt owner drift')
                        for sample in latest['observations']:
                            if sample not in known['observations']:known['observations'].append(sample)
                    except BaseException as exc: errors.append(exc)
                    for sample in self.samples:
                        if sample not in known['observations']: known['observations'].append(sample)
                    container = self.runtime.stop()
                    if container['status'] != 'STOP_CONFIRMED' or self.pending_sample:
                        raise RuntimeError('incomplete native sampling')
                    if not errors:
                        retirement = self.runtime.retire_initial_probe()
                        if retirement['status']!='INITIAL_PROBE_RETIRED': raise RuntimeError('retirement unknown')
                elif self.runtime.create_attempted:
                    raise RuntimeError('create outcome unknown')
            except BaseException as exc: errors.append(exc)
        if self.route is not None:
            try:
                # Recorded immutable code owns cleanup when launch sources drift.
                import types
                ref = self.route['stop_source']; data = _pin(ref).read()
                m = types.ModuleType('frw_initial_probe_stop'); m.__file__ = ref['path']
                exec(compile(data, ref['path'], 'exec'), m.__dict__)
                self.route_module = m
                def retain(value):
                    self.route = copy.deepcopy(value)
                    try: self.retain(route=value)
                    except (OSError, RuntimeError): pass
                cid = None if self.runtime is None or self.runtime.known is None else self.runtime.known['container_id']
                m.stop_route(self.route, retain=retain, container_id=cid)
                if self.route['settlement']['status'] != 'STOP_CONFIRMED': raise RuntimeError('route not settled')
            except BaseException as exc: errors.append(exc)
        if self.state['keys'] not in ('NOT_PREPARED', 'PREPARED'):
            errors.append(RuntimeError('partial key preparation requires exact-owner reconciliation'))
        if not errors and self.keys is not None:
            try: self.keys.remove(cessation_confirmed=True)
            except BaseException as exc: errors.append(exc)
        if errors:
            try: self.retain(phase='STOP_UNCONFIRMED', settlement=None)
            except (OSError, RuntimeError): pass
            raise StopUnconfirmed('A0 initial probe exact owner cleanup unconfirmed') from errors[0]
        settled = {'status': 'STOP_CONFIRMED', 'container': container,
                   'retirement':retirement,
                   'route': None if self.route is None else self.route['settlement'],
                   'keys': 'REMOVED' if self.keys is not None else 'NOT_PREPARED'}
        try: self.retain(phase='STOPPED', settlement=settled)
        except (OSError, RuntimeError) as exc:
            raise StopUnconfirmed('A0 initial probe settlement persistence unconfirmed') from exc
        self.values.clear()
        return pin(self.folder / 'state.json')


@contextmanager
def own_probe(probe):
    try:
        yield probe.start()
    except BaseException:
        if probe.claimed:
            probe.stop()
            probe.retain(phase='FAILED_STOPPED_NO_REPLAY')
        raise
    else:
        probe.stop()


def checked_custody(home, binding, generation, preparations, plan_ref):
    """Historical probe ownership/cessation, never a fresh execution grant."""
    from hermes_cli import friday_user_scope as scope
    original = _read(home / FOLDER / 'original.json')
    state = _read(home / FOLDER / 'state.json')
    plan = _read(home / PLAN)
    from .worker_provision import preparation
    prepared = preparation(home,binding['runtime_profile'],'a0',preparations['a0'])[1]
    phase = {k:v for k,v in original.items() if k not in ('schema','association','deadline_monotonic','retry_authorized')}
    task = 'native-' + digest(phase)
    if (original.get('schema') != 'friday.a0.initial-probe.v1'
            or original['home'] != str(home) or original['binding'] != binding
            or original['generation'] != generation or original['preparations'] != preparations
            or original['runtime_sha256'] != digest(prepared)
            or original['association']['existing_task_id'] != task
            or original['association']['owner']['user_id'] != binding['user_id']
            or original['association']['owner']['bot_id'] != binding['account_id']
            or original['association']['owner']['profile'] != binding['runtime_profile']
            or original['producer'] != _source() or original['retry_authorized'] is not False
            or original['credentials'] != credentials(home)
            or plan_ref != pin(home / PLAN) or state.get('plan') != plan_ref
            or plan['association_binding'] != original['association']
            or plan['accepted_monotonic_ns'] != original['acceptance']['accepted_monotonic_ns']
            or plan['boot_id'] != original['acceptance']['boot_id']
            or plan['boot_id'] != Path('/proc/sys/kernel/random/boot_id').read_text().strip()
            or plan['original_budget_seconds'] != original['seconds']
            or plan['accepted_unix'] != original['acceptance']['accepted_unix']
            or plan['deadline_unix'] != plan['accepted_unix'] + original['seconds']
            or state['route']['association'] != original['association']
            or state['route']['acceptance'] != original['acceptance']
            or state['route']['network'] != plan['network']
            or state['phase'] != 'STOPPED' or state['pending_sample'] is not False
            or state['settlement']['status'] != 'STOP_CONFIRMED'
            or state['settlement']['keys'] != 'REMOVED'
            or state['settlement']['container']['status'] != 'STOP_CONFIRMED'
            or state['settlement']['container']['container_id'] != state['created']['container_id']
            or state['settlement']['container'].get('native_container_stopped') is not True
            or state['settlement']['retirement']['status'] != 'INITIAL_PROBE_RETIRED'
            or state['settlement']['retirement']['container_id'] != state['created']['container_id']
            or state['settlement']['route']['status'] != 'STOP_CONFIRMED'):
        raise HostUnavailable('foreign_or_unsettled_a0_bootstrap')
    scope._private(home / FOLDER, directory=True)
    return {'original': pin(home / FOLDER / 'original.json'), 'settlement': pin(home / FOLDER / 'state.json')}


def installation_probe(product, home, original_attempt, budget, *, verify):
    """Same native producer, contained inside the original installer clock.

    Installation has no end-user setup session. Its exact protected operator,
    receiving account and installed preparation are the owning identity.
    Ambiguous multi-account installations stay pending rather than inventing
    a recipient. The bounded native phase cannot extend the installer deadline.
    """
    from scripts.install_containment import Budget
    accounts = product['accounts']
    if len(accounts) != 1:
        raise PrerequisitePending('initial_install_probe_receiving_account_ambiguous')
    binding = dict(accounts[0], runtime_profile=product['profile'],
                   user_id=product['dashboard']['operator']['user_id'], operation='installation')
    preparations = {k:pin(home / 'workers' / k / 'runtime-input.json') for k in ('dsh','a0')}
    seconds = min(300, product['runtime']['workers']['a0']['budget_seconds'], int(budget.check()))
    started = time.monotonic()
    phase = Budget(seconds, started=started, deadline=min(started+seconds,budget.deadline))
    def current(): budget.check(); verify()
    return InitialProbe(product['runtime']['workers']['a0'],binding,1,preparations,phase,current,
                        original_seconds=seconds,inherited_attempt=original_attempt)
