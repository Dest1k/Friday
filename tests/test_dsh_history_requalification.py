"""DSH provenance source controls; all qualification/native reports synthetic.

Actual native profile stores and the read-only PairingStore caller execute.
No model, worker, service, network, archive rewrite or historical replay occurs.
"""
import copy
from pathlib import Path

import pytest

from test_dsh_current_availability import candidate, env, save, reseal
from friday_admin_controls import dsh_current_availability as cur
from friday_admin_controls.host_runtime import HostUnavailable


def incomplete(f):
    h = f.d['history']; completion = cur.read_json(h['completion'])
    completion['retained']['cleanup'] = save(f.root / 'old-cleanup.json', {'old': 'unreplayed'})
    stage = {'schema': 'friday.user-worker-stage-observation.v1', 'kind': 'dsh',
        'effects': 'OBSERVATION_ONLY', 'per_job_authority': 'NOT_GRANTED',
        'generation': f.native['generation'], 'observation': {
            'smoke': cur.read_json(h['observation'])['workers']['dsh']['smoke']}}
    old_stage = save(f.root / 'old-stage.json', stage)
    completion['dsh_refs']['observation'] = old_stage
    h['completion'] = save(Path(h['completion']['path']), completion)
    obs = cur.read_json(h['observation'])
    obs['post_a0_completion']['original'] = h['completion']
    obs['post_a0_completion']['retained'] = completion['retained']
    h['observation'] = save(Path(h['observation']['path']), obs)
    receipt = cur.read_json(h['receipt']); receipt['evidence'] = [h['observation']]
    h['receipt'] = f.c['runtime_receipt'] = save(Path(h['receipt']['path']), receipt)
    graph = {**{'retained.' + k: v for k, v in completion['retained'].items()},
        **{'dsh_refs.' + k: v for k, v in completion['dsh_refs'].items()},
        **{'safety_refs.' + k: v for k, v in completion['safety_refs'].items()}}
    h['retained'] = graph
    alias = save(f.root / 'recovered-stage-exact.json', stage)
    assert alias['sha256'] == old_stage['sha256']
    Path(old_stage['path']).unlink(); Path(graph['retained.cleanup']['path']).unlink()
    edges = {k: {'reference': copy.deepcopy(v), 'state': 'VERIFIED_ORIGINAL', 'copy': None}
        for k, v in graph.items()}
    edges['retained.cleanup']['state'] = 'MISSING_AS_OF'
    edges['dsh_refs.observation'].update(state='VERIFIED_EXACT_COPY', copy=alias)
    h['current_requalification'] = {'schema': cur.HISTORY_REQUALIFICATION,
        'purpose': 'DSH_CURRENT_ONLY_NO_HISTORICAL_REACCEPTANCE',
        'historical_graph_integrity': 'INCOMPLETE', 'missing_as_of': '2026-11-11T01:30:59+03:00',
        'recovery_provenance': save(f.root / 'recovery-provenance.json', {'scope': 'synthetic bounded recovery'}),
        'edges': edges, 'static_smoke': {'observation': alias, 'canonical_observation': h['observation'],
            'reuse': 'EXACT_SAME_STATIC_INPUTS_ONLY'}}
    return h


def test_strict_legacy_still_requires_each_retained_original(candidate):
    f = candidate; h = incomplete(f); del h['current_requalification']
    with pytest.raises(FileNotFoundError): cur._history(f.c, h, f.native)


def test_explicit_mode_reuses_exact_static_only_preserves_original_graph(candidate):
    f = candidate; h = incomplete(f); before = copy.deepcopy(h)
    result = cur._history(f.c, h, f.native)
    assert h == before and result['failure']['state'] == 'STOP_UNCONFIRMED'
    assert result['completion']['old_attempt_reopened'] is False
    assert result['completion']['A0_start_repeated'] is False
    assert f.c['current_availability']['proof'] is None


def test_explicit_history_declaration_still_needs_fresh_native_current_proof(candidate):
    f = candidate; incomplete(f)
    f.c['current_availability']['declaration'] = save(f.root / 'requalification-declaration.json', f.d)
    reseal(f.h, f.c)
    checked = cur.validate_current(f.c, allow_pending=True)
    assert checked['proof'] is None
    with pytest.raises(HostUnavailable, match='pending'):
        cur.validate_current(f.c)
    # Provenance is not permission to substitute even an independently pinned
    # new static executable. Ordinary native/input validators still bind it.
    f.c['dsh']['node']['sha256'] = 'a' * 64
    with pytest.raises(HostUnavailable):
        cur.validate_declaration(f.c, f.d, check_config=False)


@pytest.mark.parametrize('damage', ['omit-edge', 'repin-original', 'omit-alias', 'alias-hash',
    'alias-symlink', 'missing-required', 'unknown-state', 'wrong-smoke', 'wrong-generation',
    'wrong-kind', 'present-corrupt-original', 'historical-pass', 'purpose', 'static-input'])
def test_requalification_refuses_lost_binding_or_history_rewrite(candidate, damage):
    f = candidate; h = incomplete(f); mode = h['current_requalification']; edges = mode['edges']
    if damage == 'omit-edge': del edges['retained.cleanup']
    elif damage == 'repin-original': edges['retained.cleanup']['reference']['sha256'] = '1' * 64
    elif damage == 'omit-alias': edges['dsh_refs.observation']['copy'] = None
    elif damage == 'alias-hash': edges['dsh_refs.observation']['copy']['sha256'] = '2' * 64
    elif damage == 'alias-symlink':
        alias = Path(mode['static_smoke']['observation']['path']); data = alias.read_bytes()
        alias.unlink(); target = f.root / 'alias-target'; target.write_bytes(data); alias.symlink_to(target)
    elif damage == 'missing-required':
        edges['retained.original']['state'] = 'MISSING_AS_OF'
    elif damage == 'unknown-state': edges['retained.cleanup']['state'] = 'ASSUMED_VERIFIED'
    elif damage in ('wrong-smoke', 'wrong-generation', 'wrong-kind'):
        ref = mode['static_smoke']['observation']; stage = cur.read_json(ref)
        if damage == 'wrong-smoke': stage['observation']['smoke'][0]['observation']['returncode'] = 1
        elif damage == 'wrong-generation': stage['generation'] += 1
        else: stage['kind'] = 'a0'
        changed = save(Path(ref['path']), stage)
        edges['dsh_refs.observation']['copy'] = mode['static_smoke']['observation'] = changed
    elif damage == 'present-corrupt-original':
        Path(edges['retained.cleanup']['reference']['path']).write_bytes(b'CORRUPT REAPPEARED ORIGINAL')
    elif damage == 'historical-pass': mode['historical_graph_integrity'] = 'COMPLETE_PASS'
    elif damage == 'purpose': mode['purpose'] = 'ACCEPT_OLD_QUALIFICATION'
    elif damage == 'static-input': f.c['dsh']['node']['sha256'] = '4' * 64
    with pytest.raises((HostUnavailable, TypeError, KeyError)):
        cur._history(f.c, h, f.native)


def test_native_profile_caller_uses_static_root_reader_without_constructor(candidate, monkeypatch):
    from friday_admin_controls.stopped_operator import StoppedOperator
    from scripts import friday_ordinary_install as ordinary
    from scripts.install_containment import Budget
    from gateway.pairing import PairingStore
    from hermes_constants import get_hermes_home
    f = candidate; original = PairingStore.is_approved_storage_readonly; calls = []
    def no_constructor(*args, **kwargs): raise AssertionError('constructor forbidden')
    def check(platform, user_id, **kwargs):
        calls.append((str(get_hermes_home()), platform, user_id, kwargs))
        return original(platform, user_id, **kwargs)
    monkeypatch.setattr(PairingStore, '__init__', no_constructor)
    monkeypatch.setattr(PairingStore, 'is_approved_storage_readonly', staticmethod(check))
    a = StoppedOperator({'profile': f.c['runtime_profile']}, Budget(180))
    a.home = f.e.home; a.profile_home = f.h; a.ordinary = ordinary
    before = {str(p): (p.read_bytes(), p.stat().st_mode, p.stat().st_ino)
        for p in f.e.home.rglob('*') if p.is_file()}
    a._profile()
    assert calls == [(str(f.e.home), 'telegram', '1', {})]
    after = {str(p): (p.read_bytes(), p.stat().st_mode, p.stat().st_ino)
        for p in f.e.home.rglob('*') if p.is_file()}
    assert before == after


def custody(f):
    from friday_admin_controls.stopped_operator import StoppedOperator
    from friday_admin_controls.worker_declarations import DSH_CURRENT_DECLARATION_SCHEMA
    from scripts import friday_ordinary_install as ordinary
    from scripts.install_containment import Budget
    f.c['current_availability']['declaration'] = save(f.root / 'custody-declaration.json', f.d)
    a = StoppedOperator({}, Budget(180)); a.ordinary = ordinary
    a.declaration_bundle = {'schema': DSH_CURRENT_DECLARATION_SCHEMA, 'runtime_after': f.c}
    a._dsh_current_source_pins()
    return a


def test_real_stopped_custody_retains_exact_alias_and_disclosed_absences(candidate):
    f = candidate; history = incomplete(f); a = custody(f)
    mode = history['current_requalification']
    alias = Path(mode['static_smoke']['observation']['path'])
    expected_absent = {Path(item['reference']['path']) for item in mode['edges'].values()
        if item['state'] in ('MISSING_AS_OF', 'VERIFIED_EXACT_COPY')}
    assert a._dsh_missing == expected_absent
    assert alias in a._dsh_external
    assert expected_absent.isdisjoint(a._dsh_external)
    assert all(Path(history[name]['path']) in a._dsh_external for name in (
        'original', 'observation', 'failure', 'completion', 'preparation', 'receipt'))
    a._dsh_missing_unchanged()


def test_history_absence_exception_cannot_be_reused_as_unverified_runtime_pin(candidate):
    f = candidate; history = incomplete(f)
    f.d['inputs']['not-a-history-edge'] = copy.deepcopy(history['retained']['retained.cleanup'])
    with pytest.raises(FileNotFoundError): custody(f)


def test_stopped_custody_detects_original_reappearing_before_publication(candidate):
    from friday_admin_controls.worker_declarations import DeclarationError
    f = candidate; history = incomplete(f); a = custody(f)
    a.before = {}; a.retained = {}; a._context = lambda: None; a._clock = lambda **kw: None
    a.pins_unchanged()
    ref = history['retained']['retained.cleanup']
    Path(ref['path']).write_bytes(b'ORIGINAL PATH REAPPEARED DURING NATIVE CUSTODY')
    with pytest.raises(DeclarationError, match='historical_absence_changed'):
        a.pins_unchanged()


def test_legacy_stopped_custody_still_reads_every_original(candidate):
    f = candidate; history = incomplete(f); del history['current_requalification']
    with pytest.raises(FileNotFoundError): custody(f)

