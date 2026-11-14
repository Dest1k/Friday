"""One Root-owned first-send integration, inert unless explicitly invoked.

Old clocks and state remain historical. Source/binding checks and read-only
preclock proof preparation precede a distinct operative clock. No retry path.
"""
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import time
import types
import uuid

D = Path('/home/jericho/.cache/FRW-ASTRA-V3-F03-RICH-ODS-ORIGINAL221-20261114')
OLD = D / 'ordinary-unsent-user-step-continuation-phase'
WORK = D / 'separate-missing-first-send-phase'
F = Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-F03-MISSING-FIRST-SEND-CONTRACT-CANDIDATE-20261114')
ASSEMBLY = Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-F03-ROOT-FIRST-SEND-ASSEMBLY-20261114/assembly.py')
ASSEMBLY_SHA = 'e6defdd8ea61bb81a30c50c066c1d652eac4a371285ce53e7ab9f9caa1f9942b'
OWN = Path(__file__).parent
DELTA_FREEZE_REF = {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-F03-EXACT-R108-CUSTODY-DELTA-20261114/revision2/SOURCE-FREEZE.json', 'bytes': 2997, 'sha256': 'b2a4c97c30702709cc0b336fa2b507d9fcbbcfe3232a53a867c9294f1681c636'}
POLICY = Path('/home/jericho/jericho/FRIDAY_PRODUCTION_PROCESS_CORRECTION_V1_RU_2026-10-22.md')
STABLE = ('installed_product', 'gateway', 'selected_scope', 'canonical4',
          'services', 'source_stat', 'history', 'databases', 'current_files',
          'mutable_paths', 'once', 'f03_mutable_boundary')
PHASE_REF = {'path': '/home/jericho/.cache/FRW-ASTRA-NATIVE-F03-EXACT-R108-CUSTODY-DELTA-20261114/revision2/candidate/first_send.py', 'bytes': 19459, 'sha256': '52d48a7cfc6162c137569728ec024e6d2633a0d7901ef92071b47cd764af63d7'}


def need(value, reason):
    if not value:
        raise ValueError('F03_ROOT_' + reason)


def enc(value):
    return (json.dumps(value, ensure_ascii=True, sort_keys=True,
                       allow_nan=False) + '\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load_raw(raw, path, name):
    module = types.ModuleType(name)
    module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def same(current, actual, expected):
    for key in STABLE:
        need(actual[key] == expected[key], 'CURRENT_DRIFT_' + key)
    need(current.native_stable(actual['native_readonly']) ==
         current.native_stable(expected['native_readonly']), 'NATIVE_DRIFT')


def static_inputs(root_review_sha):
    # Bootstrap only the already reviewed fixed phase source, then use its
    # bounded, no-link, protected-parent, regular-file/CAS reader everywhere.
    p = Path(PHASE_REF['path'])
    z = p.stat()
    need(p.is_absolute() and not any(x.is_symlink() for x in (p, *p.parents))
         and stat.S_ISREG(z.st_mode) and z.st_uid == os.getuid()
         and stat.S_IMODE(z.st_mode) == 0o600 and z.st_nlink == 1
         and z.st_size == PHASE_REF['bytes']
         and stat.S_IMODE(p.parent.stat().st_mode) == 0o700,
         'PHASE_BOOTSTRAP_CUSTODY')
    with os.fdopen(os.open(p, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as stream:
        raw = stream.read(PHASE_REF['bytes'] + 1)
    need(len(raw) == PHASE_REF['bytes'] and sha(raw) == PHASE_REF['sha256'],
         'PHASE_BOOTSTRAP_PIN')
    phase = load_raw(raw, p, '_Root_phase')
    need(phase.rawref(PHASE_REF) == raw, 'PHASE_BOOTSTRAP_POST_CAS')
    result_ref = phase.pin(F / 'RESULT.json', phase.read(F / 'RESULT.json'))
    need(result_ref['sha256'] == 'e91a8c80462213e019c249cb6f14073f1fe4580851e86266c41edccdafe8c4af', 'CANDIDATE_RESULT_PIN')
    result = phase.doc(result_ref)
    for row in phase.doc(result['source_freeze'])['files'].values():
        phase.rawref(row)
    review = phase.doc(result['final_independent_review'])
    need(review['decision'] == 'SOURCE_ONLY_READY_UNBOUND' and not review['open_critical_defects'], 'CANDIDATE_REVIEW')
    acceptance = phase.pin(D / 'ROOT-SEPARATE-FIRST-SEND-SOURCE-ACCEPTANCE.json', phase.read(D / 'ROOT-SEPARATE-FIRST-SEND-SOURCE-ACCEPTANCE.json'))
    need(acceptance['sha256'] == 'b02eb14238fcd720062c5adbb1c72a042c0d36d5a75627f4a58c98fe3d3a5d93', 'ROOT_SOURCE_ACCEPTANCE_PIN')
    need(type(root_review_sha) is str and len(root_review_sha) == 64
         and all(c in '0123456789abcdef' for c in root_review_sha), 'ROOT_REVIEW_UNBOUND')
    ar = phase.read(ASSEMBLY)
    need(sha(ar) == ASSEMBLY_SHA, 'ASSEMBLY_PIN')
    independent = phase.read(OWN / 'FINAL-REVIEW.json')
    need(sha(independent) == root_review_sha, 'ROOT_REVIEW_PIN')
    rv = json.loads(independent)
    need(rv['decision'] == 'SOURCE_ONLY_READY_UNBOUND' and not rv['open_critical_defects'], 'ROOT_REVIEW_NOT_READY')
    need(rv['reviewed_root_operator'] == phase.pin(Path(__file__), phase.read(Path(__file__))),
         'ROOT_REVIEW_TARGET_CHANGED')
    need(sha(POLICY.read_bytes()) == '220a86e1e59dccb50a0ce34332d1f9061cb52a5e4c17f81df08df38202a18128', 'OWNER_POLICY_PIN')
    # This narrow reviewed supervisor copy fixes comparison of the native
    # query timestamp while preserving every stable field and all other checks.
    supervisor_ref = rv.get('reviewed_supervisor')
    need(phase.refshape(supervisor_ref) and
         Path(supervisor_ref['path']) == OWN / 'candidate/supervisor_adapter.py',
         'ROOT_REVIEW_SUPERVISOR_UNBOUND')
    phase.rawref(supervisor_ref)
    # Preserve accepted original freeze and explicitly authenticate this narrow
    # custody/pin delta with the outside final review; no self-hash cycle.
    need(rv.get('reviewed_source_freeze') == DELTA_FREEZE_REF, 'ROOT_REVIEW_DELTA_FREEZE_UNBOUND')
    delta = phase.doc(DELTA_FREEZE_REF)
    need(delta.get('schema') == 'frw.F03.exact-r108-custody-delta.source-freeze.v1'
         and delta.get('execution_grant') is False and delta.get('templates_UNBOUND') is True
         and delta.get('base_candidate_result') == result_ref, 'DELTA_FREEZE_BASE')
    need(set(delta['source_delta']) == {'phase', 'current', 'fullconsumer', 'pure_binder', 'case_entry', 'supervisor', 'adapter'}
         and delta['source_delta']['phase'] == PHASE_REF
         and delta['source_delta']['adapter'] == result['source_delta']['adapter']
         and delta['source_delta']['supervisor'] == supervisor_ref, 'DELTA_EXACT_SOURCE_SET')
    for ref in delta['source_delta'].values():
        phase.rawref(ref)
    result = copy.deepcopy(result)
    result['final_independent_review'] = phase.pin(OWN / 'FINAL-REVIEW.json', independent)
    sources = result['source_delta']
    sources.update(delta['source_delta'])
    sources['supervisor'] = supervisor_ref
    modules = {name: load_raw(phase.rawref(sources[key]), sources[key]['path'], '_Root_' + name)
               for name, key in [('adapter', 'adapter'), ('current', 'current'),
                                 ('binder', 'pure_binder'), ('supervisor', 'supervisor')]}
    modules.update(phase=phase, assembly=load_raw(ar, ASSEMBLY, '_Root_assembly'))
    old_binding = phase.read(OLD / 'ROOT-ACTUAL-BINDING.json')
    need(sha(old_binding) == '16ce03f11c36b8dad19e5fec074eaf9da05262fa8d2ae7ab38cbc7e61755af2d', 'OLD_BINDING_PIN')
    original = json.loads(old_binding)['contract']
    previous = phase.doc(original['root_current_review'])
    reviews = {name: phase.doc(ref) for name, ref in original['root_proofs'].items()}
    maker_ref = dict(path='/home/jericho/.cache/FRW-ASTRA-NATIVE-M09-PUBLIC-SCOPE-PRIVACY-REPAIR-20261113/consumer/m09_request.py', bytes=1765, sha256='fb2cf766155e56889aeb09786f75048209d8660f729e4f7154f9364a44154e98')
    maker = load_raw(phase.rawref(maker_ref), maker_ref['path'], '_Root_request_maker')
    operator_path = Path('/home/jericho/.cache/FRW-ASTRA-NATIVE-F03-UNSENT-STEP-CONTINUATION-PREP-20261114/candidate/operator/root_operator_bind_phase81.py')
    operator_raw = phase.read(operator_path)
    need(sha(operator_raw) == 'd0723eac570b16fb93b97e2b4cf9180e1c679b73d597033598972c803fedb4fc', 'REUSED_DEPENDENCY_READER_PIN')
    dependency_reader = load_raw(operator_raw, operator_path, '_Root_dependencies')
    return modules, result, acceptance, original, previous, reviews, maker, dependency_reader


def existing_lock(path, expected):
    p = Path(path)
    need(not any(x.is_symlink() for x in (p, *p.parents)), 'LOCK_LINK')
    fd = os.open(p, os.O_RDWR | os.O_NOFOLLOW)
    try:
        z, fz = p.stat(), os.fstat(fd)
        need((z.st_dev, z.st_ino) == (expected['device'], expected['inode'])
             and z.st_uid == os.getuid() and stat.S_IMODE(z.st_mode) == 0o600
             and z.st_nlink == 1 and stat.S_ISREG(z.st_mode)
             and (z.st_dev, z.st_ino, z.st_mode, z.st_uid, z.st_nlink) ==
                 (fz.st_dev, fz.st_ino, fz.st_mode, fz.st_uid, fz.st_nlink), 'LOCK_IDENTITY')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except BaseException:
        os.close(fd)
        raise


def execute(root_review_sha):
    os.umask(0o077)
    modules, result, acceptance, original, previous, reviews, maker, dep = static_inputs(root_review_sha)
    phase, adapter, current, assembly = (modules[k] for k in ('phase', 'adapter', 'current', 'assembly'))
    need(not WORK.exists() and not WORK.is_symlink(), 'EXISTING_PHASE_RECONCILE_NO_RETRY')
    need(phase.read(phase.STATE / 'runs' / (phase.RUN + '.json')) == phase.rawref(phase.PRISTINE), 'ACTUAL_PRISTINE_CHANGED')
    for ref in [phase.CLOSURE, phase.OLD_CLOCK, phase.R108, *phase.MARKERS]:
        phase.rawref(ref)
    need(not phase.ONCE.exists() and not phase.BEFORE.exists(), 'ALREADY_CLAIMED')
    # No generation probe: authenticated configured GET /models only.
    ready = dep.dependencies()
    WORK.mkdir(mode=0o700)
    provisional = WORK / 'provisional'
    provisional.mkdir(mode=0o700)
    saved = lambda p, value: phase.exclusive(p, enc(value))
    saved(WORK / 'DEPENDENCY-READINESS-BEFORE-CLOCK.json', ready)
    scope = saved(WORK / 'ROOT-STANDING-SCOPE-DECISION.json', dict(
        schema='frw.Root.F03.distinct-missing-step-standing-scope.v1', operator='Root',
        status='STANDING_AUTHORITY_COVERS_SEPARATE_MISSING_PORTION_PENDING_FRESH_ADMISSION',
        execution_grant=False, current_admission=False,
        authorization_basis='Owner continuation/autonomy plus 2026-10-24 rule: after effect/resource reconciliation a separate future missing portion may have a finite budget; 2026-10-22 production policy independent lifecycles.',
        policy_sha256='220a86e1e59dccb50a0ce34332d1f9061cb52a5e4c17f81df08df38202a18128',
        original300_timing_acceptance=False, original_clocks_unchanged=True,
        no_new_run_no_generic_resume_no_reissue=True,
        positive_no_send=phase.CLOSURE, exact_raw_before=phase.PRISTINE,
        source_acceptance=acceptance))
    slot_fd = existing_lock(current.SLOT, phase.LOCKS['slot'])
    locks = []
    try:
        for name in ('consumer.lock', 'tester-token'):
            locks.append(existing_lock(phase.STATE / name, phase.LOCKS[name]))
        holder = current.kernel(os.getpid())
        current.shared_slot(holder, current.helper())
        old_actors = []
        for pid, birth in [(928072, 9415497), (928021, 9414877), (927965, 9414226)]:
            try:
                actor = current.kernel(pid)
            except FileNotFoundError:
                actor = None
            need(actor is None or actor['start_time'] != birth, 'OLD_ACTOR_STILL_PRESENT')
            old_actors.append(dict(pid=pid, start_time=birth, absent_by_identity=True))
        held = saved(WORK / 'ROOT-ACTUAL-LOCK-AND-OLD-ACTOR-RECONCILIATION.json', dict(
            operator='Root', observed_wall=time.time(), observed_monotonic=time.monotonic(),
            root_identity=holder, old_actors=old_actors, actual_existing_three_locks=phase.LOCKS,
            Root_holds_all_three_locks_now=True,
            child_future_lock_acquisition='NOT_ESTABLISHED; Root releases two before child, child must acquire create=False and revalidate'))
        roots = set(reviews['private_exclusion']['private_roots'])
        roots.update(map(str, (WORK, provisional, F, F / 'candidate', F / 'candidate/current',
                               F / 'review', ASSEMBLY.parent, OWN, OWN / 'candidate', OWN / 'candidate/current', phase.STATE, phase.ONCE.parent)))
        root_refs = copy.deepcopy(original['root_proofs'])
        root_refs['source_review'] = result['final_independent_review']
        for name in ('source_custody', 'all_profile_history_semantic_once', 'owned_actor_stop_resources', 'private_exclusion'):
            body = copy.deepcopy(reviews[name])
            body['state'] = 'HISTORICAL_REVIEW_INPUT_FOR_READONLY_PRECLOCK_COLLECTION_NOT_ADMISSION'
            if name == 'private_exclusion':
                body['private_roots'] = sorted(roots)
            body['evidence'] += [acceptance, scope, held]
            root_refs[name] = saved(provisional / (name + '.json'), body)
        wall, mono = time.time(), time.monotonic()
        request_old = phase.doc(previous['native_request'])
        req = maker.make_request(request_old['scope_ref'], query_id=uuid.uuid4().hex,
                                 kernel=previous['observed']['gateway'],
                                 created_monotonic=mono, expires_monotonic=mono + 120)
        req_ref = saved(WORK / 'NATIVE-CURRENT-REQUEST.private.json', req)
        draft = copy.deepcopy(previous)
        draft.update(status='ROOT_PREPARED_ONE_FUTURE_OPERATION', created_at=wall,
                     expires_at=wall + 120, created_monotonic=mono, expires_monotonic=mono + 120,
                     shared_slot_owner=holder, native_request=req_ref,
                     execution_grant=False, preparation_only=True)
        contract, draft, projection = assembly.preclock_inputs(adapter, current, modules['binder'], phase,
                                                              original, root_refs, draft, str(WORK))
        observed = current.observe(draft, boundary_phase='CURSOR_AUTHORITY', first_send=projection,
                                   first_send_preclaim=True)
        # Reuse immutable judgments only when every previous semantic input and
        # mutable data boundary is unchanged. A difference requires real analysis.
        same(current, observed, previous['observed'])
        for name in ('source_custody', 'all_profile_history_semantic_once', 'owned_actor_stop_resources', 'private_exclusion'):
            body = copy.deepcopy(reviews[name])
            body.update(state='ROOT_CURRENT_REUSE_CONFIRMED_BY_IDENTICAL_SEMANTIC_INPUTS',
                        judgment=body['judgment'] + '; Root freshly verified unchanged semantic inputs; separate first-send only, no old timing PASS.')
            body['evidence'] += [acceptance, scope, held, original['root_current_review']]
            if name == 'private_exclusion':
                body['private_roots'] = sorted(roots)
            root_refs[name] = saved(WORK / (name + '.json'), body)
        contract, draft, projection = assembly.preclock_inputs(adapter, current, modules['binder'], phase,
                                                              original, root_refs, draft, str(WORK))
        current.semantics(adapter.effect(contract), current.proof_documents(adapter.effect(contract)), observed)
        current.lifetime(draft)
        draft.update(status='ROOT_BOUND', preparation_only=False, shared_slot_owner=holder)
        frozen = assembly.freeze_preclock(adapter, current, modules['binder'], phase, contract, draft,
                                           observed, WORK / 'ROOT-FRESH-CURRENT-PROOF.private.json',
                                           WORK / 'bot_tester.f03.first-send.bound.py',
                                           phase.rawref(result['source_delta']['fullconsumer']))
        need(phase.exclusive(frozen['proof_ref']['path'], frozen['proof_bytes']) == frozen['proof_ref'], 'PROOF_WRITE_BINDING')
        need(phase.exclusive(frozen['consumer_ref']['path'], frozen['consumer_bytes']) == frozen['consumer_ref'], 'CONSUMER_WRITE_BINDING')
        again = current.observe(frozen['proof'], boundary_phase='CURSOR_AUTHORITY', first_send=projection,
                                first_send_preclaim=True)
        same(current, again, observed)
        current.lifetime(frozen['proof'])
        memory = int(next(x.split()[1] for x in Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:'))) * 1024
        fs = os.statvfs(phase.STATE)
        need(memory >= 536870912 and fs.f_bavail * fs.f_frsize >= 67108864 and os.sched_getaffinity(0), 'FINITE_RESOURCES_UNAVAILABLE')
        # Every source and exact bound consumer is now ready. New times are
        # paired once here, never recreated or substituted for either old clock.
        origin_wall, origin_mono = time.time(), time.monotonic()
        need(origin_wall + 600 <= phase.R108_EXPIRY, 'ABSOLUTE_OLD_AUTHORITY_BOUND')
        plan_sha = sha(enc(phase.plan()))
        clock = dict(schema='frw.Root.F03.distinct-first-send-clock.v1', role=phase.ROLE,
                     run_id=phase.RUN, plan_sha256=plan_sha, boot_id=holder['boot_id'],
                     origin_wall=origin_wall, origin_monotonic=origin_mono,
                     first_send_deadline_wall=origin_wall + 300, first_send_deadline_monotonic=origin_mono + 300,
                     outer_deadline_wall=origin_wall + 600, outer_deadline_monotonic=origin_mono + 600)
        clock_ref = saved(WORK / 'DISTINCT-FIRST-SEND-CLOCK.json', clock)
        recon = dict(schema='frw.Root.F03.separate-first-send-reconciliation.v1', operator='Root',
                     plan_sha256=plan_sha, original_pristine=phase.PRISTINE,
                     created_at=origin_wall, created_monotonic=origin_mono, boot_id=holder['boot_id'],
                     facts={key: True for key in phase.FACTS}, evidence=[scope, held, acceptance,
                          phase.CLOSURE, frozen['proof_ref'], *phase.MARKERS],
                     lock_fact_scope='Actual Root-held existing locks at reconciliation; child acquisition remains mandatory and unproved until executed.')
        recon_ref = saved(WORK / 'ROOT-FRESH-SEPARATE-RECONCILIATION.json', recon)
        unsigned = assembly.supplement_without_decision(phase, PHASE_REF, frozen['consumer_ref'], clock_ref, recon_ref)
        decision = dict(schema='frw.Root.F03.separate-first-send-decision.v1', operator='Root',
                        status='ROOT_ACCEPTED_SEPARATE_MISSING_FIRST_SEND', execution_grant=True,
                        authorization_basis='ROOT_STANDING_AUTHORIZATION_APPLIES',
                        old_clocks_not_extended=True, R108_is_only_additional_bound_not_grant=True,
                        expires_at=clock['first_send_deadline_wall'],
                        case_entry_source=result['source_delta']['case_entry'],
                        supervisor_source=result['source_delta']['supervisor'],
                        original300_timing_acceptance=False, **assembly.decision_bindings(phase, unsigned))
        finished = assembly.finish_supplement(phase, unsigned, decision, clock, recon,
                      WORK / 'ROOT-SEPARATE-FIRST-SEND-DECISION.json', WORK / 'ROOT-SEPARATE-FIRST-SEND-CONTRACT.json',
                      result['source_delta']['case_entry'], result['source_delta']['supervisor'])
        phase.exclusive(finished['decision_ref']['path'], finished['decision_bytes'])
        phase.exclusive(finished['supplement_ref']['path'], finished['supplement_bytes'])
        meta = assembly.projected_metadata(phase, finished['supplement_ref'], phase.rawref(phase.PRISTINE))
        phase.validate_preclaim(meta, json.loads(phase.rawref(phase.PRISTINE)), phase.STATE)
        actual = current.observe(frozen['proof'], boundary_phase='CURSOR_AUTHORITY', first_send=meta,
                                 first_send_preclaim=True)
        same(current, actual, observed)
        current.semantics(adapter.effect(frozen['contract']), current.proof_documents(adapter.effect(frozen['contract'])), actual)
        current.lifetime(frozen['proof'])
        for fd in locks:
            os.close(fd)
        locks.clear()
        return modules['supervisor'].launch(finished['supplement_ref'], meta, str(WORK), slot_fd)
    finally:
        for fd in locks:
            os.close(fd)
        os.close(slot_fd)


if __name__ == '__main__':
    need(len(sys.argv) == 3 and sys.argv[1] == '--Root-one-separate-first-send', 'EXPLICIT_ROOT_COMMAND_REQUIRED')
    print(json.dumps(execute(sys.argv[2]), sort_keys=True))
